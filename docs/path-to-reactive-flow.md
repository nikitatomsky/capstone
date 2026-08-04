# Path to Admin-Initiated Assignment Flow

## Current Application Flow

**How it works now:**
1. Field technician sends a message to the bot
2. System extracts structured data from the message using LLM
3. Bot asks follow-up questions for missing required fields
4. When complete, bot confirms and (TODO) persists the record
5. (TODO) Manager notification

**Key components:**
- Sessions tracked by `chat_id` only
- No concept of assignments or user roles
- Reactive flow (technician initiates)
- Single intake record per session

## Target Application Flow (MVP with Swagger UI)

**Admin-initiated workflow via API (Swagger UI):**
1. Admin opens Swagger UI at `/docs` endpoint
2. Admin creates new assignment via POST `/api/assignments` (title, description, priority, technician_chat_id)
3. System sends assignment notification to technician via Telegram
4. Technician receives assignment and responds with service report
5. LLM extracts structured data and asks follow-up questions for missing fields
6. Admin polls GET `/api/assignments` or GET `/api/assignments/{id}` to check status
7. When complete, assignment status shows "completed" with full intake record
8. All data persisted in DynamoDB (provisioned via Terraform)

**Future Enhancement (Stretch Goal):**
- React SPA with real-time SSE updates for better UX
- Deployed to S3 + CloudFront

## Required Adjustments

### 1. Data Model Changes

**New Models Needed:**

```python
# app/models/assignment.py
class Assignment(BaseModel):
    assignment_id: str  # UUID
    technician_chat_id: int  # Assigned technician's Telegram chat_id
    technician_name: str  # Display name for technician
    title: str
    description: str
    priority: str  # low, medium, high, urgent
    status: str  # pending, assigned, in_progress, completed, cancelled
    created_at: datetime
    assigned_at: datetime | None
    completed_at: datetime | None
    intake_record_id: str | None  # Link to completed intake record
    
class Technician(BaseModel):
    """Technician registration with phone number from Telegram"""
    chat_id: int  # Telegram chat_id (primary key)
    name: str
    phone_number: str  # Phone number associated with Telegram account
    registered_at: datetime
```

**Update IntakeRecord:**
```python
class IntakeRecord(BaseModel):
    # REMOVED: employee_name (known from assignment)
    location: str | None
    service_type: str | None
    outcome: str | None
    notes: str | None
    timestamp: datetime | None
    assignment_id: str | None  # Link to assignment
    
    # Required fields (employee_name removed):
    # - location
    # - service_type  
    # - outcome
```

### 2. Session Service Updates

**Current:** Sessions keyed by `chat_id` only

**Needed:**
```python
class SessionService:
    def __init__(self, dynamodb_client):
        self._sessions: dict[int, dict]  # existing in-memory sessions
        self._dynamodb = dynamodb_client  # NEW: DynamoDB connection
    
    def create_assignment(
        self, 
        technician_chat_id: int,
        technician_name: str,
        title: str,
        description: str,
        priority: str
    ) -> Assignment:
        """Create assignment and persist to DynamoDB"""
        
    def link_session_to_assignment(
        self, 
        chat_id: int, 
        assignment_id: str
    ) -> None:
        """Link technician's session to assignment"""
        
    def get_assignment_by_id(
        self, 
        assignment_id: str
    ) -> Assignment | None:
        """Retrieve assignment from DynamoDB"""
        
    def update_assignment_status(
        self, 
        assignment_id: str,
        status: str
    ) -> None:
        """Update assignment status"""
        
    def complete_assignment(
        self, 
        assignment_id: str
    ) -> None:
        """Mark assignment as completed"""
        
    def list_assignments(
        self,
        admin_user_id: str | None = None,
        status: str | None = None
    ) -> list[Assignment]:
        """List assignments with optional filters"""
        
    def list_technicians(self) -> list[UserProfile]:
        """Get all registered technicians"""
```

### 3. Message Routing Logic

**Current:** All messages treated as technician reports

**Needed:** Route based on user role and message context

```python
# In webhook.py
async def webhook(update: TelegramUpdate):
    chat_id = update.message.chat.id
    message_text = update.message.text
    
    # NEW: Check if technician is registered
    user_profile = session_service.get_user_by_chat_id(chat_id)
    
    if not user_profile:
        await telegram_client.send_message(
            chat_id,
            "Please register first. Contact your administrator."
        )
        return
    
    # Get or create session
    session = session_service.get_or_create_session(chat_id)
    
    # Check if technician has active assignment
    assignment_id = session.get("assignment_id")
    
    if not assignment_id:
        # Check for new assignment
        pending_assignment = session_service.get_pending_assignment(chat_id)
        if pending_assignment:
            session_service.link_session_to_assignment(chat_id, pending_assignment.assignment_id)
            session_service.update_assignment_status(
                pending_assignment.assignment_id,
                "in_progress"
            )
            assignment_id = pending_assignment.assignment_id
        else:
            await telegram_client.send_message(
                chat_id,
                "No active assignment. Please wait for admin to assign work."
            )
            return
    
    # Existing extraction and validation flow...
    # [Current webhook logic here]
    
    # When complete:
    if not missing_fields:
        assignment = session_service.get_assignment_by_id(assignment_id)
        session_service.complete_assignment(assignment_id)
        
        # Notify via webhook/SSE to update admin dashboard
        await notify_dashboard_update(assignment_id, "completed")
```

