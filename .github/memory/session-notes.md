# Session Notes

Development session history for the Field Intake Service.

---

## 2026-08-02 - Project Scaffold Creation

**Focus**: Initialize golden-path project template from project overview

**Accomplishments**:
- Created repository structure with `packages/api`, `docs/`, `context/`, `infra/`, `.github/workflows/`
- Generated documentation placeholders adapted for Python/FastAPI/Telegram stack
- Created Terraform placeholders for AWS serverless target (Lambda, API Gateway, DynamoDB, SNS)
- Generated GitHub Actions workflow placeholders for CI/CD
- Adapted testing guidelines to Pytest/FastAPI TestClient patterns
- Adapted copilot-instructions.md for Field Intake Service stack
- Established memory system for tracking development patterns

**Decisions**:
- Use `packages/api` for single API service (no frontend)
- Use Poetry for Python package management
- Target AWS serverless architecture (documented, applied only if time allows)
- Use SQLite for local demo, design for DynamoDB swap-in
- Use Telegram manager chat for local notifications, design for SNS swap-in

**Next Steps**:
- Implement FastAPI webhook endpoint (`POST /webhook`)
- Create Pydantic intake record schema
- Implement LLM extraction service
- Add SQLite storage implementation
- Write Pytest tests for each component

---

## 2026-08-03 - Admin-Initiated Assignment Architecture

**Focus**: Design admin-initiated assignment workflow with Swagger UI + DynamoDB

**Context**:
- User requested shift from technician-initiated (reactive) to admin-initiated (proactive) workflow
- Goal: Admin assigns work via web interface, technician responds via Telegram
- Requirement: Admin sees real-time status updates

**Architecture Decisions**:

1. **Frontend Strategy - API-First with Swagger UI**:
   - **MVP**: Swagger UI at `/docs` endpoint (zero additional code)
   - **Rationale**: Validate backend workflow first, iterate quickly
   - **Stretch Goal**: React SPA with SSE real-time updates (Phase 4)
   - **Benefit**: All APIs proven before investing in frontend

2. **Storage Strategy - DynamoDB from Day 1**:
   - **Decision**: Skip SQLite entirely, go straight to DynamoDB
   - **Provisioning**: Terraform module for 3 tables (assignments, technicians, intake_records)
   - **Rationale**: Avoid migration later, practice cloud-native patterns
   - **GSIs**: StatusIndex for filtering, TechnicianIndex for lookups

3. **Authentication Strategy - Deferred**:
   - **MVP**: No authentication - Swagger UI is open
   - **Rationale**: Don't block workflow validation with auth complexity
   - **Future**: JWT or AWS Cognito when moving to production

4. **Real-time Updates - Deferred**:
   - **MVP**: Manual polling/refresh in Swagger UI
   - **Future**: Server-Sent Events (SSE) in React SPA

**Data Model Changes**:

```python
# New models (simplified for MVP)
class Assignment:
    assignment_id: str (UUID)
    technician_chat_id: int
    technician_name: str
    title: str
    description: str
    priority: str  # low, medium, high, urgent
    status: str  # pending, assigned, in_progress, completed
    created_at, assigned_at, completed_at: datetime
    intake_record_id: str (nullable)

class Technician:
    chat_id: int (PK)
    name: str
    registered_at: datetime

# Updated IntakeRecord
class IntakeRecord:
    # ... existing fields ...
    assignment_id: str (nullable)  # Link to assignment
```

**API Endpoints** (all exposed in Swagger UI):
- `POST /api/assignments` - Create assignment, notify technician via Telegram
- `GET /api/assignments` - List all assignments (with optional status filter)
- `GET /api/assignments/{id}` - Get assignment details + linked intake record
- `POST /api/technicians` - Register technician (get chat_id from Telegram first)
- `GET /api/technicians` - List registered technicians

**Workflow**:
1. Admin opens Swagger UI (`http://localhost:4000/docs`)
2. Admin registers technician via POST `/api/technicians` (using their Telegram chat_id)
3. Admin creates assignment via POST `/api/assignments`
4. System sends Telegram notification to technician immediately
5. Technician responds via Telegram (existing LLM extraction flow preserved 100%)
6. Assignment status updates in DynamoDB (in_progress → completed)
7. Admin polls GET `/api/assignments/{id}` to check status and view intake record

**Preserved Components**:
- All existing LLM extraction logic unchanged
- All existing validation logic unchanged
- All existing follow-up question logic unchanged
- Changes are purely orchestration layers

**Documentation Created**:
- `docs/path-to-reactive-flow.md` - Complete migration plan with:
  - Current vs target flow comparison
  - Data model changes
  - Terraform DynamoDB module structure
  - Implementation phases (4 phases, 5 days)
  - Practical usage guide for Swagger UI
  - Testing strategy
  - Migration path to React SPA
- `docs/project-overview.md` - Updated:
  - Project description (admin-initiated system)
  - Architecture diagrams (Swagger + DynamoDB)
  - Tech stack (added boto3, DynamoDB)
  - Repository structure (new files/modules)
  - Development workflow (Terraform provisioning)

**Implementation Plan**:
- **Phase 1 (Day 1)**: Terraform DynamoDB module + provision tables
- **Phase 2 (Days 2-3)**: Assignment API + DynamoDB integration + webhook updates
- **Phase 3 (Days 4-5)**: End-to-end testing with Swagger UI + integration tests
- **Phase 4 (Stretch)**: React SPA with real-time SSE updates (if time permits)

**Files to Create**:
- `app/models/assignment.py` - Assignment and Technician models
- `app/routers/assignments.py` - Assignment REST API
- `app/services/dynamodb_client.py` - DynamoDB wrapper
- `infra/modules/dynamodb/main.tf` - Table definitions
- `infra/modules/dynamodb/outputs.tf` - Table names/ARNs
- `infra/modules/dynamodb/variables.tf` - Environment config
- `tests/test_assignments.py` - Assignment API tests

**Files to Modify**:
- `app/models/intake.py` - Add assignment_id field
- `app/services/session_service.py` - Add DynamoDB client + assignment methods
- `app/routers/webhook.py` - Add assignment linking logic
- `app/main.py` - Register assignments router, initialize DynamoDB
- `infra/stacks/dev/main.tf` - Include DynamoDB module
- `pyproject.toml` - Add boto3 dependency

**Testing Strategy**:
- Unit tests for DynamoDB client operations
- Integration tests for assignment creation → Telegram notification
- Integration tests for technician response → assignment linking
- End-to-end test: full assignment workflow from creation to completion
- Optional: DynamoDB Local for isolated testing

**Success Criteria (MVP)**:
- ✅ DynamoDB tables provisioned via Terraform
- ✅ Assignment creation via Swagger UI works
- ✅ Telegram notification sent immediately
- ✅ Technician response links to assignment
- ✅ LLM extraction works (existing logic preserved)
- ✅ Assignment status updates in DynamoDB
- ✅ Completed intake record persisted with assignment link
- ✅ All tests pass

**Next Steps**:
1. Create Terraform DynamoDB module structure
2. Define DynamoDB table resources with GSIs
3. Implement Assignment and Technician Pydantic models
4. Create DynamoDBClient service wrapper
5. Implement POST /api/assignments endpoint
6. Update webhook to link sessions to assignments
7. Test end-to-end with Swagger UI
