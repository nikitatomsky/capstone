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
  region = var.aws_region
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