### 4. Web API Endpoints (New)

**Admin Dashboard REST API:**

```python
# app/routers/assignments.py
@router.post("/api/assignments")
async def create_assignment(assignment: AssignmentCreate):
    """
    Create new assignment.
    
    Body:
    - technician_chat_id: int
    - technician_name: str
    - title: str
    - description: str
    - priority: str (low, medium, high, urgent)
    
    Returns: Assignment object with assignment_id
    """
    
@router.get("/api/assignments")
async def list_assignments(status: str | None = None):
    """
    List all assignments, optionally filtered by status.
    
    Query params:
    - status: pending, assigned, in_progress, completed, cancelled
    """
    
@router.get("/api/assignments/{assignment_id}")
async def get_assignment(assignment_id: str):
    """Get assignment details including linked intake record if completed."""
    
@router.get("/api/technicians")
async def list_technicians():
    """List all registered technicians for assignment dropdown."""
    
@router.post("/api/technicians")
async def register_technician(technician: TechnicianCreate):
    """
    Register new technician with phone number.
    
    Body:
    - chat_id: int (Telegram chat_id)
    - name: str
    - phone_number: str (phone number associated with Telegram account)
    
    Note: Get chat_id by having the technician message the bot first.
    The phone_number should match the phone number associated with their
    Telegram account for verification purposes.
    """
```

### 5. Frontend Implementation Options

#### Option A: Swagger UI (Recommended for MVP)

**Pros:**
- Already included with FastAPI - zero additional code
- Auto-generated from API schema with OpenAPI docs
- Perfect for API-first development and testing
- Fast iteration - focus on backend logic first
- Good for technical admins and demo validation
- Easy to test end-to-end workflow immediately

**Cons:**
- No real-time updates (requires manual refresh)
- Basic UX (not suitable for non-technical users long-term)
- Manual polling needed to check status changes

**Implementation:**
```python
# Already available at /docs endpoint - no additional code!
# FastAPI automatically generates interactive API documentation

from fastapi import FastAPI

app = FastAPI(
    title="Field Intake Assignment API",
    description="Admin API for managing field technician assignments",
    version="1.0.0"
)

# All endpoints automatically appear in Swagger UI at /docs
# Alternative ReDoc UI available at /redoc
```

**Usage Flow:**
1. Navigate to `http://localhost:4000/docs`
2. Use POST `/api/technicians` to register technician (get chat_id from Telegram)
3. Use POST `/api/assignments` to create and assign work
4. Technician receives Telegram notification
5. Use GET `/api/assignments/{id}` to check status and view completed intake
6. Use GET `/api/assignments?status=completed` to filter assignments

#### Option B: Lightweight SPA (Stretch Goal - Future Enhancement)

**Tech Stack:**
- **Frontend:** React + Vite (or Vue.js, Svelte)
- **Styling:** Tailwind CSS
- **State Management:** React Query / SWR for data fetching
- **Real-time:** EventSource (SSE) for live updates
- **Build:** Served as static files from FastAPI

**Project Structure:**
```
packages/
  admin-ui/              # NEW
    src/
      components/
        AssignmentForm.tsx
        AssignmentList.tsx
        AssignmentCard.tsx
        TechnicianSelect.tsx
        StatusBadge.tsx
      pages/
        Dashboard.tsx
        CreateAssignment.tsx
        AssignmentDetails.tsx
      hooks/
        useAssignments.ts
        useRealTimeUpdates.ts
      api/
        client.ts
      App.tsx
      main.tsx
    package.json
    vite.config.ts
    
  api/
    app/
      static/             # Built SPA files served here
```

**Key Features:**

1. **Dashboard View**
   - List all assignments with color-coded status
   - Filter by status (all, assigned, in-progress, completed)
   - Real-time status updates via SSE
   - Search and sort capabilities

2. **Create Assignment Form**
   - Title and description fields
   - Priority selector (low, medium, high, urgent)
   - Technician dropdown (from registered users)
   - Submit → immediately notifies technician via Telegram

3. **Assignment Status States**
   ```
   pending → assigned → in_progress → completed
     ⬜       🟡          🔵            🟢
   ```

4. **Real-time Updates**
   ```typescript
   // useRealTimeUpdates.ts
   useEffect(() => {
     const eventSource = new EventSource('/api/assignments/stream');
     
     eventSource.onmessage = (event) => {
       const update = JSON.parse(event.data);
       // Update local state with new assignment status
       queryClient.setQueryData(['assignments', update.assignment_id], update);
     };
     
     return () => eventSource.close();
   }, []);
   ```

5. **Assignment Card Component**
   ```tsx
   <AssignmentCard>
     <StatusBadge status={assignment.status} />
     <h3>{assignment.title}</h3>
     <p>{assignment.description}</p>
     <TechnicianInfo user={assignment.technician} />
     <Timeline>
       <Event>Created: {assignment.created_at}</Event>
       <Event>Assigned: {assignment.assigned_at}</Event>
       {assignment.completed_at && (
         <Event>Completed: {assignment.completed_at}</Event>
       )}
     </Timeline>
     <IntakeRecordPreview record={assignment.intake_record} />
   </AssignmentCard>
   ```

