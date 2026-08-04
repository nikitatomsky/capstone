# Infrastructure Scripts

Scripts for AWS infrastructure setup and management.

## setup-iam.sh

Creates IAM user and policies for Terraform operations.

### Prerequisites

- AWS CLI installed and configured with admin credentials
- Appropriate AWS permissions to create IAM users and policies

### Usage

```bash
# Setup IAM for dev environment (default)
./infra/scripts/setup-iam.sh

# Setup for specific environment
./infra/scripts/setup-iam.sh dev
./infra/scripts/setup-iam.sh staging
./infra/scripts/setup-iam.sh prod
```

### What It Creates

1. **IAM Policy** (`field-intake-service-terraform-policy-{env}`)
   - DynamoDB permissions for table management
   - Lambda permissions (for future use)
   - API Gateway permissions (for future use)
   - SNS permissions (for future use)
   - CloudWatch Logs permissions (for future use)
   - IAM read-only access

2. **IAM User** (`field-intake-service-terraform-{env}`)
   - Tagged with project and environment
   - Policy attached for Terraform operations

3. **Access Key**
   - Programmatic access for Terraform
   - Credentials output for secure storage

### Permissions Granted

**Current (Phase 1 - DynamoDB Module):**
- Create/update/delete DynamoDB tables
- Manage table configurations (GSIs, TTL, tags)
- List tables in account

**Future (Phase 2+ - Full Serverless API):**
- Lambda function management
- API Gateway HTTP API management
- SNS topic management
- CloudWatch Logs management
- IAM role read access

### After Running

The script outputs AWS credentials. Store them securely:

#### Option 1: GitHub Secrets (for CI/CD)
```bash
gh secret set AWS_ACCESS_KEY_ID -b"AKIA..."
gh secret set AWS_SECRET_ACCESS_KEY -b"..."
gh secret set AWS_DEFAULT_REGION -b"us-east-1"
```

#### Option 2: Local .env (for development)
```bash
echo 'AWS_ACCESS_KEY_ID=AKIA...' >> packages/api/.env
echo 'AWS_SECRET_ACCESS_KEY=...' >> packages/api/.env
echo 'AWS_DEFAULT_REGION=us-east-1' >> packages/api/.env
```

#### Option 3: AWS CLI Profile
```bash
aws configure --profile field-intake-service-dev
# Enter credentials when prompted
```

### Verification

Test Terraform with the new credentials:

```bash
cd infra/stacks/dev

# Using environment variables
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
terraform init -backend=false
terraform plan

# Using AWS profile
AWS_PROFILE=field-intake-service-dev terraform plan
```

### Security Best Practices

- ✅ **Rotate keys every 90 days** - Set calendar reminder
- ✅ **Use different credentials per environment** - Separate dev/staging/prod
- ✅ **Store in secrets manager** - GitHub Secrets, 1Password, AWS Secrets Manager
- ✅ **Never commit to git** - `.env` is gitignored
- ✅ **Delete unused keys** - Run `aws iam list-access-keys --user-name <user>`
- ✅ **Monitor with CloudTrail** - Enable for audit logging

### Troubleshooting

**"AWS CLI not configured"**
```bash
aws configure
# Enter your admin AWS credentials
```

**"Access Denied" when running script**
```bash
# Your AWS user needs these permissions:
# - iam:CreateUser, iam:CreatePolicy, iam:AttachUserPolicy
# - iam:CreateAccessKey, iam:GetUser, iam:ListAccessKeys

# Check your current identity:
aws sts get-caller-identity
```

**"User already has 2 access keys"**
```bash
# AWS limits users to 2 active access keys
# Delete old key first:
aws iam list-access-keys --user-name field-intake-service-terraform-dev
aws iam delete-access-key --user-name field-intake-service-terraform-dev --access-key-id AKIA...
```

### Cleanup

To delete IAM resources created by this script:

```bash
# List and delete access keys
aws iam list-access-keys --user-name field-intake-service-terraform-dev
aws iam delete-access-key --user-name field-intake-service-terraform-dev --access-key-id AKIA...

# Detach policy
aws iam detach-user-policy \
  --user-name field-intake-service-terraform-dev \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/field-intake-service-terraform-policy-dev

# Delete user
aws iam delete-user --user-name field-intake-service-terraform-dev

# Delete policy
aws iam delete-policy --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/field-intake-service-terraform-policy-dev
```
