---
description: "Global workspace instructions for Field Intake Service development"
---

# Field Intake Service - Copilot Instructions

## Project Context

This is a conversational AI field intake service using Python 3.12, FastAPI, and Telegram webhooks. Field employees report service call outcomes through chat; the system extracts structured data using an LLM, validates completeness with Pydantic, asks follow-up questions when needed, and persists completed records. Development follows an iterative, feedback-driven approach with emphasis on quality and systematic validation.

**Current Phase**: Local demo implementation with cloud-ready design

**Key Characteristics**:
- Python FastAPI backend with Telegram Bot API integration
- LLM-powered extraction and conversational validation
- Local-first demo (uvicorn + ngrok + SQLite)
- Cloud-shaped for AWS Lambda, DynamoDB, SNS deployment
- Test-driven development methodology
- Multiple testing layers (unit, integration, webhook simulation)
- Infrastructure as Code with Terraform
- Focus on incremental, validated changes

## Documentation References

Consult these project documentation files for detailed guidance:

- [docs/project-overview.md](../docs/project-overview.md) - Architecture, tech stack, and project structure
- [docs/testing-guidelines.md](../docs/testing-guidelines.md) - Test patterns and standards
- [docs/workflow-patterns.md](../docs/workflow-patterns.md) - Development workflow guidance

These documents provide essential context for understanding the codebase and making informed decisions.

## Development Principles

Follow these core principles in all development work:

1. **Test-Driven Development (TDD)**: Follow the Red-Green-Refactor cycle
   - Write failing tests first (RED)
   - Implement minimal code to pass (GREEN)
   - Refactor while keeping tests green (REFACTOR)

2. **Incremental Changes**: Make small, testable modifications
   - One feature or fix at a time
   - Each change should be independently testable
   - Avoid large, multi-purpose commits

3. **Systematic Debugging**: Use test failures as diagnostic guides
   - Read error messages carefully
   - Isolate the failing component
   - Fix root causes, not symptoms

4. **Validation Before Commit**: Ensure all quality gates pass
   - All tests pass (unit, integration, and UI)
   - No lint errors or warnings
   - Code meets project standards

## Testing Scope

This project employs a comprehensive testing strategy across multiple layers:

### Testing Layers

- **Backend API**: Pytest + FastAPI TestClient for webhook endpoint testing
- **Unit Tests**: Pydantic schema validation, extraction logic, storage interfaces
- **Integration Tests**: End-to-end webhook flows with mocked LLM and storage
- **Infrastructure Tests**: Terraform validation for AWS target architecture
- **Manual Testing**: Telegram-based exploratory validation with live bot

### Testing Philosophy

Combine fast feedback loops (unit/integration tests) with real-world webhook validation (manual Telegram testing). This multi-layer approach catches issues early while ensuring the conversational flow works correctly for field employees.

### Testing Approach by Context

**Webhook API Changes**:
- Write Pytest tests FIRST, then implement
- Follow strict RED-GREEN-REFACTOR cycle
- Test both success and error cases
- Validate Telegram payload handling

**Extraction and Validation Logic**:
- Write Pytest tests FIRST for Pydantic schemas and extraction functions
- Mock LLM calls to avoid hitting live APIs in tests
- Test incomplete data handling and follow-up prompts
- Validate field extraction accuracy

**Storage and Notification Services**:
- Write tests with fake/in-memory implementations FIRST
- Test SQLite local implementation
- Design for DynamoDB/SNS swap-in (future cloud deployment)
- Validate persistence and notification delivery

**Critical Conversation Flows**:
- Manual testing with Telegram bot and ngrok tunnel
- Test multi-turn conversations with missing fields
- Validate manager notifications
- Ensure graceful error handling

**Important**: This is true TDD - write the test first, watch it fail, then write code to make it pass.

## Workflow Patterns

Follow these structured workflows for different development activities:

### 1. TDD Workflow (Implementation)

1. Write or fix test(s) for the feature/bug
2. Run tests and observe failure (RED)
3. Implement minimal code to pass the test
4. Run tests and observe success (GREEN)
5. Refactor code while keeping tests green (REFACTOR)
6. Validate all tests still pass

### 2. Code Quality Workflow (Lint/Standards)

1. Run linter to identify issues
2. Categorize issues by type and severity
3. Fix systematically (one category at a time)
4. Re-validate with linter
5. Ensure all tests still pass

### 3. Integration Workflow (Full Stack)

1. Identify integration issue or requirement
2. Debug to understand root cause
3. Write tests at appropriate layer(s)
4. Implement fix or feature
5. Verify end-to-end functionality
6. Validate all automated tests pass

### 4. UI Testing Workflow (Playwright)

1. Define critical user journeys to automate
2. Create Playwright test specifications
3. Run tests and observe results
4. Debug and fix test failures (application or test issues)
5. Validate test coverage and stability
6. Document test scope and maintenance notes