### 6. Authentication & Authorization (DEFERRED)

**Current approach:**
- No authentication for MVP
- Swagger UI is open for testing
- Suitable for local demo and development

**Future enhancement (when moving to production):**
- API key or JWT-based auth
- AWS Cognito integration
- Role-based access control (RBAC)

**Note:** Skip authentication until end-to-end workflow is validated with Swagger UI.

### 7. DynamoDB Storage with Terraform

**DynamoDB Tables to Provision:**

```hcl
# infra/modules/dynamodb/main.tf

# Assignments table
resource "aws_dynamodb_table" "assignments" {
  name           = "field-intake-assignments-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"  # On-demand pricing
  hash_key       = "assignment_id"

  attribute {
    name = "assignment_id"
    type = "S"  # String (UUID)
  }
  
  attribute {
    name = "status"
    type = "S"
  }
  
  attribute {
    name = "technician_chat_id"
    type = "N"  # Number
  }

  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "status"
    projection_type = "ALL"
  }
  
  global_secondary_index {
    name            = "TechnicianIndex"
    hash_key        = "technician_chat_id"
    projection_type = "ALL"
  }

  tags = {
    Environment = var.environment
    Project     = "field-intake-service"
  }
}

# Technicians table
resource "aws_dynamodb_table" "technicians" {
  name           = "field-intake-technicians-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "chat_id"

  attribute {
    name = "chat_id"
    type = "N"  # Telegram chat_id
  }

  tags = {
    Environment = var.environment
    Project     = "field-intake-service"
  }
}

# Intake records table
resource "aws_dynamodb_table" "intake_records" {
  name           = "field-intake-records-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "record_id"

  attribute {
    name = "record_id"
    type = "S"  # UUID
  }
  
  attribute {
    name = "assignment_id"
    type = "S"  # Foreign key to assignments
  }

  global_secondary_index {
    name            = "AssignmentIndex"
    hash_key        = "assignment_id"
    projection_type = "ALL"
  }

  tags = {
    Environment = var.environment
    Project     = "field-intake-service"
  }
}
```

**DynamoDB Item Schemas:**

```python
# assignments table item
{
    "assignment_id": "uuid" (PK),
    "technician_chat_id": int,
    "technician_name": str,
    "title": str,
    "description": str,
    "priority": str,
    "status": str,
    "created_at": "ISO timestamp",
    "assigned_at": "ISO timestamp",
    "completed_at": "ISO timestamp" (nullable),
    "intake_record_id": "uuid" (nullable)
}

# technicians table item
{
    "chat_id": int (PK),
    "name": str,
    "phone_number": str,  # Phone number associated with Telegram
    "registered_at": "ISO timestamp"
}

# intake_records table item
{
    "record_id": "uuid" (PK),
    "assignment_id": "uuid",  # Link to assignment (provides employee_name)
    "location": str,
    "service_type": str,
    "outcome": str,
    "notes": str (nullable),
    "timestamp": "ISO timestamp"
}
```

**Terraform Provisioning Commands:**

```bash
# Navigate to infra directory
cd infra/stacks/dev

# Initialize Terraform (downloads AWS provider)
terraform init

# Validate configuration
terraform validate

# Preview changes
terraform plan

# Provision DynamoDB tables
terraform apply

# When done testing, tear down resources
terraform destroy
```

**Python DynamoDB Client Integration:**

```python
# app/services/dynamodb_client.py
import boto3
from botocore.exceptions import ClientError

class DynamoDBClient:
    def __init__(self, region_name="us-east-1"):
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.assignments_table = self.dynamodb.Table('field-intake-assignments-dev')
        self.technicians_table = self.dynamodb.Table('field-intake-technicians-dev')
        self.intake_records_table = self.dynamodb.Table('field-intake-records-dev')
    
    def create_assignment(self, assignment: dict) -> bool:
        """Create new assignment in DynamoDB"""
        try:
            self.assignments_table.put_item(Item=assignment)
            return True
        except ClientError as e:
            logger.error(f"Error creating assignment: {e}")
            return False
    
    def get_assignment(self, assignment_id: str) -> dict | None:
        """Retrieve assignment by ID"""
        try:
            response = self.assignments_table.get_item(
                Key={'assignment_id': assignment_id}
            )
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting assignment: {e}")
            return None
    
    def list_assignments(self, status: str | None = None) -> list[dict]:
        """List assignments, optionally filtered by status"""
        try:
            if status:
                response = self.assignments_table.query(
                    IndexName='StatusIndex',
                    KeyConditionExpression='status = :status',
                    ExpressionAttributeValues={':status': status}
                )
            else:
                response = self.assignments_table.scan()
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error listing assignments: {e}")
            return []
```

### 8. Real-time Notification Flow (DEFERRED for MVP)

**Current MVP approach:**
- No real-time updates in Swagger UI
- Admin manually refreshes/polls GET endpoints to check status
- Simpler implementation - focus on core workflow first

**Future enhancement (React SPA):**
- Server-Sent Events (SSE) for real-time dashboard updates
- WebSocket API Gateway integration for cloud deployment
- Automatic status updates without polling

