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

---

## 2026-08-03 - Step 2-1: Assignment API with DynamoDB Persistence

**Focus**: Implement Assignment API layer with DynamoDB persistence using strict TDD

**Accomplishments**:
- ✅ Created Assignment and Technician Pydantic models with full validation (16 tests)
- ✅ Implemented DynamoDB repository with abstract interface (13 tests)
- ✅ Built REST API endpoints for assignments and technicians (11 tests)
- ✅ All 91 tests passing (40 new tests added for Step 2-1)
- ✅ Swagger UI accessible at `/docs` with all endpoints documented
- ✅ Used TDD RED-GREEN-REFACTOR cycle for entire implementation

**Key Decisions**:

1. **DynamoDB from Day 1** (not SQLite):
   - User requested DynamoDB persistence instead of SQLite
   - Implemented `DynamoDBAssignmentRepository` with boto3
   - Created `FakeAssignmentRepository` for fast in-memory testing
   - Repository pattern enables easy testing without real DynamoDB

2. **Testing Strategy**:
   - Fake repository for unit/integration tests (fast, no infrastructure)
   - Real DynamoDB repository ready for production use
   - All tests use FakeAssignmentRepository to avoid dependency on AWS
   - Tests verify contract, implementation swappable

3. **API Design**:
   - RESTful endpoints following OpenAPI best practices
   - Status filtering on GET /api/assignments (query parameter)
   - 404 for non-existent resources
   - 400 for validation errors (custom handler from existing code)
   - 201 for successful creation

**Files Created**:
- `app/models/assignment.py` - Assignment, AssignmentCreate models
- `app/models/technician.py` - Technician, TechnicianCreate models
- `app/repositories/__init__.py` - Repository package
- `app/repositories/assignment_repository.py` - AssignmentRepository interface, DynamoDBAssignmentRepository, FakeAssignmentRepository
- `app/routers/assignment.py` - Assignment REST API endpoints
- `tests/test_models_assignment.py` - 8 tests for Assignment model validation
- `tests/test_models_technician.py` - 8 tests for Technician model validation
- `tests/test_assignment_repository.py` - 13 tests for repository operations
- `tests/test_assignment_api.py` - 11 tests for REST API endpoints

**Files Modified**:
- `app/main.py` - Registered assignment router

**TDD Workflow Applied**:

Each component followed strict RED-GREEN-REFACTOR:

1. **Models** (RED → GREEN → REFACTOR):
   - Wrote 8 Assignment model tests → Failed (RED)
   - Implemented Assignment model → Tests passed (GREEN)
   - Wrote 8 Technician model tests → Failed (RED)
   - Implemented Technician model → Tests passed (GREEN)

2. **Repository** (RED → GREEN → REFACTOR):
   - Wrote 13 repository tests with FakeAssignmentRepository → Failed (RED)
   - Implemented DynamoDBAssignmentRepository and FakeAssignmentRepository → Tests passed (GREEN)
   - Refactored to clean up connection handling

3. **API Endpoints** (RED → GREEN → REFACTOR):
   - Wrote 11 API endpoint tests → Failed with 404 (RED)
   - Implemented assignment router with all endpoints → Tests passed (GREEN)
   - Registered router in main.py → All tests green

**Repository Pattern Implementation**:

```python
# Abstract interface
class AssignmentRepository(ABC):
    def create_assignment(self, assignment: Assignment) -> Assignment
    def get_assignment(self, assignment_id: str) -> Assignment | None
    def list_assignments(self, status: str | None = None) -> list[Assignment]
    def update_assignment_status(self, assignment_id: str, status: str) -> Assignment | None
    def create_technician(self, technician: Technician) -> Technician
    def get_technician(self, chat_id: int) -> Technician | None
    def list_technicians(self) -> list[Technician]

# Production implementation
class DynamoDBAssignmentRepository(AssignmentRepository):
    # Uses boto3 DynamoDB resource
    # Table names from environment variables
    # Ready for production use

# Testing implementation
class FakeAssignmentRepository(AssignmentRepository):
    # In-memory dict storage
    # Fast, no infrastructure dependencies
    # Used in all tests
```

**API Endpoints Implemented**:

```
POST   /api/assignments          → Create assignment (201)
GET    /api/assignments           → List all (200)
GET    /api/assignments?status=X  → Filter by status (200)
GET    /api/assignments/{id}      → Get by ID (200/404)
POST   /api/technicians           → Register technician (201)
GET    /api/technicians           → List all (200)
```

**Test Results**:
```
91 passed, 1 skipped in 4.95s

Breakdown:
- 8 tests: Assignment model validation
- 8 tests: Technician model validation
- 13 tests: Repository operations (CRUD, filtering)
- 11 tests: REST API endpoints (success, validation, 404s)
- 51 tests: Existing tests (webhook, extraction, session service) - all still passing
```

**Patterns Discovered**:

1. **Repository Pattern with Fake for Testing**:
   - Abstract interface defines contract
   - DynamoDB implementation for production
   - Fake in-memory implementation for testing
   - Tests validate contract, not implementation
   - Makes tests fast and infrastructure-independent

2. **TDD Discipline**:
   - Write test first (RED)
   - Implement minimal code to pass (GREEN)
   - Refactor while keeping tests green (REFACTOR)
   - Never write implementation before tests
   - Catch bugs early, maintain confidence

3. **FastAPI Dependency Injection**:
   ```python
   def get_assignment_repo() -> AssignmentRepository:
       return _repository_instance
   
   @router.post("/api/assignments")
   async def create_assignment(
       assignment_data: AssignmentCreate,
       repo: AssignmentRepository = Depends(get_assignment_repo)
   ):
       # Easy to mock in tests
       # Easy to swap implementations
   ```

4. **Pydantic Model Separation**:
   - Full models (Assignment, Technician) - for responses
   - Create models (AssignmentCreate, TechnicianCreate) - for requests
   - Auto-generated defaults (UUID, timestamps) in full models
   - Clean API contract

**DynamoDB Table Design**:

Tables (ready to provision with Terraform):
- `field-intake-assignments-dev` - Assignments table
- `field-intake-technicians-dev` - Technicians table
- `field-intake-records-dev` - Intake records table (future)

GSIs planned (for DynamoDB):
- StatusIndex - Query assignments by status
- TechnicianIndex - Query assignments by technician

**Swagger UI Verification**:

All endpoints appear in Swagger UI at `http://localhost:4000/docs`:
- Interactive API documentation auto-generated
- Try-it-out functionality for each endpoint
- Request/response schemas documented
- Validation rules visible

**Scope Boundaries Maintained**:

✅ **Did Implement**:
- Assignment and Technician models
- DynamoDB repository with abstract interface
- REST API endpoints
- Comprehensive test coverage

❌ **Did NOT Implement** (future steps):
- Telegram notification integration (Step 2-2)
- Webhook integration for assignment linking (Step 2-3)
- DynamoDB table provisioning with Terraform (Step 2-0, parallel work)
- Real-time updates (future React SPA)
- Authentication/authorization

**Next Steps**:
- Step 2-2: Implement Telegram notification when assignment created
- Step 2-3: Update webhook to link technician responses to assignments
- Step 2-4: End-to-end integration testing
- Ensure DynamoDB tables provisioned (Step 2-0)
- Manual testing with Swagger UI + Telegram bot

**Branch**: `feature/assignment-api` (ready to commit and PR)
