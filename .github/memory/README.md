---
description: "Global workspace instructions for TODO application development"
---

# TODO Application - Copilot Instructions

## Project Context

This is a full-stack TODO application with a React frontend and Express backend. Development follows an iterative, feedback-driven approach with emphasis on quality and systematic validation.

**Current Phase**: Backend stabilization and frontend feature completion

**Key Characteristics**:
- Monorepo structure with separate frontend and backend packages
- Test-driven development methodology
- Multiple testing layers (unit, integration, UI automation)
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

- **Backend**: Jest + Supertest for API endpoint testing
- **Frontend**: React Testing Library for component unit and integration tests
- **UI Testing**: Playwright for critical user journey automation
- **Manual Testing**: Browser-based exploratory validation and visual checks

### Testing Philosophy

Combine fast feedback loops (unit/integration tests) with end-to-end quality confidence (UI automation). This multi-layer approach catches issues early while ensuring real-world user scenarios work correctly.

### Testing Approach by Context

**Backend API Changes**:
- Write Jest tests FIRST, then implement
- Follow strict RED-GREEN-REFACTOR cycle
- Test both success and error cases
- Validate request/response contracts

**Frontend Component Features**:
- Write React Testing Library tests FIRST for component behavior
- Follow strict RED-GREEN-REFACTOR cycle
- Test user interactions and state changes
- Follow with manual browser testing for full UI flows

**Critical User Journeys**:
- Create Playwright UI tests for end-to-end validation
- Focus on high-value user workflows
- Ensure tests are stable and maintainable

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

## Agent Usage

Use specialized agents for different types of work:

### tdd-developer Agent

**Use for**:
- Feature implementation with TDD cycles
- Unit and integration test authoring
- Backend API development
- Frontend component development
- Bug fixes with test-first approach

**Does NOT**:
- Create or run Playwright UI tests (use test-engineer instead)
- Handle lint-only issues (use code-reviewer instead)

### code-reviewer Agent

**Use for**:
- Addressing lint errors and warnings
- Code quality improvements
- Refactoring for better patterns
- Ensuring code standards compliance
- Style and consistency fixes

### test-engineer Agent

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

- **`session-notes.md`** (committed) - Historical summaries of completed development sessions
- **`patterns-discovered.md`** (committed) - Recurring code patterns and architectural decisions discovered through TDD
- **`scratch/working-notes.md`** (not committed) - Active session notes for real-time tracking

### Usage During Development

**During active work**:
- Take notes in `.github/memory/scratch/working-notes.md`
- Document current task, approach, findings, and decisions
- Track blockers and next steps

**At end of session**:
- Summarize key findings into `.github/memory/session-notes.md`
- Extract reusable patterns into `.github/memory/patterns-discovered.md`
- Clear or archive scratch notes for next session

**When providing guidance**:
- AI assistants reference these files for project-specific context
- Suggestions align with established patterns and past decisions
- Avoid repeating past mistakes or suggesting incompatible approaches

See [.github/memory/README.md](.github/memory/README.md) for comprehensive usage instructions.

## Workflow Utilities

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