### 9. Testing Updates

**New test scenarios for MVP:**

```python
# tests/test_assignments.py
def test_create_assignment_via_api():
    """Test POST /api/assignments creates assignment and sends Telegram notification"""

def test_list_assignments_all():
    """Test GET /api/assignments returns all assignments"""

def test_list_assignments_filtered_by_status():
    """Test GET /api/assignments?status=completed filters correctly"""

def test_get_assignment_by_id():
    """Test GET /api/assignments/{id} returns assignment details"""

def test_register_technician():
    """Test POST /api/technicians creates technician record"""

def test_list_technicians():
    """Test GET /api/technicians returns all registered technicians"""

def test_assignment_persisted_to_dynamodb():
    """Test assignment is saved to DynamoDB"""

def test_assignment_status_updates_in_dynamodb():
    """Test assignment status changes are persisted"""

# tests/test_webhook.py (updated)
def test_technician_response_links_to_assignment():
    """Test technician webhook message links to existing assignment"""

def test_completed_intake_updates_assignment_status():
    """Test assignment status changes to 'completed' when intake is done"""

def test_completed_intake_persisted_with_assignment_link():
    """Test intake record saved to DynamoDB with assignment_id"""

# tests/integration/test_end_to_end.py
def test_full_assignment_workflow():
    """
    End-to-end test:
    1. Register technician
    2. Create assignment
    3. Simulate technician response
    4. Verify LLM extraction
    5. Verify assignment completion
    6. Verify DynamoDB persistence
    """
```

**Test execution:**
```bash
# Run all tests
poetry run pytest

# Run only assignment tests
poetry run pytest tests/test_assignments.py

# Run with DynamoDB local (optional)
docker run -p 8000:8000 amazon/dynamodb-local
export AWS_ENDPOINT_URL=http://localhost:8000
poetry run pytest
```

## Implementation Priority (Revised for MVP-First Approach)

### Phase 1: DynamoDB Infrastructure (Day 1)
1. ⬜ Create Terraform DynamoDB module
2. ⬜ Provision assignments, technicians, and intake_records tables
3. ⬜ Configure GSIs for status and technician lookups
4. ⬜ Test Terraform apply/destroy cycle
5. ⬜ Add boto3 DynamoDB client to FastAPI

### Phase 2: Backend API with DynamoDB (Days 2-3)
1. ⬜ Add Assignment and Technician models
2. ⬜ Create DynamoDBClient service wrapper
3. ⬜ Implement assignment REST API endpoints
4. ⬜ Update webhook to link technician responses to assignments
5. ⬜ Update IntakeRecord to include assignment_id
6. ⬜ Persist completed intake records to DynamoDB

### Phase 3: End-to-End Testing with Swagger (Days 4-5)
1. ⬜ Test technician registration via Swagger UI
2. ⬜ Test assignment creation via Swagger UI
3. ⬜ Verify Telegram notification delivery
4. ⬜ Test technician response via Telegram
5. ⬜ Verify LLM extraction and follow-up questions
6. ⬜ Verify assignment status updates in DynamoDB
7. ⬜ Test GET endpoints for assignment listing and details
8. ⬜ Write integration tests for full workflow

### Phase 4: React SPA (STRETCH GOAL - Future)
1. ⬜ Set up React + Vite project
2. ⬜ Create assignment form component
3. ⬜ Build dashboard with assignment list
4. ⬜ Implement real-time SSE updates
5. ⬜ Add authentication layer
6. ⬜ Deploy to S3 + CloudFront

## Key Files to Create/Modify

### New Files
1. `app/models/assignment.py` - Assignment and Technician models
2. `app/routers/assignments.py` - Assignment REST API
3. `app/services/dynamodb_client.py` - DynamoDB wrapper
4. `infra/modules/dynamodb/` - Terraform DynamoDB module
5. `infra/modules/dynamodb/main.tf` - Table definitions
6. `infra/modules/dynamodb/outputs.tf` - Table names and ARNs
7. `infra/modules/dynamodb/variables.tf` - Environment config

### Modified Files
1. `app/models/intake.py` - Add assignment_id field
2. `app/services/session_service.py` - Add DynamoDB client and assignment methods
3. `app/routers/webhook.py` - Add assignment linking logic
4. `app/main.py` - Register assignments router, initialize DynamoDB
5. `infra/stacks/dev/main.tf` - Include DynamoDB module
6. `tests/test_webhook.py` - Add assignment flow tests
7. `tests/test_assignments.py` - New test file for assignment API
8. `pyproject.toml` - Add boto3 dependency

## Architecture Diagram (Updated)

### MVP with Swagger UI + DynamoDB

