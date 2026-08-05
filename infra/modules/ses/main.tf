# AWS SES configuration for Field Intake Service
# Email delivery for Telegram invitation links

# Domain identity for SES (if using domain-based sending)
resource "aws_ses_domain_identity" "main" {
  count  = var.domain_name != "" ? 1 : 0
  domain = var.domain_name
}

# Email address identity for SES (if using single email address)
resource "aws_ses_email_identity" "from_email" {
  count = var.from_email != "" ? 1 : 0
  email = var.from_email
}

# SES configuration set for tracking
resource "aws_ses_configuration_set" "main" {
  name = "field-intake-${var.environment}"

  delivery_options {
    tls_policy = "Require"
  }

  reputation_metrics_enabled = true
}

# SNS topic for SES bounce notifications (optional but recommended)
resource "aws_sns_topic" "ses_bounces" {
  name = "field-intake-ses-bounces-${var.environment}"

  tags = {
    Environment = var.environment
    Project     = "field-intake-service"
  }
}

# SES event destination for bounces
resource "aws_ses_event_destination" "bounces" {
  name                   = "bounce-notifications"
  configuration_set_name = aws_ses_configuration_set.main.name
  enabled                = true
  matching_types         = ["bounce", "complaint"]

  sns_destination {
    topic_arn = aws_sns_topic.ses_bounces.arn
  }
}

# IAM policy for Lambda to send emails via SES
data "aws_iam_policy_document" "ses_send" {
  statement {
    sid    = "AllowSESSendEmail"
    effect = "Allow"

    actions = [
      "ses:SendEmail",
      "ses:SendRawEmail",
    ]

    resources = var.domain_name != "" ? [
      aws_ses_domain_identity.main[0].arn
    ] : var.from_email != "" ? [
      aws_ses_email_identity.from_email[0].arn
    ] : ["*"]
  }
}

resource "aws_iam_policy" "ses_send" {
  name        = "field-intake-ses-send-${var.environment}"
  description = "Allow sending emails via SES for invitation delivery"
  policy      = data.aws_iam_policy_document.ses_send.json

  tags = {
    Environment = var.environment
    Project     = "field-intake-service"
  }
}
