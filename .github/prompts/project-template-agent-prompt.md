# Agent Prompt - Create a Golden Path Project Template from an App Overview

Use this prompt when you have a `project-overview.md` for a new application and need an agent to create a repository template that follows the same platform-engineering architecture as this lab, adjusted for the new application's actual technology stack.

The goal is to generate a project scaffold and planning artifacts, not to implement production application code.

---

## Input Required

Before starting, read the new project's `project-overview.md` and extract these facts:

| Area | What to identify |
| --- | --- |
| Application type | API, frontend, worker, full-stack app, scheduled job, static site, etc. |
| Runtime stack | Node, Python, Java, Go, .NET, Ruby, or other runtime versions |
| Frontend stack | React, Vue, Angular, Next.js, static HTML, mobile client, or none |
| Backend stack | Express, FastAPI, Spring Boot, Gin, Rails, ASP.NET, or none |
| Package manager | npm, pnpm, yarn, pip, Poetry, Gradle, Maven, Go modules, etc. |
| Local ports | Frontend, backend, worker, database, or mock service ports |
| Deployment unit | Single container, multiple containers, static assets, serverless function, ECS service, etc. |
| Persistence | In-memory, database, queue, object storage, cache, or none |
| Required endpoints | Health checks, API routes, metrics routes, readiness/liveness probes |
| Cloud target | AWS ECS Fargate, Lambda, Kubernetes, static hosting, or other target |
| CI requirements | Lint, test, coverage, security scan, image build, infrastructure plan/apply |

If the overview does not specify one of these values, use a clearly named placeholder such as `<backend-port>` or `<package-manager>`. Ask a clarifying question only when the missing value blocks the scaffold shape.

---

## Agent Role

You are a platform-engineering scaffolding agent. Create a repository template that gives future teams a repeatable golden path for this application type.

Do not build business logic. Do not implement the real application. Use shell commands only for filesystem creation and placeholder files. The output should be a clear sequence of commands and generated Markdown/Terraform/workflow placeholder paths that another agent or developer can fill in later.

---

## Replication Strategy

Derive the new template from the project overview in this order.

### 1. Confirm the Target Shape

Summarize the application in one paragraph:

```text
This project is a <application-type> using <frontend-stack> and <backend-stack>. It runs locally on <ports>, is packaged as <deployment-units>, and targets <cloud-runtime> through the platform golden path.
```

Then list the main services:

```text
- frontend: <framework>, port <port>, build output <output-dir>
- backend: <framework>, port <port>, health path <path>
- worker: <runtime>, trigger <trigger>, if applicable
- persistence: <database/cache/queue/none>
```

### 2. Create the Repository Layout

Use the app overview to choose the correct package folders. Keep the same platform boundaries as this lab:

```text
docs/
context/
infra/
  modules/
  stacks/
    dev/
.github/
  workflows/
packages/
  <service-or-app-name>/
```

For a full-stack app, use:

```text
packages/frontend/
packages/backend/
```

For a single API service, use:

```text
packages/api/
```

For a worker-based system, use:

```text
packages/worker/
```

For a monolith, use:

```text
packages/app/
```

Example shell scaffold:

```bash
mkdir -p docs context infra/modules infra/stacks/dev .github/workflows packages
mkdir -p packages/<service-name>
touch README.md LOCAL-SETUP.md
touch docs/project-overview.md docs/functional-requirements.md docs/coding-guidelines.md docs/testing-guidelines.md
touch context/iac-requirements.md context/ci-requirements.md
touch infra/stacks/dev/main.tf infra/stacks/dev/terraform.tfvars
touch .github/workflows/golden-path-ci.yml .github/workflows/<project-name>-ci.yml
```

Adjust the `packages/` directories to match the actual stack from the overview.

### 3. Create Documentation Placeholders

Create the same documentation set, but rewrite each file for the new stack.

Required docs:

```text
docs/project-overview.md
docs/functional-requirements.md
docs/coding-guidelines.md
docs/testing-guidelines.md
context/iac-requirements.md
context/ci-requirements.md
LOCAL-SETUP.md
README.md
```

Each file should contain headings and TODO placeholders, not final implementation details, unless the overview explicitly provides them.

Use this mapping:

| Source from overview | Write into |
| --- | --- |
| Architecture, ports, service boundaries | `docs/project-overview.md` |
| API routes, user-visible behavior, platform outcomes | `docs/functional-requirements.md` |
| Runtime conventions, formatting, naming, error handling | `docs/coding-guidelines.md` |
| Unit/integration/e2e expectations and coverage | `docs/testing-guidelines.md` |
| Cloud target, Terraform module inputs, state backend | `context/iac-requirements.md` |
| CI jobs, required checks, artifact/image publishing | `context/ci-requirements.md` |
| Required local tools and setup commands | `LOCAL-SETUP.md` |
| Short entrypoint and exercise navigation | `README.md` |

### 4. Select the Infrastructure Pattern

Choose the infrastructure path from the deployment target in the overview.

Use this decision table:

| New app deployment target | Template shape |
| --- | --- |
| ECS Fargate service | `infra/stacks/dev` calls an ECS app module |
| Static frontend only | `infra/stacks/dev` calls a static hosting/CDN module |
| Serverless API | `infra/stacks/dev` calls an API Gateway/Lambda module |
| Kubernetes workload | `infra/stacks/dev` calls a cluster/workload module or Helm release |
| Worker/queue app | `infra/stacks/dev` calls worker, queue, and IAM modules |
| Unknown | create placeholders and mark module selection as TODO |