```
┌─────────────────────────────────────────────────────────────┐
│  Admin (browser)                                            │
│  Swagger UI at /docs (localhost:4000/docs)                 │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP REST API
┌─────────────────────▼───────────────────────────────────────┐
│  FastAPI app (uvicorn, localhost:4000)                      │
│  Routes:                                                     │
│    POST /webhook               (Telegram bot webhook)       │
│    POST /api/assignments       (Create assignment)          │
│    GET  /api/assignments       (List assignments)           │
│    GET  /api/assignments/{id}  (Get assignment details)     │
│    POST /api/technicians       (Register technician)        │
│    GET  /api/technicians       (List technicians)           │
│  Services:                                                   │
│    session_service.py          (assignments + sessions)     │
│    extraction_service.py       (LLM extraction)             │
│    dynamodb_client.py          (DynamoDB operations)        │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────────┐
        ▼              ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐
│  DynamoDB    │ │  Telegram    │ │  ngrok tunnel        │
│  (AWS)       │ │  Bot API     │ │  (webhook exposure)  │
│  - assignments│ │  (notify tech)│ │                      │
│  - technicians│ │              │ │                      │
│  - intake_   │ │              │ │                      │
│    records   │ │              │ │                      │
└──────────────┘ └──────────────┘ └──────────────────────┘
                      │
                      ▼
           ┌────────────────────┐
           │ Field Technician   │
           │ (Telegram mobile)  │
           └────────────────────┘
```

### Target Cloud Architecture (Stretch)

```
Admin (browser) → CloudFront → S3 (static SPA files)
                      │
                      └─→ API Gateway → Lambda (FastAPI + Mangum)
                                            │
                    ┌───────────────────────┼─────────────────┐
                    ▼                       ▼                  ▼
                DynamoDB              Telegram Bot API      SNS/SQS
            (assignments, users,      (notify technicians)  (real-time
             intake_records)                                 updates)
```

## Decision: Frontend Approach

**Recommendation for MVP: Option A - Swagger UI**

**Rationale:**
- Zero additional code - focus on backend logic and DynamoDB integration
- Immediate testing capability - validate workflow end-to-end quickly
- API-first development - ensures clean REST contract
- Perfect for demo and technical validation
- Can iterate on backend without frontend coupling
- React SPA becomes natural next step once API is proven

**Migration Path:**
1. **Phase 1 (Current):** Swagger UI for testing and demo
2. **Phase 2 (Stretch):** React SPA for production-ready admin experience
3. Both can coexist - Swagger for debugging, React for daily use

## Next Steps

1. ✅ Review and approve MVP architecture (Swagger + DynamoDB)
2. ⬜ Provision DynamoDB tables via Terraform
3. ⬜ Implement assignment models and API endpoints
4. ⬜ Update webhook handler for assignment linking
5. ⬜ Test end-to-end with Swagger UI
6. ⬜ Validate Telegram notifications work correctly
7. ⬜ Verify DynamoDB persistence
8. ⬜ (Stretch) Begin React SPA if time permits

## Open Questions (Resolved)

1. **Authentication:** ✅ DEFERRED - Skip for MVP, add later
2. **Frontend:** ✅ Swagger UI for MVP, React SPA as stretch goal
3. **Storage:** ✅ DynamoDB (not SQLite) provisioned via Terraform
4. **Real-time updates:** ✅ DEFERRED - Manual polling in Swagger, SSE in future React SPA
5. **Technician registration:** ✅ Manual via POST `/api/technicians` (get chat_id from Telegram first)

## Success Criteria (MVP)

- ⬜ DynamoDB tables provisioned via Terraform
- ⬜ Admin can register technician via POST `/api/technicians` in Swagger
- ⬜ Admin can create assignment via POST `/api/assignments` in Swagger
- ⬜ Technician receives Telegram notification immediately
- ⬜ Technician responds via Telegram with service report
- ⬜ LLM extracts fields and asks follow-up questions
- ⬜ Admin can check status via GET `/api/assignments/{id}` in Swagger
- ⬜ Assignment status updates correctly in DynamoDB (pending → assigned → in_progress → completed)
- ⬜ Completed intake record persisted to DynamoDB and linked to assignment
- ⬜ All existing LLM extraction/validation logic preserved
- ⬜ All tests pass (unit + integration)
- ⬜ Documentation updated

**Stretch Goals:**
- ⬜ React SPA with real-time SSE updates
- ⬜ Authentication layer
- ⬜ Deploy to AWS (Lambda, API Gateway, CloudFront)

---

## Practical Usage Guide: Swagger UI Workflow

### Step 1: Start Services

```bash
# Terminal 1 - Backend
cd packages/api
poetry run uvicorn app.main:app --reload --port 4000

# Terminal 2 - ngrok (for Telegram webhook)
ngrok http 4000

# Terminal 3 - Register webhook
curl -F "url=https://<your-ngrok-id>.ngrok.io/webhook" \
  https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
```

### Step 2: Register Technician

1. Have technician send `/start` to your Telegram bot
2. Check logs for their `chat_id` (e.g., `12345678`)
3. Open Swagger UI: `http://localhost:4000/docs`
4. Find `POST /api/technicians` endpoint
5. Click "Try it out"
6. Enter request body:
   ```json
   {
     "chat_id": 12345678,
     "name": "John Smith",
     "phone_number": "+1-555-0123"
   }
   ```
7. Click "Execute"
8. Verify response shows technician created

### Step 3: Create Assignment

1. In Swagger UI, find `POST /api/assignments`
2. Click "Try it out"
3. Enter request body:
   ```json
   {
     "technician_chat_id": 12345678,
     "technician_name": "John Smith",
     "title": "HVAC Repair - Building 5",
     "description": "Check heating system in Building 5, Room 203",
     "priority": "high"
   }
   ```
