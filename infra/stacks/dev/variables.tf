variable "project_name" {
  description = "Project name used for resource naming."
  type        = string
  default     = "field-intake-service"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for the target stack."
  type        = string
  default     = "<aws-region>"
}

variable "lambda_runtime" {
  description = "Lambda runtime for the FastAPI application."
  type        = string
  default     = "python3.12"
}

variable "lambda_handler" {
  description = "Lambda handler for the Mangum adapter."
  type        = string
  default     = "app.lambda_handler.handler"
}

variable "lambda_artifact_path" {
  description = "Path to the packaged Lambda artifact."
  type        = string
  default     = "<lambda-artifact-path>"
}

variable "webhook_path" {
  description = "Telegram webhook route path."
  type        = string
  default     = "/webhook"
}

variable "health_path" {
  description = "Health or readiness route path."
  type        = string
  default     = "<health-path>"
}

variable "intake_table_name" {
  description = "DynamoDB table name for completed intake records."
  type        = string
  default     = "field-intake-service-dev-intake-records"
}

variable "manager_notification_topic_name" {
  description = "SNS topic name for manager notifications."
  type        = string
  default     = "field-intake-service-dev-manager-notifications"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days."
  type        = number
  default     = 14
}

# SES Configuration
variable "ses_from_email" {
  description = "Email address for SES identity (e.g., noreply@example.com). Used for sending invitation emails."
  type        = string
  default     = ""
}

variable "ses_domain_name" {
  description = "Domain name for SES identity (e.g., example.com). Leave empty to use email identity instead."
  type        = string
  default     = ""
}
