# Field Intake Service — Project Overview

## What This Project Is

The **Field Intake Service** is an **admin-initiated assignment system** that combines a web dashboard with conversational AI. Admins create and assign service call tasks to field technicians via a web interface; technicians receive notifications and respond through Telegram chat. An LLM extracts structured data from their free-text responses, validates completeness, and asks targeted follow-up questions when information is missing. The admin sees real-time status updates in the dashboard, and when the intake record is complete, both persistence and notification workflows are triggered automatically.

It represents a modern enterprise pattern — **assignment management with conversational AI intake** — applicable across verticals (field service, incident reporting, delivery exceptions, inspections) wherever:
- Work needs to be assigned and tracked by supervisors/admins
- Field employees report outcomes via mobile chat instead of forms
- Structured data is required by downstream systems
- Real-time status visibility is critical for operations

**Scope for this build:** a fully working local demo with three components:
1. **Admin Web UI** (React SPA) — create assignments, select technicians, view real-time status
2. **Telegram Bot** — technicians receive assignments and respond conversationally
3. **FastAPI Backend** — LLM extraction, validation, persistence, and real-time updates

The demo runs entirely on a laptop via `uvicorn` + `ngrok` + Vite dev server. No cloud resources are provisioned. The AWS deployment (Lambda, DynamoDB, SNS, CloudFront, Terraform) is designed and documented as a target architecture, and provisioned only if time allows.

The goal is demonstrating the **complete assignment-to-completion workflow** — admin assignment creation → Telegram notification → conversational intake → real-time dashboard updates → completion notification — end to end, in a way that maps cleanly onto a production architecture without requiring one to exist.

## Architecture

### Local demo (current implementation)

```
┌──────────────────────────────────────────────────────────────┐
│  Admin (browser)                                             │
│  React SPA (Vite dev server, localhost:5173)                │
└─────────────────────┬────────────────────────────────────────┘
                      │ HTTP REST + SSE
                      │ (assignments, real-time updates)
┌─────────────────────▼────────────────────────────────────────┐
│  FastAPI app (uvicorn, localhost:4000)                       │
│  Routes:                                                      │
│    POST /webhook                (Telegram bot)               │
│    POST /api/assignments        (Create assignment)          │
│    GET  /api/assignments        (List assignments)           │
│    GET  /api/assignments/stream (SSE real-time updates)      │
│    GET  /api/technicians        (List technicians)           │
│  Services (Python):                                           │
│    session_service.py           (assignments + sessions)     │
│    extraction_service.py        (LLM extraction)             │
│    sse_manager.py               (Real-time updates)          │
└─────────────────────┬────────────────────────────────────────┘
                      │
        ┌─────────────┼──────────────┐
        │              │               │
        ▼              ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐
│  SQLite      │ │  Telegram    │ │  SSE Broadcast       │
│  assignments │ │  Bot API     │ │  to connected admins │
│  users       │ │  (notify     │ │  (status updates)    │
│  intake      │ │   technician)│ │                      │
│  _records    │ │              │ │                      │
└──────────────┘ └──────────────┘ └──────────────────────┘
                      │
                      ▼
           ┌────────────────────┐
           │ Field Technician   │
           │ (Telegram mobile)  │
           └────────────────────┘
```

**Workflow:**
1. Admin creates assignment in web UI, selects technician from list
2. Backend sends Telegram notification to technician's chat
3. Technician responds via Telegram with service report (free text)
4. LLM extracts structured data, asks follow-up questions for missing fields
5. Assignment status updates in real-time on admin dashboard (SSE)
6. When complete, admin sees green/completed status with full intake record

### Target cloud architecture (documented; stretch goal)

