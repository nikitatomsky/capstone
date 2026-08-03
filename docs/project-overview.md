# Field Intake Service — Project Overview

## What This Project Is

The **Field Intake Service** is a conversational AI intake system that lets
field employees report service call or inspection outcomes through a chat
interface instead of filling out manual forms. Employees describe their work
in free text; an LLM extracts structured data, validates it for completeness,
and asks targeted follow-up questions when information is missing. Once a
record is complete, it is persisted and pushed to a downstream system of
record, with a summary notification sent to a manager.

It represents a common enterprise pattern — **structured intake via
conversational AI** — applicable across verticals (field service, incident
reporting, delivery exceptions, inspections) wherever employees need to
report unstructured information that a downstream system requires in
structured form.

**Scope for this build:** a fully working local demo — real Telegram bot,
real LLM extraction and validation loop, real persistence — running on a
laptop via `uvicorn` + `ngrok`. No cloud resources are provisioned. The AWS
deployment (Lambda, DynamoDB, SNS, Terraform) is designed and documented as a
target architecture, and provisioned only if time allows.

The goal is **not** the chatbot alone, but demonstrating the pipeline —
extraction, validation, persistence, integration — end to end, in a way that
maps cleanly onto a production architecture without requiring one to exist.

## Architecture

### Local demo (built)

```
┌────────────────────────────────────────────────────────────┐
│  Field Employee (mobile)                                   │
│  Telegram client                                            │
└───────────────────────┬────────────────────────────────────┘
                        │ Webhook (HTTPS via ngrok tunnel)
┌───────────────────────▼────────────────────────────────────┐
│  FastAPI app (uvicorn, localhost:4000)                     │
│  Routes: POST /webhook                                     │
│  Services (Python):                                         │
│    session_service.py   session/state per chat_id           │
│    extraction_agent.py  LLM call — free text → structured   │
│    validation_service.py field/range checks (Pydantic)      │
└───────────────────────┬────────────────────────────────────┘
                        │
        ┌───────────────┼────────────────┐
        ▼                ▼                ▼
┌───────────────┐ ┌──────────────┐ ┌──────────────────┐
│  SQLite        │ │ Ticketing API │ │ Manager           │
│  intake records│ │ (stub/mock)   │ │ notification       │
│                │ │               │ │ (2nd Telegram chat)│
└───────────────┘ └──────────────┘ └──────────────────┘
```

### Target cloud architecture (documented; stretch goal)

```
Telegram → API Gateway → Lambda (same FastAPI app via Mangum)
                              │
              ┌───────────────┼────────────────┐
              ▼                ▼                ▼
          DynamoDB       Ticketing API        SNS → Manager
        (replaces SQLite)  (real integration)  (email/SMS)

Logs/metrics: CloudWatch. Provisioned via Terraform (infra/stacks/dev).
```

The application code is written so the swap from local to cloud is
**config, not rewrite** — the same FastAPI app runs under `uvicorn` locally
and under Lambda (via the Mangum adapter) in the cloud; storage and
notification clients are abstracted behind an interface so SQLite → DynamoDB
and Telegram-chat → SNS are drop-in swaps.

### AWS resources (target deployment)

| Resource | Purpose | Demo-scale cost |
|---|---|---|
| Lambda function | Runs the FastAPI app via Mangum | Free tier: 1M requests + 400,000 GB-seconds/month |
| API Gateway (HTTP API) | Public HTTPS endpoint for the Telegram webhook | Free tier: 1M requests/month (first 12 months); $1.00/million after |
| DynamoDB table | Intake record storage | Free tier: 25GB storage + 25 RCU/WCU, always free |
| SNS topic | Manager notification delivery | Free tier: 1,000 email notifications/month; SMS billed per message |
| CloudWatch Logs | Lambda + API Gateway logs | Free tier: 5GB ingestion + 5GB storage/month |
| IAM role/policies | Lambda execution permissions (DynamoDB, SNS, CloudWatch) | No cost |
| Data transfer out | API responses to Telegram/clients | Free tier: 100GB/month |

At demo volume (a few dozen to a few hundred requests), this stack stays
within AWS's free tier — expect **$0.00–$1.00 total**, plus normal LLM API
usage costs (Anthropic/OpenAI), which are separate from AWS and the larger
of the two at this scale. The main cost discipline is remembering to
`terraform destroy` after the demo so nothing lingers past free-tier limits.

## Tech Stack

