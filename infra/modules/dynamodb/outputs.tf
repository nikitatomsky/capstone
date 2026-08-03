# Assignments table outputs
output "assignments_table_name" {
  description = "Name of the assignments DynamoDB table"
  value       = aws_dynamodb_table.assignments.name
}

output "assignments_table_arn" {
  description = "ARN of the assignments DynamoDB table"
  value       = aws_dynamodb_table.assignments.arn
}

output "assignments_status_index_name" {
  description = "Name of the StatusIndex GSI on assignments table"
  value       = "StatusIndex"
}

output "assignments_technician_index_name" {
  description = "Name of the TechnicianIndex GSI on assignments table"
  value       = "TechnicianIndex"
}

# Technicians table outputs
output "technicians_table_name" {
  description = "Name of the technicians DynamoDB table"
  value       = aws_dynamodb_table.technicians.name
}

output "technicians_table_arn" {
  description = "ARN of the technicians DynamoDB table"
  value       = aws_dynamodb_table.technicians.arn
}

# Intake records table outputs
output "intake_records_table_name" {
  description = "Name of the intake_records DynamoDB table"
  value       = aws_dynamodb_table.intake_records.name
}

output "intake_records_table_arn" {
  description = "ARN of the intake_records DynamoDB table"
  value       = aws_dynamodb_table.intake_records.arn
}

output "intake_records_assignment_index_name" {
  description = "Name of the AssignmentIndex GSI on intake_records table"
  value       = "AssignmentIndex"
}
