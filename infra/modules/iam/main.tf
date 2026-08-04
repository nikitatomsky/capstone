# IAM policy for backend to access Telegram bot token and invitations table
# Least-privilege access to Secrets Manager and DynamoDB

resource "aws_iam_policy" "telegram_backend_policy" {
  name        = "${var.project_name}-telegram-backend-${var.environment}"
  description = "Policy for backend to access Telegram bot token and invitations"
  policy      = file("${path.module}/telegram-backend-policy.json")

  tags = {
    Name        = "Telegram Backend Policy"
    Environment = var.environment
    Project     = var.project_name
  }
}

# For local development (attach to user/role as needed)
# For Lambda (would attach to Lambda execution role)
