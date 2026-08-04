# Patterns Discovered

Reusable patterns and architectural decisions for the Field Intake Service.

---

## Project Structure

### Golden Path Scaffold Pattern

```text
docs/                         Planning and requirements
context/                      IaC and CI specifications
infra/
  modules/                    Reusable Terraform modules
  stacks/dev/                 Environment-specific configs
packages/api/                 Python FastAPI service
  app/
    main.py                   FastAPI entrypoint
    routers/                  Route handlers
    services/                 Business logic
    models/                   Pydantic schemas
  tests/                      Pytest test suite
.github/workflows/            CI/CD automation
```

**Why**: Separates planning (docs), requirements (context), infrastructure (infra), and implementation (packages) into clear boundaries.

---

## Testing Patterns

### Telegram Webhook Test Helper

```python
def get_sample_telegram_message(text: str, chat_id: int = 999):
    """Generate test Telegram update payload."""
    return {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {"id": 888, "first_name": "Test"},
            "chat": {"id": chat_id, "type": "private"},
            "text": text
        }
    }
```

**Why**: Telegram payloads have specific structure; a helper ensures test consistency.

### Storage Interface Testing with Fakes

```python
class FakeStorage(StorageInterface):
    """In-memory storage for testing."""
    def __init__(self):
        self.records = {}

    def save_record(self, record):
        self.records[record.id] = record
        return record.id
```

**Why**: Fast, isolated tests without database dependencies; easy swap for SQLite/DynamoDB.

---

## Service Integration Patterns

### Non-Blocking Notification Pattern

```python
async def create_assignment(
    assignment_data: AssignmentCreate,
    repo: AssignmentRepository = Depends(get_assignment_repo),
    telegram: TelegramClient = Depends(get_telegram_client)
) -> Assignment:
    # Create core entity first (source of truth)
    assignment = repo.create_assignment(assignment_data)
    
    # Send notification (best-effort, non-blocking)
    try:
        await telegram.send_assignment_notification(
            chat_id=assignment.technician_chat_id,
            assignment_id=assignment.assignment_id,
            title=assignment.title,
            description=assignment.description,
            priority=assignment.priority
        )
    except Exception as e:
        # Log error but don't fail assignment creation
        logger.error(f"Failed to send notification: {e}")
    
    return assignment
```

**Why**: External service failures (Telegram API) shouldn't prevent core operations. The database is the source of truth; notifications are best-effort delivery. This prevents cascading failures and maintains data integrity.

**When to use**: Any integration with external services (email, SMS, webhooks, third-party APIs) where the external call is not critical to the core business operation.

---

## Placeholder Conventions

### Clear Naming for TODOs

- Use `<descriptive-placeholder>` for required values: `<aws-region>`, `<health-path>`
- Use `TODO:` prefix in comments for implementation tasks
- Use `placeholder` in echo commands for CI jobs that aren't implemented yet

**Why**: Makes it obvious what needs to be filled in before production use.

---

## Real-Time Communication Patterns

### Server-Sent Events (SSE) for Real-Time Updates

**Pattern**: Use SSE for server-to-client push notifications

**Implementation**:

```python
# SSE Manager Service (app/services/sse_manager.py)
class SSEManager:
    """Manages Server-Sent Events connections for real-time updates."""
    
    def __init__(self):
        self.connections: set[asyncio.Queue] = set()
    
    async def subscribe(self) -> AsyncGenerator[str, None]:
        """Subscribe to assignment update events."""
        queue = asyncio.Queue()
        self.connections.add(queue)
        try:
            while True:
                message = await queue.get()
                yield message
        finally:
            self.connections.remove(queue)
    
    async def broadcast(self, event_type: str, data: dict):
        """Broadcast event to all connected clients."""
        message = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        for queue in self.connections:
            try:
                await queue.put(message)
            except Exception as e:
                logger.error(f"Failed to send SSE message: {e}")

# Global instance
sse_manager = SSEManager()

# SSE Router (app/routers/sse.py)
@router.get("/api/assignments/stream")
async def stream_assignments():
    """Stream assignment updates via Server-Sent Events."""
    return EventSourceResponse(sse_manager.subscribe())

# Broadcast on Entity Changes (app/routers/assignment.py)
async def create_assignment(...):
    assignment = repo.create_assignment(...)
    
    # Broadcast to all connected SSE clients
    await sse_manager.broadcast(
        "assignment_created",
        {
            "assignment_id": assignment.assignment_id,
            "status": assignment.status,
            "technician_name": assignment.technician_name,
        }
    )
    
    return assignment
```

