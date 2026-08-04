#!/bin/bash
# Setup IAM user and policies for Field Intake Service infrastructure
# Usage: ./setup-iam.sh [environment]
# Example: ./setup-iam.sh dev

set -e  # Exit on error

ENVIRONMENT="${1:-dev}"
PROJECT_NAME="field-intake-service"
IAM_USER_NAME="${PROJECT_NAME}-terraform-${ENVIRONMENT}"
POLICY_NAME="${PROJECT_NAME}-terraform-policy-${ENVIRONMENT}"

echo "🔐 Setting up IAM resources for ${PROJECT_NAME} (${ENVIRONMENT} environment)"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Error: AWS CLI not configured. Run 'aws configure' first."
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region || echo "us-east-1")

echo "📋 Configuration:"
echo "   AWS Account: ${ACCOUNT_ID}"
echo "   Region: ${REGION}"
echo "   IAM User: ${IAM_USER_NAME}"
echo ""

# Create IAM policy for Terraform operations
echo "📝 Creating IAM policy: ${POLICY_NAME}"

POLICY_DOCUMENT=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DynamoDBFullAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:CreateTable",
        "dynamodb:DeleteTable",
        "dynamodb:DescribeTable",
        "dynamodb:DescribeContinuousBackups",
        "dynamodb:DescribeTimeToLive",
        "dynamodb:ListTagsOfResource",
        "dynamodb:TagResource",
        "dynamodb:UntagResource",
        "dynamodb:UpdateTable",
        "dynamodb:UpdateContinuousBackups",
        "dynamodb:UpdateTimeToLive"
      ],
      "Resource": [
        "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${PROJECT_NAME}-*"
      ]
    },
    {
      "Sid": "DynamoDBListTables",
      "Effect": "Allow",
      "Action": [
        "dynamodb:ListTables"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMReadOnly",
      "Effect": "Allow",
      "Action": [
        "iam:GetRole",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:ListAttachedRolePolicies",
        "iam:ListRolePolicies"
      ],
      "Resource": "*"
    },
    {
      "Sid": "FutureLambdaPermissions",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:AddPermission",
        "lambda:RemovePermission",
        "lambda:ListVersionsByFunction",
        "lambda:PublishVersion",
        "lambda:CreateAlias",
        "lambda:DeleteAlias",
        "lambda:GetAlias",
        "lambda:UpdateAlias"
      ],
      "Resource": [
        "arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${PROJECT_NAME}-*"
      ]
    },
    {
      "Sid": "FutureAPIGatewayPermissions",
      "Effect": "Allow",
      "Action": [
        "apigateway:GET",
        "apigateway:POST",
        "apigateway:PUT",
        "apigateway:DELETE",
        "apigateway:PATCH"
      ],
      "Resource": [
        "arn:aws:apigateway:${REGION}::/restapis",
        "arn:aws:apigateway:${REGION}::/restapis/*"
      ]
    },
    {
      "Sid": "FutureSNSPermissions",
      "Effect": "Allow",
      "Action": [
        "sns:CreateTopic",
        "sns:DeleteTopic",
        "sns:GetTopicAttributes",
        "sns:SetTopicAttributes",
        "sns:Subscribe",
        "sns:Unsubscribe",
        "sns:ListSubscriptionsByTopic",
        "sns:ListTagsForResource",
        "sns:TagResource",
        "sns:UntagResource"
      ],
      "Resource": [
        "arn:aws:sns:${REGION}:${ACCOUNT_ID}:${PROJECT_NAME}-*"
      ]
    },
    {
      "Sid": "FutureCloudWatchLogsPermissions",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:DescribeLogGroups",
        "logs:PutRetentionPolicy",
        "logs:ListTagsLogGroup",
        "logs:TagLogGroup",
        "logs:UntagLogGroup"
      ],
      "Resource": [
        "arn:aws:logs:${REGION}:${ACCOUNT_ID}:log-group:/aws/lambda/${PROJECT_NAME}-*"
      ]
    }
  ]
}
EOF
)

# Create or update policy
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

if aws iam get-policy --policy-arn "${POLICY_ARN}" &> /dev/null; then
    echo "   ℹ️  Policy already exists. Creating new version..."
    
    # Delete old versions if at limit (keep last 4)
    VERSIONS=$(aws iam list-policy-versions --policy-arn "${POLICY_ARN}" --query 'Versions[?!IsDefaultVersion].[VersionId]' --output text)
    VERSION_COUNT=$(echo "${VERSIONS}" | wc -l)
    
    if [ "${VERSION_COUNT}" -ge 4 ]; then
        OLDEST_VERSION=$(echo "${VERSIONS}" | tail -1)
        echo "   🗑️  Deleting oldest policy version: ${OLDEST_VERSION}"
        aws iam delete-policy-version --policy-arn "${POLICY_ARN}" --version-id "${OLDEST_VERSION}"
    fi
    
    aws iam create-policy-version \
        --policy-arn "${POLICY_ARN}" \
        --policy-document "${POLICY_DOCUMENT}" \
        --set-as-default > /dev/null
    echo "   ✅ Policy updated"
