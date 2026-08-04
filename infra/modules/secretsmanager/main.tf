# AWS Secrets Manager for sensitive configuration
# Telegram bot token storage

resource "aws_secretsmanager_secret" "telegram_bot_token" {
  name        = "${var.project_name}/${var.environment}/telegram-bot-token"
  description = "Telegram bot token for field intake service"

  tags = {
    Name        = "Telegram Bot Token"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Note: Secret value must be set manually or via separate process
# Do NOT store actual token in Terraform state
resource "aws_secretsmanager_secret_version" "telegram_bot_token" {
  count         = var.telegram_bot_token != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.telegram_bot_token.id
  secret_string = var.telegram_bot_token
}
