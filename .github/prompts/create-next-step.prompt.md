---
description: "Assess project memory and create the next app development step as a GitHub Issue"
agent: "copilot-customization"
tools: ["search", "read", "edit", "execute", "web", "todo"]
---

# Create Next App Development Step

You are now in **copilot-customization** agent mode. Create a well-structured next development step by assessing project state and memory, then generate a comprehensive GitHub Issue following the app-development step template embedded in this prompt.

## Optional Inputs

${input:step-number:Step number to create, e.g. "5-3" or "6-0". Leave blank to infer the next step.}

${input:step-focus:Desired focus or title for the next step. Leave blank to infer from memory and current project state.}

${input:base-issue-number:Existing exercise issue number to inspect for continuity. Leave blank to auto-detect or create a standalone issue.}

## Goal

Generate a complete, actionable development step as a GitHub Issue. The step should be:
- **Focused**: One clear objective that can be completed and tested
- **Contextualized**: Connected to prior work and current project state
- **Actionable**: Clear instructions with concrete commands
- **Measurable**: Observable success criteria
- **Integrated**: Uses existing agents, prompts, and workflows

## Instructions

### Step 1: Gather Project Context

Collect information about the current project state:

**Read memory files if they exist** (optional - graceful if missing):
```bash
# Project workflow context
test -f .github/copilot-instructions.md && cat .github/copilot-instructions.md || echo "No project instructions found"
test -f .github/memory/session-notes.md && cat .github/memory/session-notes.md || echo "No session notes found"
test -f .github/memory/patterns-discovered.md && cat .github/memory/patterns-discovered.md || echo "No patterns file found"
test -f .github/memory/scratch/working-notes.md && cat .github/memory/scratch/working-notes.md || echo "No active notes found"
```

**Check for existing step files** (to infer numbering):
```bash
ls -la .github/steps/ 2>/dev/null || echo "No steps directory found"
```

**Inspect codebase state**:
```bash
# Check test status
npm test 2>/dev/null || echo "No tests configured"

# Check lint status
npm run lint 2>/dev/null || echo "No lint configured"

# Check Git state
git status
git log --oneline -5
```

### Step 2: Check GitHub Issue Context

If `${base-issue-number}` is provided, inspect it:

```bash
gh issue view ${base-issue-number} --comments
```

If no issue number is provided, look for open issues:

```bash
gh issue list --state open --limit 10
```

If there's an issue with "Exercise:" in the title, consider it as context for continuity.

### Step 3: Analyze and Decide

Based on the gathered context, determine:

1. **What's been completed**: From memory, git history, and issue context
2. **Current blockers or gaps**: Missing features, failing tests, quality issues
3. **Next logical step**: The smallest coherent increment that advances the project
4. **Workflow approach**: Which agents/prompts should execute, validate, test

**Prioritization criteria**:
- Failing tests → Fix them first
- Missing core features → Implement with TDD
- Code quality issues → Systematic cleanup
- New features → Plan with tests first
- Integration gaps → Connect components

**Step characteristics**:
- **Atomic**: One clear objective
- **Testable**: Observable completion criteria
- **Scoped**: Can be completed in one session
- **Sequential**: Builds on completed work

### Step 4: Determine Step Number and Title

**Step Number**:
- If `${step-number}` provided → use it
- Otherwise infer from existing step files (e.g., if 5-2 exists, next is 5-3)
- If no step files exist, start with `1-0`

**Title Format**: `Step X-Y: Clear Action-Oriented Title`

**Good titles**:
- "Step 5-1: Fix Failing Backend Tests"
- "Step 5-2: Resolve Lint Errors Systematically"
- "Step 5-3: Implement Todo Edit Feature with TDD"

**Bad titles**:
- "Step 5-1: Backend Work" (too vague)
- "Step 5-2: Fix Everything" (not focused)
- "Step 5-3: Improvements" (not actionable)

### Step 5: Generate the Issue Body Using This Template

Create the issue body using this comprehensive template structure. Fill in all bracketed placeholders with specific, contextual content based on your analysis.