else
    aws iam create-policy \
        --policy-name "${POLICY_NAME}" \
        --policy-document "${POLICY_DOCUMENT}" \
        --description "Terraform permissions for ${PROJECT_NAME} (${ENVIRONMENT})" > /dev/null
    echo "   ✅ Policy created"
fi

# Create IAM user
echo ""
echo "👤 Creating IAM user: ${IAM_USER_NAME}"

if aws iam get-user --user-name "${IAM_USER_NAME}" &> /dev/null; then
    echo "   ℹ️  User already exists"
else
    aws iam create-user \
        --user-name "${IAM_USER_NAME}" \
        --tags "Key=Project,Value=${PROJECT_NAME}" "Key=Environment,Value=${ENVIRONMENT}" "Key=ManagedBy,Value=script" > /dev/null
    echo "   ✅ User created"
fi

# Attach policy to user
echo ""
echo "🔗 Attaching policy to user"

aws iam attach-user-policy \
    --user-name "${IAM_USER_NAME}" \
    --policy-arn "${POLICY_ARN}"

echo "   ✅ Policy attached"

# Create access key
echo ""
echo "🔑 Creating access key"

# Check if user already has access keys
EXISTING_KEYS=$(aws iam list-access-keys --user-name "${IAM_USER_NAME}" --query 'AccessKeyMetadata[].AccessKeyId' --output text)

if [ -n "${EXISTING_KEYS}" ]; then
    echo "   ⚠️  User already has access key(s):"
    echo "   ${EXISTING_KEYS}"
    echo ""
    read -p "   Create new access key? (existing keys won't be deleted) [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "   ℹ️  Skipping access key creation"
        exit 0
    fi
fi

ACCESS_KEY_OUTPUT=$(aws iam create-access-key --user-name "${IAM_USER_NAME}")

ACCESS_KEY_ID=$(echo "${ACCESS_KEY_OUTPUT}" | grep -o '"AccessKeyId": "[^"]*' | cut -d'"' -f4)
SECRET_ACCESS_KEY=$(echo "${ACCESS_KEY_OUTPUT}" | grep -o '"SecretAccessKey": "[^"]*' | cut -d'"' -f4)

echo "   ✅ Access key created"

# Output credentials
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🎉 IAM Setup Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📋 AWS Credentials (SAVE THESE SECURELY - shown only once):"
echo ""
echo "AWS_ACCESS_KEY_ID=${ACCESS_KEY_ID}"
echo "AWS_SECRET_ACCESS_KEY=${SECRET_ACCESS_KEY}"
echo "AWS_DEFAULT_REGION=${REGION}"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🔧 Next Steps:"
echo ""
echo "1️⃣  Add to GitHub Secrets (for CI/CD):"
echo "   gh secret set AWS_ACCESS_KEY_ID -b\"${ACCESS_KEY_ID}\""
echo "   gh secret set AWS_SECRET_ACCESS_KEY -b\"${SECRET_ACCESS_KEY}\""
echo "   gh secret set AWS_DEFAULT_REGION -b\"${REGION}\""
echo ""
echo "2️⃣  Add to local .env (for local development):"
echo "   echo 'AWS_ACCESS_KEY_ID=${ACCESS_KEY_ID}' >> packages/api/.env"
echo "   echo 'AWS_SECRET_ACCESS_KEY=${SECRET_ACCESS_KEY}' >> packages/api/.env"
echo "   echo 'AWS_DEFAULT_REGION=${REGION}' >> packages/api/.env"
echo ""
echo "3️⃣  Or add to AWS CLI profile:"
echo "   aws configure --profile ${PROJECT_NAME}-${ENVIRONMENT}"
echo "   # Then enter the credentials above"
echo ""
echo "4️⃣  Test Terraform with these credentials:"
echo "   cd infra/stacks/dev"
echo "   terraform init -backend=false"
echo "   terraform plan"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "⚠️  SECURITY NOTES:"
echo "   • Store credentials securely (1Password, GitHub Secrets, etc.)"
echo "   • Never commit credentials to git"
echo "   • Rotate access keys every 90 days"
echo "   • Use IAM roles instead of users when possible"
echo ""