4. Click "Execute"
5. Copy the `assignment_id` from response (e.g., `"abc-123-def-456"`)
6. **Technician receives Telegram notification immediately!**

### Step 4: Technician Responds

Technician replies to Telegram bot with service report:

```
Fixed HVAC unit in Building 5, Room 203. Replaced faulty thermostat.
```

Bot asks follow-up questions for missing fields:
```
What type of service was this? (e.g., HVAC Repair, Plumbing, Electrical)
```

Technician responds:
```
HVAC Repair
```

Bot continues until all required fields are collected.

### Step 5: Check Status

1. In Swagger UI, find `GET /api/assignments/{assignment_id}`
2. Click "Try it out"
3. Enter the assignment_id: `abc-123-def-456`
4. Click "Execute"
5. View response:
   ```json
   {
     "assignment_id": "abc-123-def-456",
     "status": "completed",
     "title": "HVAC Repair - Building 5",
     "technician_name": "John Smith",
     "intake_record_id": "xyz-789-uvw-012",
     "completed_at": "2026-08-03T15:30:00Z"
   }
   ```

### Step 6: View Completed Intake Record

1. Use `GET /api/assignments/{assignment_id}` response to get `intake_record_id`
2. Or use `GET /api/assignments?status=completed` to list all completed assignments
3. Each completed assignment includes linked intake record details

### Step 7: List All Assignments

```bash
# All assignments
GET /api/assignments

# Filter by status
GET /api/assignments?status=in_progress
GET /api/assignments?status=completed
```

### Troubleshooting

**Technician not receiving notification?**
- Check ngrok tunnel is still active
- Verify webhook is registered: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
- Check FastAPI logs for errors

**Assignment not updating?**
- Check DynamoDB tables exist: `aws dynamodb list-tables`
- Verify AWS credentials are configured
- Check FastAPI logs for DynamoDB errors

**LLM not extracting fields?**
- Verify LLM API key is set in `.env`
- Check extraction service logs
- Test with simpler messages first

---

## Migration to React SPA (When Ready)

Once the MVP workflow is validated with Swagger UI and DynamoDB:

1. All backend APIs are already built and tested
2. Create React project: `npm create vite@latest admin-ui -- --template react-ts`
3. Install dependencies: `npm install @tanstack/react-query axios`
4. Build components using proven API contract
5. Add SSE for real-time updates
6. No backend changes needed - just frontend addition

The API-first approach means the React SPA can be built independently without touching backend code.

---

## Phase 4: Telegram Bot Invitation System (Secure Chat ID Linking)

### Overview

Currently, technicians must manually message the bot first to get their `chat_id`, which is then manually registered by admins. This phase implements a secure, automated invitation system where:

1. Admin creates a technician in the UI with phone number
2. System generates a secure one-time invitation token
3. System sends SMS with Telegram deeplink: `https://t.me/<BOT>?start=<TOKEN>`
4. Technician taps link, opens Telegram, and starts bot
5. Telegram webhook receives `/start <TOKEN>` with technician's `chat_id`
6. Backend validates token and automatically links `technician_id ↔ chat_id`
7. Confirmation message sent via Telegram
8. Admin sees "Connected" status in UI

### Architecture Alignment

**Current Stack:**
- ✅ FastAPI backend (not generic Lambda)
- ✅ Terraform IaC (not AWS CDK)
- ✅ DynamoDB with UUID-based technicians
- ✅ Telegram webhook endpoint exists
- ✅ React SPA with technician management

**New Components:**
- AWS Secrets Manager for Telegram bot token
- DynamoDB table for invitation tokens
- SNS for SMS delivery (or existing provider)
- Webhook validation middleware
- Token generation service
- SMS integration service

### Implementation Steps

#### Step 4-0: Telegram Bot Invitation Infrastructure

**Goal:** Set up DynamoDB table for invitation tokens and Secrets Manager for bot token.

**Tasks:**
1. Create Terraform module for telegram-invitations DynamoDB table
   - Primary key: `token_hash` (string)
   - Attributes: `technician_id`, `expires_at`, `used_at`, `created_at`
   - TTL attribute: `expires_at`
   - GSI: `TechnicianIdIndex` (for looking up by technician)

2. Create AWS Secrets Manager secret for Telegram bot token
   - Secret name: `field-intake/<environment>/telegram-bot-token`
   - Store bot token value
   - Configure IAM permissions for Lambda/API to read

3. Add environment variables to backend:
   ```
   TELEGRAM_BOT_USERNAME=<your_bot>
   TELEGRAM_BOT_TOKEN_SECRET_NAME=field-intake/dev/telegram-bot-token
   TELEGRAM_INVITATION_TTL_SECONDS=3600
   AWS_REGION=us-east-1
   ```

4. Update Terraform to provision:
   - DynamoDB invitation table
   - Secrets Manager secret
   - IAM role with minimal permissions

**Success Criteria:**
- Terraform applies successfully
- DynamoDB table visible in AWS console
- Secret stored in Secrets Manager
- Backend can read secret via boto3

---

#### Step 4-1: Implement Invitation Token Service (TDD)

