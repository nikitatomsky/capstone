# Local Setup

## Required Tools

- Python 3.12+
- Poetry, or pip if the project standard is changed
- ngrok or an equivalent HTTPS tunnel for Telegram webhook testing
- Terraform >= 1.5 for validating the target AWS infrastructure placeholders
- AWS CLI for future cloud deployment work

## Required Secrets

Create `packages/api/.env` from `packages/api/.env.example` when application implementation begins.

```bash
cp packages/api/.env.example packages/api/.env
```

Do not commit real Telegram, LLM, AWS, or downstream system credentials.

## Placeholder Commands

```bash
cd packages/api
poetry install
poetry run pytest
poetry run uvicorn app.main:app --reload --port 4000
ngrok http 4000
terraform -chdir=../../infra/stacks/dev init -backend=false
terraform -chdir=../../infra/stacks/dev validate
```

## TODO

- Confirm whether Poetry or pip is the final package manager.
- Add webhook registration command once bot token handling is implemented.
- Add local SQLite migration or initialization command once persistence code exists.
- Add cloud packaging command for Lambda once deployment packaging is selected.
