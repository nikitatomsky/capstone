# Serverless API Module Placeholder

Reusable Terraform module boundary for the Field Intake Service target architecture.

## Expected Resources

- API Gateway HTTP API with `POST /webhook`
- Lambda running FastAPI through Mangum
- DynamoDB table for completed intake records
- SNS topic for manager notifications
- CloudWatch log groups
- IAM execution role and least-privilege policies

## TODO

- Add module variables, resources, outputs, and tests.
- Decide whether Lambda packaging uses zip artifacts or container images.
- Add optional health route integration after `<health-path>` is finalized.