**Goal:** Create backend service to generate secure invitation tokens and deeplinks.

**Tasks:**
1. Create `TelegramInvitationService` with methods:
   ```python
   def generate_invitation(technician_id: str) -> TelegramInvitation:
       """Generate secure token, store hash, return deeplink."""
   
   def validate_token(token: str) -> str | None:
       """Validate token, return technician_id if valid, mark as used."""
   
   def cleanup_expired() -> int:
       """Remove expired invitations (optional cleanup job)."""
   ```

2. Implement token generation:
   - Use `secrets.token_urlsafe(32)` for cryptographic randomness
   - Hash token with SHA-256 before storing
   - Store only hash in DynamoDB (never raw token)
   - Set expiration (default 1 hour)
   - Generate Telegram deeplink: `https://t.me/{BOT_USERNAME}?start={token}`

3. Create Pydantic models:
   ```python
   class TelegramInvitation(BaseModel):
       token_hash: str
       technician_id: str
       telegram_link: str
       expires_at: datetime
       created_at: datetime
       used_at: datetime | None = None
   ```

4. Write comprehensive tests (TDD):
   - Token generation produces valid URL-safe tokens
   - Token hash is SHA-256 hex string
   - Deeplink format correct
   - Token validation succeeds for valid token
   - Token validation fails for expired token
   - Token validation fails for already-used token
   - Token validation fails for invalid token
   - Token can only be used once

**Success Criteria:**
- All tests pass
- Tokens are cryptographically secure
- Only hash stored in DynamoDB
- Tokens expire correctly
- Tokens are single-use

---

#### Step 4-2: Telegram Webhook Token Validation

**Goal:** Extend webhook endpoint to handle `/start <TOKEN>` and link chat_id.

**Tasks:**
1. Update webhook handler to detect `/start` command:
   ```python
   if message_text.startswith('/start '):
       token = message_text.split(' ', 1)[1]
       await handle_telegram_invitation(token, chat_id, update)
       return
   ```

2. Implement `handle_telegram_invitation`:
   - Validate token via `TelegramInvitationService.validate_token()`
   - Get `technician_id` from validated token
   - Update technician record with `chat_id`
   - Mark invitation as used
   - Send confirmation message via Telegram
   - Handle errors gracefully (expired, invalid, already used)

3. Add Telegram webhook validation (optional security):
   - Validate Telegram IP ranges (if configured)
   - Verify webhook secret token (if configured)
   - Implement idempotency using `update_id`

4. Add tests:
   - `/start` with valid token links chat_id
   - `/start` with expired token returns error message
   - `/start` with used token returns error message
   - `/start` with invalid token returns error message
   - Duplicate webhook (same update_id) is idempotent
   - Regular messages (non-/start) work normally

**Success Criteria:**
- Webhook handles `/start <TOKEN>` correctly
- Chat ID automatically linked to technician
- Confirmation message sent
- Errors handled gracefully
- Idempotent processing
- Existing webhook functionality preserved

---

#### Step 4-3: SMS Integration with Deeplinks (Backend API)

**Goal:** Add API endpoint to create invitation and send SMS.

**Tasks:**
1. Create POST `/api/technicians/{technician_id}/telegram-invitation` endpoint:
   ```python
   @router.post("/{technician_id}/telegram-invitation")
   async def create_telegram_invitation(
       technician_id: str,
       repo: TechnicianRepository = Depends(get_technician_repo),
       invitation_service: TelegramInvitationService = Depends(get_invitation_service),
       sms_service: SMSService = Depends(get_sms_service)
   ):
       # Get technician
       technician = repo.get_technician(technician_id)
       if not technician:
           raise HTTPException(404, "Technician not found")
       
       # Generate invitation
       invitation = invitation_service.generate_invitation(technician_id)
       
       # Send SMS
       await sms_service.send_telegram_invitation(
           phone_number=technician.phone_number,
           technician_name=technician.name,
           telegram_link=invitation.telegram_link
       )
       
       return {
           "success": True,
           "expires_at": invitation.expires_at,
           "phone_number": technician.phone_number  # Masked for security
       }
   ```

2. Create `SMSService` abstraction:
   ```python
   class SMSService(ABC):
       @abstractmethod
       async def send_telegram_invitation(
           self, phone_number: str, technician_name: str, telegram_link: str
       ) -> bool:
           pass
   ```

3. Implement SMS provider (choose one):
   - **Option A:** AWS SNS (native AWS)

4. SMS message template:
   ```
   Hi {name}, tap this link to connect your Telegram account to Field Intake:
   {telegram_link}
   
   This link expires in 1 hour.
   ```

5. Add tests:
   - Endpoint creates invitation
   - SMS sent to technician's phone
   - Returns correct response
   - Handles invalid technician_id (404)
   - Handles technician without phone number
   - SMS failure logged but doesn't block invitation creation

**Success Criteria:**
- Endpoint creates invitation and returns deeplink
- SMS sent successfully
- Error handling for invalid inputs
- All tests pass

---

#### Step 4-4: Frontend UI for Telegram Connection

**Goal:** Add UI for sending invitation and showing connection status.

