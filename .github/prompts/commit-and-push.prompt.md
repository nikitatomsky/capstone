---
description: "Analyze changes, generate commit message, and push to feature branch"
mode: "agent"
tools: ['read', 'execute', 'todo']
---

# Commit and Push Workflow

You will analyze the current code changes, generate a conventional commit message, and push to a feature branch.

## Required Input

Branch name: ${input:branch-name:Enter the feature branch name (e.g., feature/webhook-validation)}

**CRITICAL**: Never commit directly to `main` branch. Always use the provided feature branch name.

## Workflow Steps

### 1. Pre-Commit Validation

Before committing, ensure code quality:

```bash
# Run linter to check for errors
cd packages/api
poetry run ruff check .

# Run all tests to ensure nothing is broken
poetry run pytest

# Check coverage (optional but recommended)
poetry run pytest --cov=app --cov-report=term-missing
```

**STOP if**:
- ❌ Linting errors exist (fix with `poetry run ruff check --fix .` or manually)
- ❌ Tests are failing (fix the tests or code first)
- ❌ Critical coverage gaps introduced

**PROCEED if**:
- ✅ All lint checks pass
- ✅ All tests pass
- ✅ Coverage is acceptable

### 2. Analyze Changes

Review what has changed:

```bash
# Show changed files
git status

# Review actual changes
git diff

# Show summary of changes
git diff --stat
```

Understand:
- What files were modified?
- What functionality was added/changed/fixed?
- What is the scope of the changes?

### 3. Generate Conventional Commit Message

Based on the changes, create a commit message following the conventional commit format:

**Format**: `<type>: <description>`

**Types**:
- `feat:` - New feature (e.g., "feat: add LLM extraction service")
- `fix:` - Bug fix (e.g., "fix: handle missing fields in webhook validation")
- `test:` - Test additions or modifications (e.g., "test: add integration tests for incomplete intake flow")
- `refactor:` - Code refactoring without behavior change (e.g., "refactor: extract storage interface")
- `chore:` - Maintenance tasks (e.g., "chore: update dependencies")
- `docs:` - Documentation changes (e.g., "docs: update API endpoint documentation")

**Examples**:
```
feat: implement POST /webhook endpoint with Telegram payload validation
fix: correct Pydantic validation for required IntakeRecord fields
test: add pytest tests for LLM extraction service with mocked responses
refactor: split webhook handler into extraction and validation layers
chore: configure Ruff linting rules for project
docs: add setup instructions for ngrok webhook tunnel
```

**Guidelines**:
- Keep description concise but descriptive
- Use present tense ("add" not "added")
- Don't capitalize first letter after colon
- No period at the end
- Reference issue number if applicable (e.g., "feat: add webhook endpoint (#42)")

### 4. Branch Management

Handle branch creation or switching:

```bash
# Check current branch
git branch --show-current

# Create and switch to feature branch (if it doesn't exist)
git checkout -b ${input:branch-name}

# OR switch to existing branch
git checkout ${input:branch-name}
```

**Verify**: Ensure you are NOT on `main` branch:
```bash
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" = "main" ]; then
    echo "ERROR: Cannot commit to main branch!"
    exit 1
fi
```

### 5. Stage and Commit

Stage all changes and commit with the generated message:

```bash
# Stage all changes
git add .

# Commit with conventional message
git commit -m "<type>: <description>"

# Example:
# git commit -m "feat: implement webhook validation with Pydantic schemas"
```

### 6. Push to Remote

Push the committed changes to the feature branch:

```bash
# Push to feature branch
git push origin ${input:branch-name}

# If first push, set upstream tracking
git push -u origin ${input:branch-name}
```

### 7. Confirm Success

Verify the push was successful:

```bash
# Show last commit
git log -1 --oneline

# Show remote tracking
git branch -vv
```

## Output Summary

After completing the workflow, provide a summary:

```markdown
✅ **Commit and Push Complete**

**Branch**: ${input:branch-name}
**Commit Message**: <type>: <description>
**Files Changed**: <count> files
**Tests**: ✅ Passing
**Lint**: ✅ Clean

**Next Steps**:
- Review changes on GitHub
- Create Pull Request when ready
- Ensure CI/CD pipeline passes
```

## Error Handling

If any step fails:

**Linting Errors**:
```bash
# Auto-fix safe issues
poetry run ruff check --fix .

# Or fix manually and re-run
poetry run ruff check .
```

**Test Failures**:
```bash
# Run tests with verbose output
poetry run pytest -vv

# Debug specific test
poetry run pytest tests/test_webhook.py::test_name -vv
```

**Merge Conflicts**:
```bash
# Pull latest changes from main
git checkout main
git pull origin main

# Rebase feature branch
git checkout ${input:branch-name}
git rebase main

# Resolve conflicts manually, then continue
git rebase --continue
```

**Push Rejected** (remote has changes):
```bash
# Pull remote changes
git pull origin ${input:branch-name} --rebase

# Then push again
git push origin ${input:branch-name}
```

## Safety Checks

**Before pushing, verify**:
- ✅ Not on `main` branch
- ✅ All tests pass
- ✅ No lint errors
- ✅ Commit message follows conventions
- ✅ Changes are intentional and complete
- ✅ No sensitive data (API keys, tokens) in commit

**Never**:
- ❌ Commit directly to `main`
- ❌ Force push (`git push -f`) without understanding impact
- ❌ Commit secrets or credentials
- ❌ Push untested code
- ❌ Use generic commit messages ("fix stuff", "wip")

## Example Complete Workflow

```bash
# 1. Validate code quality
cd packages/api
poetry run ruff check .
poetry run pytest

# 2. Review changes
git status
git diff

# 3. Create/switch to feature branch
git checkout -b feature/webhook-validation

# 4. Stage and commit
git add .
git commit -m "feat: add Pydantic validation for Telegram webhook payloads"

# 5. Push to remote
git push -u origin feature/webhook-validation

# 6. Confirm
git log -1 --oneline
```

## Integration with Project Workflow

This prompt follows the project's Git workflow:

**From `.github/copilot-instructions.md`**:
- Uses conventional commit format
- Creates feature branches (`feature/<name>`)
- Never commits to `main` directly
- Ensures tests pass before pushing
- Validates code quality with linting

**Memory Integration**:
After successful commit, consider updating `.github/memory/session-notes.md` with:
- What was accomplished
- What was committed
- Next steps

---

**Remember**: Quality over speed. A clean, tested commit is better than a rushed, broken one.
