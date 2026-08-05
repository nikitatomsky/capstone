# SES Module

Terraform module for AWS Simple Email Service (SES) configuration for Field Intake Service email delivery.

## Purpose

This module configures AWS SES for sending Telegram invitation links via email. It supports both domain-based and email address-based identities.

## Features

- **Domain or Email Identity**: Configure SES with either a verified domain or individual email address
- **Configuration Set**: Track email delivery metrics
- **Bounce Handling**: SNS topic for bounce and complaint notifications
- **IAM Policy**: Scoped permissions for Lambda to send emails

## Usage

### With Domain Identity

```hcl
module "ses" {
  source = "../../modules/ses"

  environment = "dev"
  domain_name = "example.com"
  aws_region  = "us-east-1"
}
```

### With Email Identity (for testing/dev)

```hcl
module "ses" {
  source = "../../modules/ses"

  environment = "dev"
  from_email  = "noreply@example.com"
  aws_region  = "us-east-1"
}
```

## Verification Steps

### Domain Identity

1. Apply Terraform to create the domain identity
2. Retrieve the verification token: `terraform output domain_verification_token`
3. Add TXT record to DNS:
   - Name: `_amazonses.example.com`
   - Value: `<verification_token>`
4. Wait for verification (can take up to 72 hours, usually minutes)

### Email Identity

1. Apply Terraform to create the email identity
2. Check the email inbox for verification email from AWS
3. Click the verification link
4. Email is immediately available for sending

## Sandbox Mode

By default, SES accounts are in **sandbox mode**:
- Can only send to verified email addresses
- Limited to 200 emails per day
- 1 email per second

To move to **production**:
1. Open AWS SES console
2. Request production access
3. Provide use case details
4. Wait for AWS approval (usually 24 hours)

## Outputs

- `ses_send_policy_arn`: Attach to Lambda IAM role
- `configuration_set_name`: Use in email sending code
- `bounces_topic_arn`: Subscribe to monitor bounces

## Environment Variables

Set these in your Lambda environment:

```bash
USE_AWS_SES=true
SES_FROM_EMAIL=noreply@example.com
SES_CONFIGURATION_SET=<configuration_set_name>
AWS_REGION=us-east-1
```

## Cost

SES pricing (as of 2026):
- First 62,000 emails/month: **$0** (free tier)
- After that: $0.10 per 1,000 emails
- Bounce notifications (SNS): $0.50 per 1 million requests

For typical invitation volume (< 1000/month), cost is **$0.00**.
