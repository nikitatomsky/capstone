project_name                    = "field-intake-service"
environment                     = "dev"
aws_region                      = "us-east-1"
lambda_runtime                  = "python3.12"
lambda_handler                  = "app.lambda_handler.handler"
lambda_artifact_path            = "<lambda-artifact-path>"
webhook_path                    = "/webhook"
health_path                     = "<health-path>"
intake_table_name               = "field-intake-service-dev-intake-records"
manager_notification_topic_name = "field-intake-service-dev-manager-notifications"
log_retention_days              = 14

# SES Configuration
# Option 1: Use email identity (for dev/testing)
ses_from_email = "nikita.tomsky@gmail.com" # Your Gmail will need verification

# Option 2: Use domain identity (for production)
# ses_domain_name = "example.com" # Replace with your verified domain
# ses_from_email  = "" # Leave empty when using domain