```markdown
# Step X-Y: [Clear Action-Oriented Title]

## Goal

[One to three paragraphs explaining what this step accomplishes and why it matters now]

Example:
"Fix all failing backend API tests using Test-Driven Development. The backend has comprehensive tests that currently fail because implementations are incomplete or buggy. This step establishes a stable API foundation before adding frontend features."

**What success looks like**:
- [Specific measurable outcome 1]
- [Specific measurable outcome 2]
- [Specific measurable outcome 3]

## Background

[Context section that explains:]
- **Current state**: What's working, what's broken, what exists
- **Why now**: Why this step is the next logical increment
- **Prerequisites**: What was completed in previous steps (if applicable)
- **Constraints**: Any scope boundaries or limitations

Example:
"The backend API endpoints exist but fail their tests. Tests define the expected behavior (REST conventions, error handling, data validation). Before adding UI features, we need stable backend services that pass all quality checks."

> **Continuing from Step X-Y**: [Short continuity note if this follows another step]


## Instructions

> 🔄 **Fresh Start**: Before beginning, start a new chat (+ button) to give the agent clean context while leveraging project instructions.

### :keyboard: Activity: [Primary Activity Name]

[Brief explanation of what this activity accomplishes and how to approach it]

**Recommended approach**:
1. [Concrete action with specific command or file]
2. [Concrete action with specific command or file]
3. [Concrete action with specific command or file]
4. [Continue until objective is complete]

**Using automation** (if applicable):
- Run `/execute-step X-Y` to have AI autonomously execute these instructions
- AI will auto-switch to the appropriate agent (e.g., `tdd-developer`, `code-reviewer`)
- Review changes before proceeding

**Manual approach**:
- [Alternative step-by-step instructions for manual completion]

**IMPORTANT - Scope Boundary**:

This step focuses on [specific scope]. The agent should:
- ✅ [Specific allowed work item 1]
- ✅ [Specific allowed work item 2]
- ✅ [Specific allowed work item 3]
- ❌ [Specific out-of-scope work - what NOT to do]
- ❌ [Specific out-of-scope work - what NOT to do]

Example scope boundary:
"This step focuses ONLY on making tests pass. The AI should:
- ✅ Fix code to make failing tests pass
- ✅ Verify tests pass after each fix
- ❌ DO NOT fix linting errors (those are for Step 5-2)
- ❌ DO NOT add new features beyond test requirements"

### :keyboard: Activity: [Secondary Activity if needed]

[If the step requires multiple distinct activities, add another section]

### :keyboard: Activity: Validate and Progress

Standard validation and progression workflow:

1. **Validate completion** using automation:
   ```
   /validate-step X-Y
   ```
   - Checks that all success criteria are met
   - Provides ✅/❌ report with specific guidance

2. **Run required testing workflows** (if applicable):
   - If this step involves critical user journeys, run:
     ```
     /create-ui-tests
     /run-ui-tests
     ```
   - If UI testing is not required, state why (e.g., "Backend-only changes")

3. **Update memory** (REQUIRED):
   - Update `.github/memory/session-notes.md` with:
     - Date and step/feature name
     - What was accomplished
     - Key decisions made
     - Patterns discovered
     - What's next
   - Add reusable patterns to `.github/memory/patterns-discovered.md`
   - Use the memory tool to preserve context for future sessions

## Success Criteria

To complete this step successfully:

- ✅ [Observable criterion 1 - be specific about files, tests, or commands]
- ✅ [Observable criterion 2 - include actual verification command if possible]
- ✅ [Observable criterion 3 - state expected outcome clearly]
- ✅ [Observable criterion 4 - testing criterion if applicable]
- ✅ Memory updated in `.github/memory/session-notes.md` with accomplishments and next steps

Examples:
- ✅ All tests in `packages/backend/__tests__/app.test.js` pass (`npm test`)
- ✅ No ESLint errors in backend (`npm run lint` in `packages/backend/`)
- ✅ POST /api/todos endpoint returns 201 with created todo object
- ✅ UI tests cover create/edit/delete workflows (run `/create-ui-tests` and `/run-ui-tests`)
- ✅ Memory updated in `.github/memory/session-notes.md` with accomplishments and next steps

## Key Workflow Patterns

✨ **[Pattern Name 1]**: [Concise explanation of what pattern/principle applies]

✨ **[Pattern Name 2]**: [Concise explanation of what pattern/principle applies]

✨ **[Pattern Name 3]**: [Concise explanation of what pattern/principle applies]

Examples:
- ✨ **Test-Driven Development**: Tests define requirements, implementation makes them pass (Red-Green-Refactor)
- ✨ **Iterative Development**: Small, focused changes with continuous validation
- ✨ **AI-Assisted Analysis**: Using specialized agents (`tdd-developer`, `code-reviewer`) for domain-specific work
- ✨ **Workflow Automation**: Using prompts (`/execute-step`, `/validate-step`) for autonomous execution

---

```