**Frontend Usage** (JavaScript):

```javascript
const eventSource = new EventSource('http://localhost:4000/api/assignments/stream');

eventSource.addEventListener('assignment_created', (event) => {
    const data = JSON.parse(event.data);
    console.log('New assignment:', data);
    // Update UI with new assignment
});
```

**Why**: 
- SSE is simpler than WebSockets for server-to-client push (no bidirectional communication needed)
- Perfect for dashboard status updates and notifications
- Built-in reconnection logic in browsers
- Lower overhead than polling

**When to use**:
- Real-time dashboards showing entity status
- Live notifications to admin interfaces
- One-way server-to-client updates
- Don't need client-to-server messages (use WebSockets if you do)

**Router Registration Order Gotcha**:
```python
# WRONG - SSE endpoint won't work!
app.include_router(assignment.router)  # Has /{assignment_id} route
app.include_router(sse.router)         # Has /stream route

# CORRECT - Specific routes first!
app.include_router(sse.router)         # Register /stream first
app.include_router(assignment.router)  # Then /{assignment_id}
```

**Why**: FastAPI matches routes in registration order. `/api/assignments/stream` would match `/api/assignments/{assignment_id}` pattern if assignment router is registered first, treating "stream" as an assignment_id.

---

## Cross-Origin Resource Sharing (CORS) Patterns

### Restrictive CORS Whitelist

**Pattern**: Use restrictive CORS origin whitelist instead of wildcard

**Implementation**:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React port
        # Add production domain: "https://your-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Why**:
- Wildcard CORS (`allow_origins=["*"]`) is a security risk
- Allows malicious sites to make requests to your API
- Restrictive whitelist prevents unauthorized cross-origin access
- Easy to add production domains when deploying

**Testing CORS**:

```python
def test_cors_headers_present_on_preflight():
    """Test CORS headers are present on OPTIONS preflight request."""
    response = client.options(
        "/api/assignments",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
```

**When to use**:
- Any API that will be accessed from a browser-based frontend
- Especially important when API handles authentication or sensitive data
- Always use whitelisting in production

---

## Infrastructure Patterns

### Secrets Manager Integration Pattern

**Problem**: Need to store sensitive credentials (API keys, tokens) without committing to source control or Terraform state.

**Solution**: Terraform creates empty secret resource; value populated manually.

```hcl
# Terraform creates the secret container
resource "aws_secretsmanager_secret" "telegram_bot_token" {
  name        = "${var.project_name}/${var.environment}/telegram-bot-token"
  description = "Telegram bot token for field intake service"
}

# Secret value is optional (set manually)
resource "aws_secretsmanager_secret_version" "telegram_bot_token" {
  count         = var.telegram_bot_token != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.telegram_bot_token.id
  secret_string = var.telegram_bot_token
}
```

**Manual secret value setting**:

```bash
# Retrieve token from local .env
TOKEN=$(grep TELEGRAM_BOT_TOKEN packages/api/.env | cut -d '=' -f2)

# Store in Secrets Manager
aws secretsmanager put-secret-value \
  --secret-id field-intake/dev/telegram-bot-token \
  --secret-string "$TOKEN"
```

**Application runtime retrieval**:

```python
import boto3

def get_telegram_bot_token():
    """Retrieve bot token from Secrets Manager."""
    client = boto3.client('secretsmanager', region_name=os.getenv('AWS_REGION'))
    response = client.get_secret_value(
        SecretId=os.getenv('TELEGRAM_BOT_TOKEN_SECRET_NAME')
    )
    return response['SecretString']
```

**Why**:
- Secrets never appear in Terraform state files
- Secrets never committed to source control
- Secret rotation possible without code changes
- IAM controls who can read secrets
- Audit trail of secret access in CloudTrail

