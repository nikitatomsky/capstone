# CI Requirements

## Reusable Workflow

The reusable workflow in `.github/workflows/golden-path-ci.yml` should support a Python 3.12 FastAPI service using Poetry.

Required placeholder jobs:

- lint: install dependencies and run Ruff or the selected linter
- test: run Pytest
- security-scan: run dependency and secret scanning placeholders
- terraform-plan: validate and plan `infra/stacks/dev`
- artifact-build: build the Lambda deployment artifact when packaging is defined

## Caller Workflow

The caller workflow in `.github/workflows/field-intake-service-ci.yml` should:

- Trigger on pull requests.
- Trigger on pushes to `main`.
- Call the reusable workflow.
- Pass Python version `3.12`.
- Declare least-privilege permissions.
- Include `id-token: write` only for OIDC-based AWS authentication.

## TODO

- Confirm whether CI should publish Lambda artifacts, container images, or neither.
- Confirm whether Terraform stops at plan or applies on `main`.
- Add AWS role ARN through GitHub environment secrets, not hardcoded YAML.
- Add coverage upload only after coverage tooling is selected.
