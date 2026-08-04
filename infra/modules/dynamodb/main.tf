# DynamoDB tables for Field Intake Service
# Assignment workflow storage: assignments, technicians, intake_records

# Assignments table
resource "aws_dynamodb_table" "assignments" {
  name         = "field-intake-assignments-${var.environment}"
  billing_mode = "PAY_PER_REQUEST" # On-demand pricing
  hash_key     = "assignment_id"

  attribute {
    name = "assignment_id"
    type = "S" # String (UUID)
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "technician_id"
    type = "S" # String (UUID)
  }

  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "status"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "TechnicianIdIndex"
    hash_key        = "technician_id"
    projection_type = "ALL"
  }

  tags = {
    Environment = var.environment
    Project     = "field-intake-service"
  }
}

# Technicians table
resource "aws_dynamodb_table" "technicians" {
  name         = "field-intake-technicians-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "technician_id"

  attribute {
    name = "technician_id"
    type = "S" # UUID primary key
  }

  attribute {
    name = "chat_id"
    type = "N" # Telegram chat_id (optional, for backward compatibility)
  }

  # GSI for looking up technicians by Telegram chat_id
  global_secondary_index {
    name            = "ChatIdIndex"
    hash_key        = "chat_id"
    projection_type = "ALL"
  }

  tags = {
    Environment = var.environment
    Project     = "field-intake-service"
  }
}

# Intake records table
resource "aws_dynamodb_table" "intake_records" {
  name         = "field-intake-records-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "record_id"

  attribute {
    name = "record_id"
    type = "S" # UUID
  }

  attribute {
    name = "assignment_id"
    type = "S" # Foreign key to assignments
  }

  global_secondary_index {
    name            = "AssignmentIndex"
    hash_key        = "assignment_id"
    projection_type = "ALL"
  }

  tags = {
    Environment = var.environment
    Project     = "field-intake-service"
  }
}

# Telegram invitations table
# Stores temporary invitation tokens for chat ID linking
resource "aws_dynamodb_table" "telegram_invitations" {
  name         = "field-intake-telegram-invitations-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "token_hash"

  attribute {
    name = "token_hash"
    type = "S" # SHA-256 hash of invitation token
  }

  attribute {
    name = "technician_id"
    type = "S" # UUID of technician
  }

  # GSI for looking up invitations by technician
  global_secondary_index {
    name            = "TechnicianIdIndex"
    hash_key        = "technician_id"
    projection_type = "ALL"
  }

  # Enable TTL for automatic cleanup of expired invitations
  ttl {
    attribute_name = "expires_at_ttl"
    enabled        = true
  }

  tags = {
    Name        = "Telegram Invitations"
    Environment = var.environment
    Project     = "field-intake-service"
    Purpose     = "Temporary invitation tokens for Telegram bot linking"
  }
}
