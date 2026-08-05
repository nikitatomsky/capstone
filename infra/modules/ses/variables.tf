# SES module variables

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "domain_name" {
  description = "Domain name for SES identity (e.g., example.com). Leave empty to use email identity instead."
  type        = string
  default     = ""
}

variable "from_email" {
  description = "Email address for SES identity (e.g., noreply@example.com). Used if domain_name is empty."
  type        = string
  default     = ""
}

variable "aws_region" {
  description = "AWS region for SES"
  type        = string
  default     = "us-east-1" # SES is available in limited regions
}
