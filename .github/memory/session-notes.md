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

---

## 2026-08-03 (Evening) - Development Step Planning System

**Focus**: Create comprehensive step-by-step development workflow using copilot-customization agent

**Accomplishments**:
- Created Step 2-1: Assignment API with DynamoDB Persistence (Issue #11)
  - Models: Assignment and Technician Pydantic schemas
  - Repository: AssignmentRepository with SQLite implementation
  - API: POST /api/assignments, GET /api/assignments, GET /api/assignments/{id}
  - Integration with Swagger UI at /docs
- Created Step 2-2: Telegram Assignment Notifications (Issue #13)
  - Extends TelegramClient with send_assignment_notification()
  - Integrates notifications with Assignment API
  - Non-blocking notification pattern (failures don't prevent assignment creation)
  - Manual verification workflow via ngrok
- Enhanced memory management workflow
  - Added memory update as required step in create-next-step prompt
  - Added memory management section to tdd-developer agent
  - Memory updates now part of success criteria

**Key Decisions**:
- Use Repository pattern with SQLite for local demo, designed for DynamoDB swap
- Non-blocking notifications: log failures but don't prevent assignment creation
- Use dependency injection for TelegramClient to enable testing
- Follow TDD RED-GREEN-REFACTOR cycle for all new features
- Manual verification with ngrok after automated tests pass
- Memory updates are REQUIRED, not optional, after each step completion

**Patterns Applied**:
- **Step Template System**: Comprehensive GitHub Issue template with Goal, Background, Activities, Success Criteria, Key Workflow Patterns
- **Memory-First Workflow**: Update session notes and patterns after each step completion
- **Agent Mode Selection**: Use @tdd-developer for implementation, copilot-customization for planning
- **Non-Blocking External Services**: External service failures (Telegram API) don't prevent core operations (assignment creation)

**What's Next**:
- Step 2-3: Integrate webhook to handle technician responses to assignments
- Implementation of Steps 2-1 and 2-2 using @tdd-developer agent
- Memory updates after each step completion documented in template

---

## 2026-08-03 (Evening) - Step 2-2: Telegram Assignment Notifications Complete

**Focus**: Implement Telegram notifications when admins create assignments

**Accomplishments**:
- Extended TelegramClient service with `send_assignment_notification()` method
  - Added formatted message with priority emoji indicators (🔴 urgent, 🟠 high, 🟡 medium, 🟢 low)
  - Implemented `_format_assignment_message()` helper for Markdown formatting
  - Comprehensive error handling (returns True/False)
- Integrated notifications with Assignment API
  - Added TelegramClient dependency injection via `get_telegram_client()`
  - Modified `POST /api/assignments` to send notification after creation
  - Implemented non-blocking pattern: notification failures logged but don't prevent assignment creation
- Test coverage: 102 total tests passing (added 11 new tests)
  - 7 unit tests for TelegramClient notification method
  - 4 integration tests for API notification flow
  - All tests follow TDD RED-GREEN-REFACTOR cycle
- All existing tests continue to pass

**Key Decisions**:
- **Non-Blocking Notifications**: Assignment creation succeeds even if Telegram API fails
  - Rationale: Database is source of truth, notifications are best-effort delivery
  - Implementation: Try/except block with error logging
- **Priority Emojis**: Visual indicators for assignment urgency in Telegram
  - 🔴 Urgent, 🟠 High, 🟡 Medium, 🟢 Low
  - Makes priority immediately visible to technicians
- **Dependency Injection**: TelegramClient injected via FastAPI `Depends()`
  - Enables easy mocking in tests
  - Supports different implementations (mock for tests, real for production)
- **Markdown Formatting**: Uses Telegram's Markdown support for bold text
  - `*New Assignment*`, `*Title:*`, etc.
  - Improves readability in chat interface

**Patterns Applied**:
- TDD RED-GREEN-REFACTOR: All features developed test-first
- Non-blocking external service integration
- Dependency injection for testability
- Graceful degradation (system works even when Telegram API unavailable)

**Technical Details**:
- Files modified:
  - `app/services/telegram_client.py` - Added notification method
  - `app/routers/assignment.py` - Integrated TelegramClient
  - `tests/test_telegram_client.py` - New test file with 7 tests
  - `tests/test_assignment_api.py` - Added 4 integration tests
- Test results: 102 passed, 1 skipped, 1 warning
- Branch: `feature/telegram-notifications`

**What's Next**:
- Commit and push changes to feature branch
- Manual verification with ngrok and live Telegram bot (optional)
- Step 2-3: Integrate webhook to handle technician responses to assignments
  - Link incoming Telegram messages to existing assignments
  - Update assignment status when technician responds
  - Complete the admin-to-technician-to-admin feedback loop
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

## 2026-08-04 - Step 2-4: Enable DynamoDB Persistence for Assignment Workflow

**Focus**: Switch from in-memory FakeAssignmentRepository to production-ready DynamoDBAssignmentRepository with deployed AWS tables

**Accomplishments**:
- ✅ Deployed DynamoDB tables to AWS us-east-1 via Terraform
  - field-intake-assignments-dev with 2 GSIs (StatusIndex, TechnicianIndex)
  - field-intake-records-dev with 1 GSI (AssignmentIndex)
  - field-intake-technicians-dev
- ✅ Switched assignment.py to use DynamoDBAssignmentRepository in production
- ✅ Implemented lazy repository initialization to enable test mocking
- ✅ Added test fixture to automatically inject FakeAssignmentRepository in all tests
- ✅ All 96 tests passing (test isolation maintained with FakeAssignmentRepository)
- ✅ Manual verification: created assignment, restarted server, assignment persisted
- ✅ Direct DynamoDB verification via AWS CLI confirmed data persistence
- ✅ Zero lint errors, code quality maintained

**Key Decisions**:

1. **Lazy Initialization Pattern**:
   - Changed `_repository_instance = DynamoDBAssignmentRepository()` to `_repository_instance = None`
   - Initialization happens in `get_assignment_repo()` function
   - Prevents boto3 connection at module import time
   - Allows test fixtures to mock repository before initialization

2. **Test Isolation Strategy**:
   - Added `setup_test_repository` fixture (autouse=True)
   - Automatically injects FakeAssignmentRepository for all tests
   - Tests run fast without AWS dependencies
   - Production code uses real DynamoDB, tests use fake

3. **Region Configuration**:
   - Used us-east-1 (user preference over us-east-2)
   - Updated terraform.tfvars with correct region
   - AWS credentials via `aws configure export-credentials`

**Technical Implementation**:
- Modified `app/routers/assignment.py`: lazy repository initialization
- Modified `tests/conftest.py`: added repository mocking fixture
- Updated `infra/stacks/dev/terraform.tfvars`: set aws_region to us-east-1
- Deployed infrastructure: `terraform init && terraform apply -auto-approve`

**Testing Results**:
- Unit/Integration tests: 96 passed, 1 skipped (all using FakeAssignmentRepository)
- Manual persistence test: Assignment survived server restart ✅
- AWS DynamoDB verification: Direct query confirmed data in table ✅

**What's Next**:
- Step 2-3 is actually already complete (webhook-assignment integration)
- Consider adding intake record persistence to DynamoDB (currently in-memory)
- Consider Phase 4: React SPA with real-time updates (stretch goal)

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

---

## 2026-08-04 - Step 2-3: Webhook-Assignment Integration Complete

**Focus**: Integrate webhook handler with assignment workflow (TDD approach)

**Context**: 
- Step 2-1 provided assignment API
- Step 2-2 provided Telegram notifications  
- Step 2-3 links technician Telegram responses to their active assignments

**TDD Workflow Applied**:

1. **RED Phase** - Wrote 5 failing tests first:
   - `test_webhook_links_session_to_active_assignment`
   - `test_webhook_updates_assignment_status_to_in_progress`
   - `test_webhook_links_completed_intake_to_assignment`
   - `test_webhook_works_without_assignment` (backwards compatibility)
   - `test_webhook_handles_multiple_assignments_correctly`

2. **GREEN Phase** - Implemented minimal code to pass tests:
   - Added `assignment_id` field to IntakeRecord model
   - Added `get_active_assignment_for_technician()` to repository interface
   - Added `complete_assignment()` to repository interface
   - Updated webhook handler to link sessions to active assignments
   - Updated webhook to transition assignment status (assigned → in_progress → completed)
   - Implemented methods in both FakeAssignmentRepository and DynamoDBAssignmentRepository

3. **REFACTOR Phase** - Code already clean, no refactoring needed

**Implementation Details**:

**IntakeRecord Model Change**:
```python
class IntakeRecord:
    assignment_id: str | None = Field(default=None)  # NEW: Link to assignment
    location: str | None
    service_type: str | None
    outcome: str | None
    notes: str | None
    timestamp: datetime | None
```

**New Repository Methods**:
```python
# Find active assignment for technician
def get_active_assignment_for_technician(chat_id: int) -> Assignment | None
    # Returns most recent assignment with status in (pending, assigned, in_progress)
    
# Complete assignment with intake record link
def complete_assignment(assignment_id: str, intake_record_id: str) -> Assignment | None
    # Sets status="completed", intake_record_id, and completed_at timestamp
```

**Webhook Handler Logic** (Step 2-3 additions):
1. After creating/retrieving session, check for active assignment
2. If found, link intake_record.assignment_id to assignment
3. Update assignment status to "in_progress" if currently "pending" or "assigned"
4. When intake complete, call `complete_assignment()` to mark done

**Test Results**:
- All 5 new assignment integration tests: ✅ PASS
- All 21 webhook tests: ✅ PASS  
- Full test suite (96 tests): ✅ PASS (1 skipped as expected)
- No errors or warnings

**Key Patterns Discovered**:

1. **TDD Test-First Discipline**:
   - Write test → Watch fail (RED) → Implement → Watch pass (GREEN) → Refactor
   - All 5 tests written BEFORE any implementation code
   - Verified tests failed for the right reasons

2. **Dependency Injection in Webhook Router**:
   - Module-level variables for testability
   - `init_dependencies()` function called from main.py
   - Easy to mock in tests via monkeypatch

3. **Repository Method Naming**:
   - `get_active_assignment_for_technician()` - explicit query intent
   - `complete_assignment()` - semantic action (not just "update")
   - Better than generic CRUD for domain logic

4. **Backwards Compatibility**:
   - Webhook works without assignment_repository (graceful degradation)
   - IntakeRecord.assignment_id is optional
   - Existing sessions unaffected

**Accomplishments**:
- ✅ IntakeRecord model extended with assignment_id field
- ✅ Repository can find active assignments by technician
- ✅ Webhook links technician sessions to assignments automatically
- ✅ Assignment status transitions: pending → in_progress → completed
- ✅ Completed intake records update assignment with intake_record_id
- ✅ 100% test coverage for new functionality
- ✅ No regressions - all existing tests still pass

**Decisions**:
- Used "most recent assignment" logic when multiple active assignments exist
- Generated temporary intake_record_id (will be replaced with DB persistence in future)
- Kept assignment linking optional (backwards compatible with technicians who don't have assignments)

**Next Steps**:
- Commit Step 2-3 work to Git
- Update GitHub issue to mark Step 2-3 complete
- Step 2-4: End-to-end integration testing with Swagger + Telegram
- Manual testing: Create assignment → Receive notification → Respond via Telegram → Verify status updates

**Branch**: `feature/llm-extraction-service` (continuing from Step 2-2)