**When to use**:
- API keys, tokens, passwords
- Database credentials
- OAuth client secrets
- Any sensitive configuration value

---

### DynamoDB TTL for Temporary Data

**Problem**: Need to automatically clean up temporary data (invitation tokens, session data, cache entries) without manual intervention.

**Solution**: Use DynamoDB Time-to-Live (TTL) feature.

```hcl
resource "aws_dynamodb_table" "telegram_invitations" {
  name         = "field-intake-telegram-invitations-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "token_hash"

  # ... attributes ...

  # Enable TTL for automatic cleanup
  ttl {
    attribute_name = "expires_at_ttl"
    enabled        = true
  }
}
```

**Application code**:

```python
import time

def create_invitation_token(technician_id: str, ttl_seconds: int = 3600):
    """Create invitation token with expiration."""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # TTL attribute must be Unix timestamp (seconds since epoch)
    expires_at_ttl = int(time.time()) + ttl_seconds
    
    dynamodb.put_item(
        TableName='telegram-invitations',
        Item={
            'token_hash': {'S': token_hash},
            'technician_id': {'S': technician_id},
            'expires_at_ttl': {'N': str(expires_at_ttl)},  # DynamoDB requires string
            'created_at': {'S': datetime.utcnow().isoformat()}
        }
    )
    
    return token  # Return original token (not hash)
```

**Why**:
- Automatic cleanup (no cron jobs needed)
- Reduces storage costs
- Items deleted within 48 hours of expiration
- No operational overhead
- Scales automatically with table size

**When to use**:
- Invitation tokens, password reset tokens
- Session data, temporary caches
- Rate limiting counters
- Audit logs with retention policy
- Any data with defined expiration

**Important notes**:
- TTL attribute must be Unix timestamp (seconds since epoch)
- DynamoDB stores as number, so cast to string in put_item
- Deletion happens within 48 hours (not instant)
- TTL deletes don't consume write capacity
- Deleted items don't appear in queries immediately

---

### IAM Policy Scoping by Environment

**Problem**: Need to grant access to environment-specific resources without hard-coding ARNs or granting overly broad permissions.

**Solution**: Use wildcard patterns with environment suffix in IAM policies.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadTelegramBotToken",
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": "arn:aws:secretsmanager:*:*:secret:field-intake/*/telegram-bot-token*"
    },
    {
      "Sid": "TelegramInvitationsTableAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/*-telegram-invitations-*",
        "arn:aws:dynamodb:*:*:table/*-telegram-invitations-*/index/*"
      ]
    }
  ]
}
```

**Terraform IAM policy resource**:

```hcl
resource "aws_iam_policy" "telegram_backend_policy" {
  name        = "${var.project_name}-telegram-backend-${var.environment}"
  description = "Policy for backend to access Telegram bot token and invitations"
  policy      = file("${path.module}/telegram-backend-policy.json")
}
```

**Why**:
- Prevents cross-environment access (dev can't access prod)
- Allows flexibility (works across regions)
- Least-privilege principle (specific resources, not `*`)
- Environment-specific policy names prevent conflicts
- Easy to audit (clear resource patterns)

**Pattern matching**:
- `field-intake/*/telegram-bot-token*` matches:
  - ✅ `field-intake/dev/telegram-bot-token`
  - ✅ `field-intake/staging/telegram-bot-token`
  - ✅ `field-intake/prod/telegram-bot-token`
  - ❌ `other-project/dev/telegram-bot-token`
- `*-telegram-invitations-*` matches:
  - ✅ `field-intake-telegram-invitations-dev`
  - ✅ `field-intake-telegram-invitations-prod`
  - ❌ `field-intake-assignments-dev`

**When to use**:
- Multi-environment deployments (dev, staging, prod)
- Resources with predictable naming conventions
- Least-privilege IAM policies
- Cross-region resource access
- Terraform-managed infrastructure

**Anti-patterns to avoid**:
- ❌ Hard-coding account IDs in policies (use `*`)
- ❌ Using `Resource: "*"` (too broad)
- ❌ Granting `AdministratorAccess` (violates least-privilege)
- ❌ Not scoping by project name (allows access to other projects)

---

*This file will grow as implementation patterns emerge through TDD.*
