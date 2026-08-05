terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # TODO: Configure remote state backend outside this template.
}

provider "aws" {
  region                   = var.aws_region
  skip_metadata_api_check  = true  # Disable EC2 instance metadata service checks
  skip_region_validation   = true  # Skip region validation
  skip_requesting_account_id = true  # Skip account ID lookup
  # Note: Uses environment variables AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN
}

# DynamoDB tables for assignment workflow
module "dynamodb" {
  source      = "../../modules/dynamodb"
  environment = var.environment
}

# AWS Secrets Manager for sensitive configuration
module "secretsmanager" {
  source = "../../modules/secretsmanager"

  project_name = var.project_name
  environment  = var.environment

  # Leave empty - will be set manually via AWS CLI
  telegram_bot_token = ""
}

# IAM permissions for Telegram backend
module "iam" {
  source = "../../modules/iam"

  project_name = var.project_name
  environment  = var.environment
}

# AWS SES for email delivery (invitation links)
module "ses" {
  source = "../../modules/ses"

  environment = var.environment
  from_email  = var.ses_from_email
  domain_name = var.ses_domain_name
  aws_region  = var.aws_region
}

# TODO: Replace this placeholder with a call to infra/modules/serverless-api.
# Expected resources: API Gateway HTTP API, Lambda, DynamoDB, SNS, CloudWatch Logs, IAM.
#
# module "serverless_api" {
#   source = "../../modules/serverless-api"
#
#   project_name                    = var.project_name
#   environment                     = var.environment
#   aws_region                      = var.aws_region
#   lambda_runtime                  = var.lambda_runtime
#   lambda_handler                  = var.lambda_handler
#   lambda_artifact_path            = var.lambda_artifact_path
#   webhook_path                    = var.webhook_path
#   health_path                     = var.health_path
#   intake_table_name               = var.intake_table_name
#   manager_notification_topic_name = var.manager_notification_topic_name
#   log_retention_days              = var.log_retention_days
# }
