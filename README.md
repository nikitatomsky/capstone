# Field Intake Service Template

Golden-path project scaffold for a conversational AI field intake service.

This project is a Python 3.12 FastAPI API service with a Telegram webhook interface. It runs locally with `uvicorn` on port `4000`, persists demo data in SQLite, and is shaped for an AWS serverless target using API Gateway, Lambda via Mangum, DynamoDB, SNS, CloudWatch Logs, and Terraform.

## Services

- api: FastAPI, port `4000`, webhook path `/webhook`, health path `<health-path>`
- persistence: SQLite locally, DynamoDB in the AWS target architecture
- notifications: Telegram manager chat locally, SNS in the AWS target architecture
- downstream integration: ticketing API stub, replaceable with a real system of record

## Repository Layout

```text
docs/                         Planning and adoption documentation
context/                      IaC and CI/CD requirements for future agents
infra/modules/serverless-api/  Placeholder Terraform module boundary
infra/stacks/dev/             Development Terraform stack placeholders
packages/api/                 Python FastAPI service placeholder
.github/workflows/            Reusable and caller CI workflow placeholders
```

## Next Steps

1. Fill in the API service implementation in `packages/api`.
2. Complete the Terraform module inputs in `infra/modules/serverless-api` and `infra/stacks/dev`.
3. Convert the CI placeholders into enforced checks once commands are final.
4. Add tests for extraction, validation, storage, and webhook behavior.

This scaffold is not production-ready; it is a template ready for the next implementation and platform hardening steps.
