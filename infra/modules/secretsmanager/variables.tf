variable "project_name" {
  description = "Project name prefix"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "telegram_bot_token" {
  description = "Telegram bot token (leave empty to set manually via AWS CLI)"
  type        = string
  default     = ""
  sensitive   = true
}
