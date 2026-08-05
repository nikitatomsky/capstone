output "api_endpoint" {
  description = "TODO: API Gateway base URL for Telegram webhook registration."
  value       = "<api-gateway-endpoint>"
}

output "webhook_url" {
  description = "TODO: Full Telegram webhook URL."
  value       = "<api-gateway-endpoint>/webhook"
}

output "intake_table_name" {
  description = "TODO: DynamoDB table name for completed intake records."
  value       = var.intake_table_name
}

output "manager_notification_topic_name" {
  description = "TODO: SNS topic name for manager notifications."
  value       = var.manager_notification_topic_name
}

# DynamoDB module outputs
output "assignments_table_name" {
  description = "Name of the assignments DynamoDB table"
  value       = module.dynamodb.assignments_table_name
}

output "assignments_table_arn" {
  description = "ARN of the assignments DynamoDB table"
  value       = module.dynamodb.assignments_table_arn
}

output "technicians_table_name" {
  description = "Name of the technicians DynamoDB table"
  value       = module.dynamodb.technicians_table_name
}

output "technicians_table_arn" {
  description = "ARN of the technicians DynamoDB table"
  value       = module.dynamodb.technicians_table_arn
}

output "intake_records_table_name" {
  description = "Name of the intake_records DynamoDB table"
  value       = module.dynamodb.intake_records_table_name
}

output "intake_records_table_arn" {
  description = "ARN of the intake_records DynamoDB table"
  value       = module.dynamodb.intake_records_table_arn
}

output "assignments_status_index_name" {
  description = "Name of the StatusIndex GSI on assignments table"
  value       = module.dynamodb.assignments_status_index_name
}

output "assignments_technician_index_name" {
  description = "Name of the TechnicianIndex GSI on assignments table"
  value       = module.dynamodb.assignments_technician_index_name
}

output "intake_records_assignment_index_name" {
  description = "Name of the AssignmentIndex GSI on intake_records table"
  value       = module.dynamodb.intake_records_assignment_index_name
}

# Telegram invitations table outputs
output "telegram_invitations_table_name" {
  description = "Name of the Telegram invitations DynamoDB table"
  value       = module.dynamodb.telegram_invitations_table_name
}

output "telegram_invitations_table_arn" {
  description = "ARN of the Telegram invitations DynamoDB table"
  value       = module.dynamodb.telegram_invitations_table_arn
}

# Secrets Manager outputs
output "telegram_bot_token_secret_name" {
  description = "Name of the Telegram bot token secret"
  value       = module.secretsmanager.telegram_bot_token_secret_name
}

output "telegram_bot_token_secret_arn" {
  description = "ARN of the Telegram bot token secret"
  value       = module.secretsmanager.telegram_bot_token_secret_arn
}

# IAM policy outputs
output "telegram_backend_policy_arn" {
  description = "ARN of the Telegram backend IAM policy"
  value       = module.iam.telegram_backend_policy_arn
}

output "telegram_backend_policy_name" {
  description = "Name of the Telegram backend IAM policy"
  value       = module.iam.telegram_backend_policy_name
}

# SES outputs
output "ses_configuration_set_name" {
  description = "Name of the SES configuration set for email delivery"
  value       = module.ses.configuration_set_name
}

output "ses_send_policy_arn" {
  description = "ARN of the IAM policy for sending emails via SES"
  value       = module.ses.ses_send_policy_arn
}

output "ses_bounces_topic_arn" {
  description = "ARN of the SNS topic for SES bounce notifications"
  value       = module.ses.bounces_topic_arn
}

output "ses_domain_verification_token" {
  description = "Domain verification token for DNS (if using domain identity)"
  value       = module.ses.domain_verification_token
  sensitive   = true
}
