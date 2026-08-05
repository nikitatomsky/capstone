# SES module outputs

output "domain_identity_arn" {
  description = "ARN of the SES domain identity"
  value       = var.domain_name != "" ? aws_ses_domain_identity.main[0].arn : null
}

output "email_identity_arn" {
  description = "ARN of the SES email identity"
  value       = var.from_email != "" ? aws_ses_email_identity.from_email[0].arn : null
}

output "configuration_set_name" {
  description = "Name of the SES configuration set"
  value       = aws_ses_configuration_set.main.name
}

output "ses_send_policy_arn" {
  description = "ARN of the IAM policy for sending emails via SES"
  value       = aws_iam_policy.ses_send.arn
}

output "bounces_topic_arn" {
  description = "ARN of the SNS topic for SES bounce notifications"
  value       = aws_sns_topic.ses_bounces.arn
}

output "domain_verification_token" {
  description = "Domain verification token for DNS (only for domain identity)"
  value       = var.domain_name != "" ? aws_ses_domain_identity.main[0].verification_token : null
  sensitive   = true
}
