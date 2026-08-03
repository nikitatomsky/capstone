# Testing Guidelines

## Overview

This project emphasizes **Test-Driven Development (TDD)** as a core workflow pattern. Tests are not just validation tools - they are your roadmap for implementation and your safety net for refactoring.

## Testing Scope

This project focuses on **unit tests**, **integration tests**, and **end-to-end webhook tests**:

- ✅ **Unit Tests**: Testing individual functions, validators, and extraction logic with Pytest
- ✅ **Integration Tests**: Testing FastAPI routes end-to-end with TestClient
- ✅ **Webhook Tests**: Testing Telegram webhook handling with representative payloads
- ✅ **Storage Tests**: Testing storage and notification interfaces with fakes
- ✅ **Infrastructure Tests**: Validating Terraform syntax and planned resources

**Why this scope?**

- Unit tests provide fast feedback on validation, extraction, and business logic.
- Integration tests verify webhook behavior and data flow.
- Storage tests ensure SQLite and future DynamoDB implementations work correctly.
- Infrastructure tests catch Terraform errors before deployment.

## Testing Philosophy

### Tests Should Drive Development

1. **Read the test first** to understand requirements
2. **Run the test** to see it fail (Red)
3. **Implement** minimal code to pass (Green)
4. **Refactor** to improve quality
5. **Repeat** with the next test

### TDD Workflow Scope Boundaries

When fixing failing tests (TDD Scenario 2):

- ✅ **DO**: Fix code to make tests pass
- ✅ **DO**: Run tests after each change
- ✅ **DO**: Refactor code while keeping tests green
- ❌ **DO NOT**: Fix linting errors unless they prevent tests from passing
- ❌ **DO NOT**: Remove debug logging that isn't breaking tests
- ❌ **DO NOT**: Fix unused imports unless they cause test failures

**Why?** Linting is a separate quality workflow. Keeping workflows separate teaches proper separation of concerns and systematic problem-solving.

### Tests Provide Specification

Each test describes:

- **What** the code should do
- **How** it should behave
- **When** it should succeed or fail
- **Why** certain decisions were made

## Backend Testing Strategy

### Test Structure

We use **Pytest** and **FastAPI TestClient** for API testing:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestWebhookEndpoint:
    """Test Telegram webhook handling."""

    def test_should_extract_structured_data_from_free_text(self):
        """Test that LLM extraction produces expected fields."""
        # Arrange: Set up test data
        # Act: Call the API
        # Assert: Verify results
```

### Test Categories

#### 1. Happy Path Tests

Test expected behavior with valid inputs:

```python
def test_should_accept_valid_telegram_webhook_payload():
    """Webhook accepts a well-formed Telegram update."""
    payload = {
        "update_id": 123456789,
        "message": {
            "chat": {"id": 999, "type": "private"},
            "from": {"id": 888, "first_name": "John"},
            "text": "Completed service call at 123 Main St, repaired HVAC unit"
        }
    }

    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    assert "message_id" in response.json()
```

#### 2. Validation Tests

Test error handling with invalid inputs:

```python
def test_should_reject_webhook_payload_missing_required_fields():
    """Webhook returns 422 when required fields are missing."""
    payload = {"update_id": 123}  # Missing message

    response = client.post("/webhook", json=payload)

    assert response.status_code == 422
    assert "error" in response.json()
```

#### 3. Pydantic Schema Tests

Test intake record validation:

```python
from app.models.intake_record import IntakeRecord
from pydantic import ValidationError

def test_should_require_location_field():
    """IntakeRecord raises ValidationError when location is missing."""
    with pytest.raises(ValidationError) as exc_info:
        IntakeRecord(
            employee_id="EMP123",
            service_type="HVAC Repair",
            # location missing
            timestamp="2024-03-15T14:30:00Z"
        )

    assert "location" in str(exc_info.value)
```

#### 4. Extraction Logic Tests

Test LLM extraction without calling a live LLM:

```python
def test_should_extract_service_call_fields_from_free_text(mocker):
    """Extraction agent parses free text into structured fields."""
    # Mock LLM call
    mock_llm = mocker.patch("app.services.extraction_agent.call_llm")
    mock_llm.return_value = {
        "service_type": "HVAC Repair",
        "location": "123 Main St",
        "issue": "Unit not cooling"
    }

    from app.services.extraction_agent import extract_intake_fields

    result = extract_intake_fields("Fixed HVAC at 123 Main St, wasn't cooling")

    assert result["service_type"] == "HVAC Repair"
    assert result["location"] == "123 Main St"