##Pytest unit and integration test authoring
- FastAPI webhook endpoint development
- Pydantic schema and validation logic
- LLM extraction service implementation
- Storage and notification interface development
- Bug fixes with test-first approach

**Does NOT**:
- Handle Terraform infrastructure directly (use infrastructure-engineer instead)
- Handle lint-only issues (use code-reviewer instead)

### code-reviewer Agent

**Use for**:
- Addressing Ruff lint errors and warnings
- Code quality improvements
- Refactoring for better patterns
- Ensuring PEP 8 and project code standards compliance
- Type hint validation
- Style and consistency fixes

### infrastructure-engineer Agent

**Use for**:
- Terraform module and stack authoring
- AWS resource planning and validation
- Infrastructure tests (`terraform validate`, `terraform plan`)
- Cloud deployment strategy
- IaC refactoring and best practices

**Scope**: Owns the complete infrastructure as code lifecycle using Terraform.

### integration-tester Agent

**Use for**:
- Manual Telegram bot testing workflows
- End-to-end conversation flow validation
- ngrok tunnel setup and webhook registration
- Multi-turn conversation scenarios
- Manager notification verification
- Integration smoke testing before deployment

**Scope**: Validates real-world Telegram interactions and conversational behavior
**Use for**:
- All Playwright UI test authoring
- UI test execution and validation
- Failure triage (application vs. test defects)
- Test isolation and stability checks
- End-to-end test coverage planning

**Scope**: Owns the complete UI testing lifecycle using Playwright.

## Memory System

The project uses a two-tier memory system to preserve and apply knowledge across development sessions:

### Persistent Memory
This file (`.github/copilot-instructions.md`) contains foundational principles and workflows that define the project's approach.

### Working Memory
The `.github/memory/` directory contains discoveries, patterns, and session history:

- *Project-Specific Commands

Common development commands for the Field Intake Service:

### Local Development

```bash
# Start local FastAPI server
cd packages/api
poetry install
poetry run uvicorn app.main:app --reload --port 4000

# In separate terminal: Expose webhook with ngrok
ngrok http 4000

# Register webhook with Telegram
curl -F "url=https://<ngrok-id>.ngrok.io/webhook" \
  https://api.telegram.org/bot<TOKEN>/setWebhook
```

### Testing

```bash
# Run all tests
cd packages/api
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=term-missing

# Run specific test file
poetry run pytest tests/test_webhook.py

# Run specific test
poetry run pytest -k "test_should_accept_valid_telegram_webhook_payload"

# Run in watch mode
poetry run pytest-watch
```

### Code Quality

```bash
# Lint with Ruff
cd packages/api
poetry run ruff check .

# Format with Ruff
poetry run ruff format .
```

### Infrastructure Validation

```bash
# Validate Terraform syntax
terraform -chdir=infra/stacks/dev init -backend=false
terraform -chdir=infra/stacks/dev validate

# Plan infrastructure changes (requires AWS credentials)
terraform -chdir=infra/stacks/dev plan
```

### GitHub CLI Commands

```bash
# List all open issues
gh issue list --state open

# View specific issue details
gh issue view <issue-number>

# View issue with all comments
gh issue view <issue-number> --comments
```

GitHub CLI commands are available for workflow automation across all agent modes:

### Issue Management Commands

```bash
# List all open issues
gh issue list --state open

# View specific issue details
gh issue view <issue-number>

# View issue with all comments
gh issue view <issue-number> --comments
```

### Exercise Step Commands

- The main exercise issue contains "Exercise:" in the title
- Individual steps are posted as comments on the main issue
- Use `/execute-step` prompt to implement a specific step
- Use `/validate-step` prompt to verify step completion
- Always use `gh issue view` commands to retrieve current context

## Git Workflow

Follow these Git practices for all commits and branches:

### Conventional Commits

Use conventional commit format for all commits:

- `feat:` - New feature
- `fix:` - Bug fix
- `chore:` - Maintenance tasks
- `docs:` - Documentation changes
- `test:` - Test additions or modifications
- `refactor:` - Code refactoring without behavior change

**Example**: `feat: add task completion toggle button`

### Branch Strategy

- Feature branches: `feature/<descriptive-name>`
- Bug fix branches: `fix/<issue-description>`
- Main branch: `main` (protected, requires PR)

### Commit Process

Always follow this sequence:

```bash
# 1. Stage all changes
git add .

# 2. Commit with conventional format
git commit -m "feat: descriptive message"

# 3. Push to correct branch
git push origin <branch-name>
```

### Best Practices

- Keep commits focused and atomic
- Write clear, descriptive commit messages
- Reference issue numbers when applicable: `fix: resolve API timeout (#42)`
- Ensure all tests pass before pushing
- Review changes before committing