| Layer | Technology (demo) | Cloud target (stretch) |
|---|---|---|
| Bot interface | Telegram Bot API | same |
| Backend | Python 3.12 + FastAPI, run via `uvicorn` | same app, deployed to AWS Lambda via Mangum |
| LLM integration | Anthropic/OpenAI Python SDK | same |
| Data validation | Pydantic v2 | same |
| Storage | SQLite | DynamoDB (via boto3) |
| Downstream integration | Ticketing system API (stubbed) | same, stubbed or real depending on time |
| Notifications | Second Telegram chat (manager-facing) | Amazon SNS (email/SMS) |
| Tunneling | ngrok (dev webhook exposure) | not needed — API Gateway is public |
| Testing | Pytest | same |
| Package management | Poetry (or pip) | same |
| IaC | — | Terraform >= 1.5, AWS provider ~> 5.0 (written, applied only if time allows) |
| CI/CD | — | GitHub Actions (stretch) |
| Observability | Local logging | CloudWatch Logs (stretch) |

## Repository Structure

```
backend/                      Python service — API + AI core
  app/
    main.py                    FastAPI app (entrypoint for local + Lambda)
    lambda_handler.py          Mangum adapter — unused until/unless deployed
    routers/
      webhook.py                POST /webhook — Telegram entrypoint
    services/
      session_service.py       Per-employee conversation state
      extraction_agent.py      LLM prompt + schema-constrained extraction
      validation_service.py    Pydantic models + field-level validation
      ticketing_client.py      Downstream system integration (stub)
      notification_client.py   Manager notification — Telegram chat (SQLite/dev),
                                swappable for SNS (cloud)
      storage_client.py        Storage interface — SQLite implementation now,
                                DynamoDB implementation if time allows
    models/
      intake_record.py         Pydantic schema for a completed record
  tests/                        Pytest tests
  pyproject.toml                Poetry config / dependencies
infra/stacks/dev/              Terraform for target cloud deployment (written;
                                applied only if time allows) — not required to
                                run the demo
.github/workflows/             CI/CD (stretch — not required to run the demo)
```

## Key Design Decisions

1. **Local-first demo, cloud-shaped code** — the app runs entirely on a
   laptop for the demo (`uvicorn` + `ngrok`), but is structured so it could
   be deployed to AWS with configuration changes, not a rewrite.
2. **Storage and notification behind interfaces** — `storage_client.py` and
   `notification_client.py` are thin abstractions so SQLite → DynamoDB and
   Telegram-chat → SNS are swap-in implementations, not redesigns.
3. **AI core is reusable, schema is not** — `extraction_agent.py` and
   `validation_service.py` are domain-agnostic; only the Pydantic schema in
   `models/intake_record.py` and `ticketing_client.py` change per use case.
4. **Human-in-the-loop by design** — the system never infers missing or
   ambiguous fields; it re-prompts the employee directly, bounded to a small
   number of follow-up rounds, before persisting anything.
5. **Stubbed ticketing integration** — represents a real system-of-record
   call (ServiceNow, Salesforce Field Service) without requiring production
   credentials.
6. **IaC written, not necessarily applied** — Terraform for the target AWS
   deployment is authored as documentation of the intended architecture;
   applying it is a stretch goal, not a demo dependency.

## Getting Started

### Prerequisites

- Python 3.12+
- Poetry (or pip)
- A Telegram bot token (via [@BotFather](https://t.me/BotFather)) — two bots
  recommended: one for employee intake, one for manager notifications
- An LLM API key (Anthropic or OpenAI)
- `ngrok` or equivalent for exposing the local webhook

### Installation

```bash
git clone <repo-url>
cd field-intake-service/backend
poetry install                 # or: pip install -r requirements.txt
cp .env.example .env           # TELEGRAM_BOT_TOKEN, MANAGER_BOT_TOKEN, LLM_API_KEY
```

### Development Workflow

1. Run the API locally:
   ```bash
   poetry run uvicorn app.main:app --reload --port 4000
   ```
2. Expose it for Telegram's webhook:
   ```bash
   ngrok http 4000
   ```
3. Register the webhook:
   ```bash
   curl -F "url=https://<ngrok-id>.ngrok.io/webhook" \
     https://api.telegram.org/bot<TOKEN>/setWebhook
   ```
4. Message the bot to trigger a session; iterate on prompts in
   `app/services/extraction_agent.py`.
5. Run tests before committing:
   ```bash
   poetry run pytest
   ```

### Cloud Deployment (stretch goal, if time allows)

1. Review/finish Terraform in `infra/stacks/dev` — provisions Lambda, API
   Gateway, DynamoDB, SNS, CloudWatch Logs, and the IAM role/policies tying
   them together (see AWS resources table above).
2. Swap `storage_client.py` to the DynamoDB implementation and
   `notification_client.py` to the SNS implementation.
3. Provision infrastructure:
   ```bash
   cd infra/stacks/dev
   terraform init
   terraform apply
   ```
4. Package the Python app for Lambda and re-point the Telegram webhook to
   the deployed API Gateway URL.
5. When done demoing, tear down to stay within free-tier limits:
   ```bash
   terraform destroy
   ```
