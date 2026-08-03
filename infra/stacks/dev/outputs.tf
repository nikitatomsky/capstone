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
