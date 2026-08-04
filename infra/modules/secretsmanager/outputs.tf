output "telegram_bot_token_secret_name" {
  description = "Name of the Telegram bot token secret"
  value       = aws_secretsmanager_secret.telegram_bot_token.name
}

output "telegram_bot_token_secret_arn" {
  description = "ARN of the Telegram bot token secret"
  value       = aws_secretsmanager_secret.telegram_bot_token.arn
}