```
┌──────────────────────────────────────────────────────────────┐
│  Admin (browser)                                             │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
            CloudFront + S3 (static SPA)
                      │
                      ▼
            API Gateway (HTTP API)
                      │
                      ▼
            Lambda (FastAPI via Mangum)
                      │
      ┌───────────────┼─────────────────┐
      ▼                ▼                  ▼
  DynamoDB      Telegram Bot API    SNS/SQS
 (assignments,   (notify technician)  (real-time
  users,                               updates to
  intake_records)                      admins)
      │
      └─→ Ticketing API integration
          (ServiceNow, Salesforce, etc.)

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
| CloudFront + S3 | Serve admin SPA static files | Free tier: 1TB data transfer out/month (first 12 months); $0.085/GB after |
| Lambda function | Runs the FastAPI app via Mangum | Free tier: 1M requests + 400,000 GB-seconds/month |
| API Gateway (HTTP API) | Public HTTPS endpoint for REST API + webhooks | Free tier: 1M requests/month (first 12 months); $1.00/million after |
| DynamoDB table | Assignments, users, intake records storage | Free tier: 25GB storage + 25 RCU/WCU, always free |
| SNS topic | Admin notification delivery (or SQS for real-time updates) | Free tier: 1,000 notifications/month; SMS billed per message |
| CloudWatch Logs | Lambda + API Gateway logs | Free tier: 5GB ingestion + 5GB storage/month |
| IAM role/policies | Lambda execution permissions (DynamoDB, SNS, CloudWatch) | No cost |

At demo volume (a few dozen to a few hundred requests), this stack stays
within AWS's free tier — expect **$0.00–$2.00 total**, plus normal LLM API
usage costs (Anthropic/OpenAI), which are separate from AWS and the larger
of the two at this scale. The main cost discipline is remembering to
`terraform destroy` after the demo so nothing lingers past free-tier limits.

## Tech Stack

| Layer | Technology (demo) | Cloud target (stretch) |
|---|---|---|
| Admin UI | React 18 + Vite, served via dev server | Static build served from S3 + CloudFront |
| UI Components | Tailwind CSS, React Query (data fetching) | same |
| Real-time updates | EventSource (SSE) | same, or SNS → WebSocket API Gateway |
| Bot interface | Telegram Bot API | same |
| Backend | Python 3.12 + FastAPI, run via `uvicorn` | same app, deployed to AWS Lambda via Mangum |
| LLM integration | Anthropic/OpenAI Python SDK | same |
| Data validation | Pydantic v2 | same |
| Storage | SQLite (assignments, users, intake_records) | DynamoDB (via boto3) |
| Authentication | Simple JWT or API key | AWS Cognito + IAM |
| Notifications | Telegram Bot API (to technicians) | same |
| Admin notifications | SSE broadcast | SNS or SQS → WebSocket |
| Tunneling | ngrok (dev webhook exposure) | not needed — API Gateway is public |
| Testing - Backend | Pytest | same |
| Testing - Frontend | Vitest + React Testing Library | same |
| Testing - E2E | Playwright | same |
| Package management | Poetry (Python), npm/pnpm (JS) | same |
| IaC | — | Terraform >= 1.5, AWS provider ~> 5.0 (written, applied only if time allows) |
| CI/CD | — | GitHub Actions (stretch) |
| Observability | Local logging | CloudWatch Logs (stretch) |

## Repository Structure

```
packages/
  admin-ui/                      React SPA — admin dashboard
    src/
      components/
        AssignmentForm.tsx       Create new assignment form
        AssignmentList.tsx       List view with filters
        AssignmentCard.tsx       Individual assignment display
        TechnicianSelect.tsx     Dropdown for technician selection
        StatusBadge.tsx          Color-coded status indicator
      pages/
        Dashboard.tsx            Main dashboard view
        CreateAssignment.tsx     Assignment creation page
        AssignmentDetails.tsx    Detailed assignment view
      hooks/
        useAssignments.ts        React Query hooks for assignments
        useRealTimeUpdates.ts    SSE connection for live updates
      api/
        client.ts                API client with fetch/axios
      App.tsx
      main.tsx
    package.json
    vite.config.ts
    tailwind.config.js
    
  api/                           Python service — API + AI core
    app/
      main.py                    FastAPI app (entrypoint for local + Lambda)
      lambda_handler.py          Mangum adapter — unused until/unless deployed
      routers/
        webhook.py               POST /webhook — Telegram entrypoint
        assignments.py           Assignment REST API (NEW)
        auth.py                  Authentication endpoints (NEW)
      services/
        session_service.py       Assignments + per-technician conversation state
        extraction_service.py    LLM prompt + schema-constrained extraction
        telegram_client.py       Telegram Bot API wrapper
        sse_manager.py           Server-Sent Events manager (NEW)
      models/
        intake.py                IntakeRecord Pydantic schema
        assignment.py            Assignment and UserProfile models (NEW)
        telegram.py              Telegram webhook payload models
    tests/                       Pytest tests
      test_webhook.py
      test_assignments.py        Assignment API tests (NEW)
      test_session_service.py
      test_extraction_service.py
    pyproject.toml               Poetry config / dependencies
    
infra/stacks/dev/                Terraform for target cloud deployment (written;
                                  applied only if time allows) — not required to
                                  run the demo
.github/
  workflows/                     CI/CD (stretch — not required to run the demo)
  copilot-instructions.md        Project guidelines and workflows
docs/
  project-overview.md            This file
  path-to-reactive-flow.md       Migration plan and architecture details (NEW)
  testing-guidelines.md
  workflow-patterns.md
