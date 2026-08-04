# IAM Permissions for Telegram Invitation System

This module creates an IAM policy that grants least-privilege access to:
- AWS Secrets Manager (read Telegram bot token)
- DynamoDB telegram-invitations table (CRUD operations)

## Local Development

Attach the policy to your IAM user:

```bash
# Get the policy ARN from Terraform outputs
cd infra/stacks/dev
terraform output telegram_backend_policy_arn

# Attach policy to your IAM user
aws iam attach-user-policy \
  --user-name YOUR_IAM_USER \
  --policy-arn $(terraform output -raw telegram_backend_policy_arn)
```

## Lambda Deployment (Future)

When deploying to AWS Lambda, this policy will be attached to the Lambda execution role instead of a user.

## Permissions Granted

### Secrets Manager
- `secretsmanager:GetSecretValue` - Read the Telegram bot token secret

### DynamoDB
- `dynamodb:PutItem` - Create invitation tokens
- `dynamodb:GetItem` - Retrieve invitation by token hash
- `dynamodb:UpdateItem` - Update invitation status
- `dynamodb:DeleteItem` - Delete used/expired tokens
- `dynamodb:Query` - Query invitations by technician ID (via GSI)

## Security Notes

- Policy uses least-privilege principle
- Scoped to specific secret and table patterns
- Environment-specific (dev, staging, prod)
- Does NOT grant broad AdministratorAccess
