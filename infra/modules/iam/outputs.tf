output "telegram_backend_policy_arn" {
  description = "ARN of the Telegram backend IAM policy"
  value       = aws_iam_policy.telegram_backend_policy.arn
}

output "telegram_backend_policy_name" {
  description = "Name of the Telegram backend IAM policy"
  value       = aws_iam_policy.telegram_backend_policy.name
}
