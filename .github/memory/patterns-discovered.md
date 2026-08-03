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

## Placeholder Conventions

### Clear Naming for TODOs

- Use `<descriptive-placeholder>` for required values: `<aws-region>`, `<health-path>`
- Use `TODO:` prefix in comments for implementation tasks
- Use `placeholder` in echo commands for CI jobs that aren't implemented yet

**Why**: Makes it obvious what needs to be filled in before production use.

---

*This file will grow as implementation patterns emerge through TDD.*
