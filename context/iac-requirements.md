# IaC Requirements

## Target Pattern

Serverless API golden path for AWS:

- API Gateway HTTP API receives Telegram webhook requests.
- Lambda runs the FastAPI app through Mangum.
- DynamoDB stores completed intake records.
- SNS sends manager notifications.
- CloudWatch Logs captures API and Lambda logs.
- IAM roles and policies grant least-privilege access to DynamoDB, SNS, and logs.

## Terraform Layout

```text
infra/modules/serverless-api/  TODO module for reusable serverless API resources
infra/stacks/dev/             TODO dev stack calling the serverless API module
```

## Module Inputs TODO

- `project_name`
- `environment`
- `aws_region`
- `lambda_runtime`, expected `python3.12`
- `lambda_handler`
- `lambda_artifact_path`
- `webhook_path`, expected `/webhook`
- `health_path`, placeholder `<health-path>`
- `intake_table_name`
- `manager_notification_topic_name`
- `log_retention_days`

## State Backend TODO

- Backend type: `<terraform-backend-type>`
- Backend bucket/table/workspace: `<terraform-state-backend>`
- State locking: `<state-locking-strategy>`

## Constraints

- Do not store credentials, API keys, bot tokens, or account-specific secrets in Terraform files.
- Do not run `terraform apply` unless explicitly approved for the environment.
- Keep demo cost controls documented before enabling persistent cloud resources.