**Tasks:**
1. Update TechnicianList component:
   - Add "Telegram Status" column
   - Show "Connected" (green) if `chat_id` exists
   - Show "Not Connected" (gray) with "Send Invitation" button if no `chat_id`
   - Show "Invitation Sent" (yellow) with timestamp if invitation pending

2. Create "Send Telegram Invitation" button:
   ```typescript
   const handleSendInvitation = async (technicianId: string) => {
     try {
       await api.createTelegramInvitation(technicianId);
       alert('Telegram invitation sent via SMS');
       // Refresh technician list
     } catch (error) {
       alert('Failed to send invitation: ' + error.message);
     }
   };
   ```

3. Add API client method:
   ```typescript
   async createTelegramInvitation(technicianId: string): Promise<void> {
     const response = await fetch(
       `${API_BASE_URL}/api/technicians/${technicianId}/telegram-invitation`,
       { method: 'POST' }
     );
     if (!response.ok) throw new Error('Failed to send invitation');
   }
   ```

4. Update technician status display:
   - Poll technician list every 10 seconds (or use SSE)
   - When `chat_id` changes from null to value, show "Connected" status
   - Show connection timestamp

5. Add visual feedback:
   - Loading state while sending invitation
   - Success toast/alert on invitation sent
   - Error handling for SMS failures

**Success Criteria:**
- "Send Invitation" button visible for unconnected technicians
- Clicking button sends SMS
- UI updates to show "Invitation Sent" status
- When technician connects, status changes to "Connected"
- Error messages displayed appropriately

---

#### Step 4-5: End-to-End Testing and Documentation

**Goal:** Test complete flow and document setup process.

**Tasks:**
1. **Manual end-to-end test:**
   - Create technician in UI with real phone number
   - Click "Send Telegram Invitation"
   - Receive SMS on phone
   - Tap Telegram deeplink
   - Start bot in Telegram
   - Verify confirmation message received
   - Verify UI shows "Connected" status
   - Create assignment for that technician
   - Verify assignment notification received in Telegram

2. **Automated integration tests:**
   ```python
   def test_full_telegram_invitation_flow():
       # Create technician
       # Generate invitation
       # Mock SMS sent
       # Simulate webhook with /start token
       # Verify chat_id linked
       # Verify confirmation message sent
       # Verify invitation marked as used
   ```

3. **Documentation updates:**
   - Update `docs/telegram-setup.md` with BotFather configuration
   - Document webhook registration process
   - Document Secrets Manager setup
   - Document SMS provider configuration
   - Add troubleshooting guide

4. **Webhook registration script:**
   ```bash
   #!/bin/bash
   # scripts/register-telegram-webhook.sh
   
   BOT_TOKEN=$(aws secretsmanager get-secret-value \
     --secret-id field-intake/dev/telegram-bot-token \
     --query SecretString --output text)
   
   WEBHOOK_URL="https://your-api-gateway.amazonaws.com/webhook"
   
   curl -X POST \
     "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
     -H "Content-Type: application/json" \
     -d "{\"url\":\"${WEBHOOK_URL}\"}"
   ```

5. **Security checklist:**
   - ✅ Bot token in Secrets Manager (never in code)
   - ✅ Invitation tokens hashed before storage
   - ✅ Tokens expire after 1 hour
   - ✅ Tokens single-use
   - ✅ Webhook validates update_id for idempotency
   - ✅ IAM roles follow least privilege
   - ✅ Phone numbers masked in logs
   - ✅ Raw tokens never logged

**Success Criteria:**
- Complete flow works end-to-end
- All automated tests pass
- Documentation complete and accurate
- Security checklist verified
- Webhook registered successfully

---

### Key Differences from Original Spec

**Adapted for Field Intake Architecture:**
1. **FastAPI instead of generic Lambda** - Use existing FastAPI patterns, not Lambda-specific code
2. **Terraform instead of CDK** - Extend existing Terraform modules
3. **UUID-based technicians** - Link invitation to `technician_id` (UUID), not arbitrary `userId`
4. **Existing webhook endpoint** - Extend `/webhook` rather than create `/telegram/webhook`
5. **Technician phone numbers** - Already have `phone_number` field from Step 3-2
6. **No separate authentication** - Technicians identified by `technician_id` from invitation token
7. **DynamoDB patterns** - Follow existing repository pattern conventions
8. **React SPA** - Frontend already exists, just extend TechnicianList component

### Migration from Manual chat_id to Automated

**Current state (Step 3-2):**
- Admin manually gets chat_id from logs
- Admin manually enters chat_id when creating technician
- Technician manually messages bot first

**Target state (Step 4-x):**
- Admin creates technician with phone number only
- System sends SMS invitation automatically
- Technician taps link and chat_id auto-links
- No manual chat_id copying

**Backward compatibility:**
- Keep existing manual flow working
- Add new automated flow as enhancement
- Support both flows simultaneously
- Existing technicians with chat_id continue working

### Next Steps After Phase 4

Once Telegram invitation system is complete:

1. **Phase 5:** Assignment notifications via SMS (for technicians without Telegram)
2. **Phase 6:** Bi-directional SMS support (technician responds via SMS, not just Telegram)
3. **Phase 7:** Web-based intake form (no Telegram/SMS required)
4. **Phase 8:** Mobile app with push notifications