```

#### 5. Integration Tests

Test multiple operations together:

```python
def test_should_handle_complete_intake_workflow(mocker):
    """Test full flow: webhook -> extraction -> validation -> persistence -> notification."""
    # Mock external dependencies
    mock_llm = mocker.patch("app.services.extraction_agent.call_llm")
    mock_llm.return_value = {"service_type": "Inspection", "location": "456 Oak Ave"}

    mock_notify = mocker.patch("app.services.notification_client.send_notification")

    # Send webhook
    payload = {
        "update_id": 123,
        "message": {
            "chat": {"id": 999},
            "from": {"id": 888},
            "text": "Completed inspection at 456 Oak Ave"
        }
    }

    response = client.post("/webhook", json=payload)

    # Verify response
    assert response.status_code == 200

    # Verify notification was sent
    mock_notify.assert_called_once()
```

## Telegram Webhook Testing Strategy

### Webhook Payload Structure

Telegram sends updates in a specific format. Test with representative payloads:

```python
def get_sample_telegram_message(text: str, chat_id: int = 999):
    """Helper to generate test Telegram payloads."""
    return {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {"id": 888, "first_name": "Test", "is_bot": False},
            "chat": {"id": chat_id, "type": "private"},
            "date": 1638360000,
            "text": text
        }
    }
```

### Testing Conversation State

Test multi-turn conversations:

```python
def test_should_prompt_for_missing_fields_in_follow_up():
    """When extraction is incomplete, bot asks for missing information."""
    # First message with incomplete data
    payload1 = get_sample_telegram_message("Fixed something")
    response1 = client.post("/webhook", json=payload1)

    # Verify bot asks for location
    assert "location" in response1.json()["reply"].lower()

    # Second message with location
    payload2 = get_sample_telegram_message("At 123 Main St")
    response2 = client.post("/webhook", json=payload2)

    # Verify record is now complete
    assert response2.json()["status"] == "complete"
```

## Storage Testing Strategy

### Testing with Fakes

Use in-memory storage for fast tests:

```python
from app.services.storage_client import StorageInterface

class FakeStorage(StorageInterface):
    """In-memory storage for testing."""

    def __init__(self):
        self.records = {}

    def save_record(self, record):
        self.records[record.id] = record
        return record.id

    def get_record(self, record_id):
        return self.records.get(record_id)

def test_should_persist_complete_intake_record():
    """Storage saves and retrieves records correctly."""
    storage = FakeStorage()

    from app.models.intake_record import IntakeRecord

    record = IntakeRecord(
        employee_id="EMP123",
        service_type="HVAC Repair",
        location="123 Main St",
        timestamp="2024-03-15T14:30:00Z"
    )

    record_id = storage.save_record(record)
    retrieved = storage.get_record(record_id)

    assert retrieved.employee_id == "EMP123"
    assert retrieved.location == "123 Main St"
```

## Running Tests

### Run All Tests

```bash
cd packages/api
poetry run pytest
```

### Run Tests in Watch Mode

```bash
poetry run pytest-watch
```

### Run Specific Test File

```bash
poetry run pytest tests/test_webhook.py
```

### Run Specific Test by Name

```bash
poetry run pytest -k "test_should_extract_service_call_fields"
```

### Run with Coverage

```bash
poetry run pytest --cov=app --cov-report=term-missing
```

### Run Verbose

```bash
poetry run pytest -v
```

### Infrastructure Validation

```bash
terraform -chdir=../../infra/stacks/dev init -backend=false
terraform -chdir=../../infra/stacks/dev validate
```

## Test-Driven Workflow with Copilot

### Step 1: Understand the Test

```text
You: "Explain what this test expects:
[paste test code]"

Copilot: "This test verifies that..."
```

### Step 2: Implement to Pass

```text
You: "Implement the webhook handler to pass this test:
[paste test code]"

Copilot: [Provides implementation]
```

### Step 3: Verify

```bash
poetry run pytest -k "test_should_accept_valid_telegram_webhook_payload"
```

### Step 4: Handle Failures

```text
Test output:
  AssertionError: assert 422 == 200

You: "The test expects 200 but returns 422. What's wrong with this code:
[paste current implementation]"

Copilot: "The endpoint is rejecting valid payloads. Check your Pydantic model..."
```

### Step 5: Iterate

Continue until the test passes, then move to the next test.

## Common Testing Patterns

### Testing Async Operations

```python
import pytest