```

## Key Design Decisions

1. **Admin-initiated assignment workflow** — Work assignments are created by admins through a web UI, not self-initiated by technicians. This reflects real-world field service operations where supervisors dispatch work.

2. **Dual interface (web + chat)** — Admins use a modern web dashboard with real-time updates; field technicians use Telegram for mobile-friendly, async communication. Each interface is optimized for its user's context.

3. **Pre-registered technicians with phone verification** — Technicians are registered in advance with their Telegram chat_id, name, and phone number (associated with their Telegram account). This eliminates the need to extract employee names from conversations and provides a verification mechanism. The intake form only collects service-specific data: location, service_type, outcome, and notes.

4. **Real-time status visibility** — Admins see assignment status updates in real-time via Server-Sent Events (SSE), providing operational visibility without polling or page refreshes.

4. **Local-first demo, cloud-shaped code** — The app runs entirely on a laptop for the demo (FastAPI + Vite dev servers + `ngrok`), but is structured so it could be deployed to AWS with configuration changes, not a rewrite.

5. **Storage and notification behind interfaces** — Services are abstracted so SQLite → DynamoDB and SSE → SNS/SQS are swap-in implementations, not redesigns.

6. **AI core is reusable, schema is domain-specific** — `extraction_service.py` is domain-agnostic; only the Pydantic schema in `models/intake.py` changes per use case.

7. **Human-in-the-loop by design** — The system never infers missing or ambiguous fields; it re-prompts the technician directly, bounded to a small number of follow-up rounds, before persisting anything.

8. **Assignment-driven sessions** — Conversation state is linked to assignments, not free-form chats. Technicians without active assignments are prompted to wait, preventing orphaned intake records.

9. **Status state machine** — Assignments follow a clear state flow: `pending → assigned → in_progress → completed`, with status updates triggering notifications and dashboard updates.

10. **IaC written, not necessarily applied** — Terraform for the target AWS deployment is authored as documentation of the intended architecture; applying it is a stretch goal, not a demo dependency.

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+ and npm/pnpm
- Poetry (Python package manager)
- A Telegram bot token (via [@BotFather](https://t.me/BotFather))
- An LLM API key (Anthropic or OpenAI)
- `ngrok` or equivalent for exposing the local webhook

### Installation

```bash
git clone <repo-url>
cd capstone

# Backend setup
cd packages/api
poetry install
cp .env.example .env           # TELEGRAM_BOT_TOKEN, LLM_API_KEY

# Frontend setup
cd ../admin-ui
npm install                    # or: pnpm install
cp .env.example .env.local     # VITE_API_URL=http://localhost:4000
```

### Development Workflow

**Terminal 1 — Backend API:**
```bash
cd packages/api
poetry run uvicorn app.main:app --reload --port 4000
```

**Terminal 2 — Admin UI:**
```bash
cd packages/admin-ui
npm run dev                    # Starts Vite dev server on :5173
```

**Terminal 3 — ngrok tunnel (for Telegram webhook):**
```bash
ngrok http 4000
```

**Terminal 4 — Register webhook:**
```bash
curl -F "url=https://<ngrok-id>.ngrok.io/webhook" \
  https://api.telegram.org/bot<TOKEN>/setWebhook
```

**Usage:**
1. Open browser to `http://localhost:5173` (admin UI)
2. Create assignment: title, description, select technician
3. Technician receives Telegram notification
4. Technician responds via Telegram with service report
5. Watch real-time status updates in admin dashboard
6. See completed intake record when technician finishes

### Running Tests

**Backend tests:**
```bash
cd packages/api
poetry run pytest                          # All tests
poetry run pytest --cov                    # With coverage
poetry run pytest tests/test_assignments.py  # Specific file
```

**Frontend tests:**
```bash
cd packages/admin-ui
npm test                                   # Vitest unit tests
npm run test:e2e                          # Playwright E2E tests
```

### Cloud Deployment (stretch goal, if time allows)

1. **Build frontend for production:**
   ```bash
   cd packages/admin-ui
   npm run build                  # Creates dist/ with optimized static files
   ```

2. **Review/finish Terraform** in `infra/stacks/dev` — provisions:
   - S3 bucket + CloudFront for SPA hosting
   - Lambda for FastAPI backend
   - API Gateway for REST API + webhooks
   - DynamoDB for data storage
   - SNS/SQS for notifications and real-time updates
   - CloudWatch Logs for observability
   - IAM roles/policies for least-privilege access

3. **Swap implementations** for cloud services:
   - `storage_client.py`: SQLite → DynamoDB
   - `sse_manager.py`: In-memory SSE → SNS/SQS + WebSocket API Gateway
   - Static file serving: Vite dev server → S3 + CloudFront

4. **Provision infrastructure:**
   ```bash
   cd infra/stacks/dev
   terraform init
   terraform apply
   ```

5. **Deploy application:**
   ```bash
   # Upload SPA to S3
   aws s3 sync packages/admin-ui/dist s3://<bucket-name>/ --delete
   
   # Update CloudFront distribution
   aws cloudfront create-invalidation --distribution-id <dist-id> --paths "/*"
   
   # Package Lambda and update function
   # (FastAPI app with Mangum adapter)
   ```

6. **Update Telegram webhook** to point to deployed API Gateway URL

7. **When done demoing**, tear down to stay within free-tier limits:
   ```bash
   terraform destroy
   ```
