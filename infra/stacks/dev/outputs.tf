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