@pytest.mark.asyncio
async def test_should_call_async_llm_api():
    """Test async LLM extraction."""
    from app.services.extraction_agent import extract_async

    result = await extract_async("Completed repair at 123 Main St")

    assert result["location"] == "123 Main St"
```

### Mocking External APIs

```python
def test_should_handle_llm_api_timeout(mocker):
    """Extraction gracefully handles LLM timeouts."""
    mock_llm = mocker.patch("app.services.extraction_agent.call_llm")
    mock_llm.side_effect = TimeoutError("API timeout")

    from app.services.extraction_agent import extract_intake_fields

    with pytest.raises(TimeoutError):
        extract_intake_fields("Some text")
```

### Testing Error States

```python
def test_should_return_error_message_when_storage_fails(mocker):
    """Webhook returns 500 when storage fails."""
    mock_storage = mocker.patch("app.services.storage_client.save_record")
    mock_storage.side_effect = Exception("Database error")

    payload = get_sample_telegram_message("Completed work")
    response = client.post("/webhook", json=payload)

    assert response.status_code == 500
    assert "error" in response.json()
```

### Using Pytest Fixtures

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    """FastAPI test client fixture."""
    from app.main import app
    return TestClient(app)

@pytest.fixture
def sample_telegram_message():
    """Sample Telegram payload fixture."""
    return {
        "update_id": 123,
        "message": {
            "chat": {"id": 999},
            "text": "Test message"
        }
    }

def test_webhook_accepts_message(client, sample_telegram_message):
    """Use fixtures in tests."""
    response = client.post("/webhook", json=sample_telegram_message)
    assert response.status_code == 200
```

## Debugging Failing Tests

### 1. Read the Error Message Carefully

```text
AssertionError: assert 400 == 200

This tells you:
- The test expected success (200)
- The API returned a validation error (400)
- Check request payload structure
```

### 2. Use Print Statements Strategically

```python
def test_debugging_example(client):
    """Example of debugging with print."""
    response = client.post("/webhook", json=payload)

    print(f"Status: {response.status_code}")
    print(f"Body: {response.json()}")
    # Now you can see what's actually being returned

    assert response.status_code == 200
```

### 3. Use Pytest's `-s` Flag

```bash
poetry run pytest -s  # Shows print statements
```

### 4. Ask Copilot for Help

```text
You: "This test is failing with this error: [paste error]
Here's the test: [paste test]
Here's my implementation: [paste code]
What's wrong?"
```

### 5. Isolate the Problem

Run just the failing test:

```bash
poetry run pytest tests/test_webhook.py::test_should_accept_valid_telegram_webhook_payload -v
```

### 6. Check Test Assumptions

Verify:

- Is the test correct?
- Are imports working?
- Is the endpoint path correct?
- Is test data valid?
- Are mocks configured correctly?

## Test Organization Best Practices

### Group Related Tests

```python
class TestWebhookValidation:
    """Tests for webhook payload validation."""

    def test_requires_update_id(self):
        """Webhook rejects payloads without update_id."""
        pass

    def test_requires_message_or_callback(self):
        """Webhook rejects payloads without message."""
        pass


class TestExtractionAgent:
    """Tests for LLM extraction logic."""

    def test_extracts_service_type(self):
        """Extraction identifies service type from free text."""
        pass

    def test_extracts_location(self):
        """Extraction identifies location from free text."""
        pass
```

### Use Descriptive Test Names

❌ **Vague:**

```python
def test_webhook():
    pass

def test_error():
    pass
```

✅ **Clear:**

```python
def test_should_accept_valid_telegram_webhook_payload():
    pass

def test_should_return_422_when_payload_missing_required_fields():
    pass
```

### Keep Tests Independent

Each test should:

- Set up its own data
- Use fixtures or factories for test data
- Not rely on other tests
- Clean up if needed (Pytest handles most cleanup automatically)

## Success Criteria

You understand testing when you can:

- ✅ Read a test and explain what it verifies
- ✅ Run tests and interpret failure messages
- ✅ Implement code to make failing tests pass
- ✅ Write new tests for new features
- ✅ Mock external dependencies (LLM APIs, Telegram, storage)
- ✅ Use tests to catch regressions during refactoring
- ✅ Debug failing tests systematically

## Remember

> "Tests are not just about finding bugs - they are about confidence. When all
> tests pass, you know your code works as intended. When you refactor, tests
> ensure you have not broken anything. Tests are your safety net."

Happy testing!
