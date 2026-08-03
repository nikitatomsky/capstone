# Coding Guidelines

## Runtime

- Use Python 3.12.
- Use FastAPI for HTTP routes.
- Use Pydantic v2 for structured intake models and validation.
- Use Mangum only at the Lambda adapter boundary.

## Package Management

- Prefer Poetry unless the team chooses pip.
- Keep runtime, test, lint, and cloud SDK dependencies explicit in `packages/api/pyproject.toml`.

## Boundaries

- Keep route handlers thin; delegate session state, extraction, validation, persistence, ticketing, and notification behavior to services.
- Hide SQLite and DynamoDB behind a storage interface.
- Hide Telegram manager chat and SNS behind a notification interface.
- Keep the LLM prompt and extraction schema easy to test without a live webhook.

## Error Handling

- Do not infer missing or ambiguous user fields silently.
- Return targeted follow-up prompts for incomplete records.
- Log integration failures without exposing secrets or raw credentials.

## TODO

- Choose formatter and linter settings, such as Ruff format/check.
- Define module naming conventions after implementation files are created.
- Define retry and timeout policy for LLM, Telegram, ticketing, and AWS SDK calls.