### Step 6: Quality Checklist

Before creating the GitHub Issue, verify your draft:

**Structure**:
- ✅ Uses `# Step X-Y: Title` heading format
- ✅ Has all major sections: Goal, Background, Instructions, Success Criteria, Key Workflow Patterns
- ✅ Includes at least one `### :keyboard: Activity:` section
- ✅ Ends with a next-step handoff sentence

**Content Quality**:
- ✅ Goal section explains WHAT and WHY (not just what to do, but why it matters)
- ✅ Background provides context (current state, prerequisites, constraints)
- ✅ Activities have concrete commands or file references (not vague "implement X")
- ✅ Scope boundary clearly defines what IS and ISN'T in scope
- ✅ Success criteria are observable and verifiable (include actual commands to check)
- ✅ Key patterns explain the principles being applied

**Agent Integration**:
- ✅ Names appropriate agents or prompts for execution (`/execute-step`, `/validate-step`, etc.)
- ✅ Specifies which agent auto-switches happen (if using prompts)
- ✅ Includes memory update instructions in "Validate and Progress" activity

**Completeness**:
- ✅ Step is focused enough to complete in one session
- ✅ Step is testable with clear pass/fail criteria
- ✅ Step builds incrementally on prior work (if applicable)
- ✅ Step preserves scope boundaries for future increments
- ✅ Success criteria includes memory update requirement

### Step 7: Create the GitHub Issue

Write the issue body to a temporary file:

```bash
cat > /tmp/create-next-step-body.md << 'EOF'
[paste your generated step content here]
EOF
```

**Default: Create standalone issue**:
```bash
gh issue create \
  --title "Step X-Y: [Clear Action-Oriented Title]" \
  --body-file /tmp/create-next-step-body.md
```

**Alternative: Add as comment to existing issue** (if user explicitly requests):
```bash
gh issue comment ${base-issue-number} --body-file /tmp/create-next-step-body.md
```

### Step 8: Report Result

After creating the issue, provide this summary:

```markdown
✅ Created next step issue: [issue URL]

**Step**: X-Y
**Title**: [Title]
**Focus**: [One-sentence summary of what this step accomplishes]
**Basis**: [One-sentence summary of why this step is next, based on context analysis]

**Recommended next command**:
```
/execute-step X-Y
```

**Alternative manual approach**:
1. Open the issue: [issue URL]
2. Follow the instructions in the :keyboard: Activity sections
3. Run `/validate-step X-Y` when complete
```

## Template Philosophy

This template is designed to create steps that are:

1. **Self-Documenting**: Each step explains its context and rationale
2. **Executable**: Can be completed manually or with `/execute-step` automation
3. **Verifiable**: Success criteria are measurable and checkable
4. **Educational**: Key patterns explain principles being applied
5. **Incremental**: Focused scope enables steady progress
6. **Integrated**: Uses existing agents, prompts, and workflows

## Adaptability

This prompt works in any development context:

- **If memory files exist**: Use them for rich context
- **If memory files missing**: Infer from git history and codebase state
- **If agents exist**: Reference them in activities
- **If no agents**: Provide manual instructions
- **If prompts exist**: Use them for automation
- **If no prompts**: Provide terminal commands

The template structure remains the same; only the content adapts to the project.

## Context Sources

This prompt can leverage these files when available (all optional):

- **`.github/copilot-instructions.md`**: Project workflow conventions, agent guidelines, Git practices
- **`.github/memory/session-notes.md`**: Historical record of completed work
- **`.github/memory/patterns-discovered.md`**: Accumulated implementation patterns
- **`.github/memory/scratch/working-notes.md`**: Active session state
- **`.github/steps/*.md`**: Existing step files for numbering continuity
- **Git history**: Recent commits, current branch, test/lint status
- **GitHub Issues**: Open issues and comments for project continuity

**Graceful degradation**: If any file doesn't exist, the prompt infers from available sources. The embedded template ensures consistent step structure regardless of available context.

