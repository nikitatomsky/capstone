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