For this lab's architecture, the expected pattern is ECS Fargate behind an ALB. For a new project, keep the same golden-path idea but adapt the module inputs to the actual runtime, ports, container count, and health check path.

Shell-only placeholder creation:

```bash
mkdir -p infra/stacks/dev
touch infra/stacks/dev/main.tf infra/stacks/dev/variables.tf infra/stacks/dev/outputs.tf infra/stacks/dev/terraform.tfvars
```

Do not write provider credentials or secrets into Terraform files.

### 5. Select the CI/CD Pattern

Create a reusable workflow plus a caller workflow:

```text
.github/workflows/golden-path-ci.yml
.github/workflows/<project-name>-ci.yml
```

The reusable workflow should be designed around the new stack:

| Stack | Likely CI commands |
| --- | --- |
| Node/npm | `npm ci`, `npm run lint`, `npm test`, `npm run build` |
| Node/pnpm | `pnpm install --frozen-lockfile`, `pnpm lint`, `pnpm test`, `pnpm build` |
| Python/Poetry | `poetry install`, `poetry run ruff check`, `poetry run pytest` |
| Java/Gradle | `./gradlew test build` |
| Java/Maven | `mvn test package` |
| Go | `go test ./...`, `go vet ./...`, `go build ./...` |
| .NET | `dotnet restore`, `dotnet test`, `dotnet publish` |

Required reusable workflow jobs should usually include:

```text
lint
test
security-scan
terraform-plan
docker-build or artifact-build
build-and-push, if the app publishes container images
terraform-apply, if the golden path deploys infrastructure from CI
```

Caller workflow requirements:

```text
- trigger on pull requests
- trigger on push to main
- call the reusable workflow
- pass project-specific runtime versions
- declare least-privilege permissions
- request id-token: write when OIDC cloud auth is needed
```

### 6. Add Local Setup Guidance

Generate `LOCAL-SETUP.md` from the overview's stack.

Include only tools the new project actually needs:

```text
- language runtime and version
- package manager
- Terraform, if infrastructure is included
- cloud CLI, if deployment is included
- Docker, if images are built locally
- security scanners, if used in CI
```

Add shell commands as placeholders:

```bash
<install-runtime-command>
<install-dependencies-command>
<run-tests-command>
<start-local-dev-command>
<validate-infra-command>
```

### 7. Add Acceptance Criteria

Create acceptance criteria that match the new app instead of copying this repo verbatim.

Use this structure:

```text
FR-1: Infrastructure as Code
FR-2: CI/CD Pipeline
FR-3: Deployment and Release
FR-4: Observability
FR-5: Pull Request and Adoption Documentation
```

Only include criteria that make sense for the new app. For example, do not require frontend Docker builds for an API-only service, and do not require Terraform apply for a template that intentionally stops at plan.

### 8. Add Validation Commands

End the scaffold with a validation section. Choose commands based on the actual stack.

For a Node full-stack app:

```bash
npm install
npm test --workspaces
npm run lint --workspaces
terraform -chdir=infra/stacks/dev init -backend=false
terraform -chdir=infra/stacks/dev validate
docker build -f packages/backend/Dockerfile packages/backend
docker build -f packages/frontend/Dockerfile packages/frontend
```

For a Python API:

```bash
poetry install
poetry run ruff check .
poetry run pytest
terraform -chdir=infra/stacks/dev init -backend=false
terraform -chdir=infra/stacks/dev validate
docker build -f packages/api/Dockerfile packages/api
```

For Go:

```bash
go mod download
go test ./...
go vet ./...
terraform -chdir=infra/stacks/dev init -backend=false
terraform -chdir=infra/stacks/dev validate
docker build -f packages/api/Dockerfile packages/api
```

Use placeholders when the overview does not define the exact command.

---

## Shell-Only Execution Contract

When executing this prompt, the agent must follow these limits:

```text
- Use shell commands only to create directories and placeholder files.
- Do not implement application source code.
- Do not install dependencies unless explicitly asked.
- Do not run generators that create large framework apps unless explicitly asked.
- Do not create secrets, credentials, or cloud resources.
- Do not run Terraform apply.
- Do not hardcode account IDs, role ARNs, API keys, or passwords.
- Prefer placeholders where project-specific details are missing.
```

Allowed commands include:

```bash
mkdir -p <path>
touch <path>
find . -maxdepth <n> -type f | sort
tree -a -I '<ignore-pattern>'
```

Avoid commands that write full application implementations. If file contents are needed, create lightweight Markdown placeholders and TODOs only.

---

## Final Output Required from the Agent

After scaffolding, report:

```text
1. The inferred architecture from project-overview.md
2. The created folder structure
3. The docs and context files created
4. The stack-specific substitutions made
5. Any assumptions or placeholders left for the developer
6. The next recommended agent prompt, such as:
   - fill in IaC requirements
   - generate CI workflow
   - add service implementation
   - add tests
   - prepare PR description
```

Do not claim the project is production-ready. The output is a template scaffold ready for the next agent or developer step.
