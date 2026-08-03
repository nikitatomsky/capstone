# Functional Requirements

## FR-1: Infrastructure as Code

- Terraform placeholders define the target AWS serverless architecture.
- The dev stack models API Gateway, Lambda, DynamoDB, SNS, CloudWatch Logs, and IAM boundaries.
- State backend, provider region, and account-specific values remain TODO placeholders.

## FR-2: CI/CD Pipeline

- GitHub Actions placeholders include reusable lint, test, security scan, Terraform plan, and artifact build jobs.
- Pull requests and pushes to `main` call the reusable golden-path workflow.
- OIDC permissions are reserved for future AWS authentication.

## FR-3: Deployment and Release

- The local demo runs with `uvicorn` on port `4000` and an ngrok HTTPS tunnel.
- The cloud target packages the same FastAPI app for Lambda via Mangum.
- Terraform apply and webhook repointing are stretch goals unless explicitly enabled.

## FR-4: Observability

- Local logging captures webhook handling, validation outcomes, persistence results, and downstream notification status.
- CloudWatch Logs capture Lambda and API Gateway events in the target architecture.
- Metrics and alerting thresholds are TODO.

## FR-5: Pull Request and Adoption Documentation

- Documentation explains local demo setup, cloud-shaped design, CI expectations, and required secrets.
- Adoption notes identify which placeholders must be completed before production use.

## Application Behavior TODOs

- Define required intake fields and valid value ranges in the Pydantic schema.
- Define the maximum number of follow-up prompts before handing off to a human.
- Define ticketing API payload shape and failure handling.
- Define manager notification content and delivery rules.
