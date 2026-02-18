# AWS Bedrock-Based Claude Code Alternative

## Goal

Build a self-hosted AWS Bedrock agent system that **replaces Claude Code in the cloud**:

1. **User provides initial prompt** → Agent processes it
2. **Agent creates structured prompt** → User reviews and approves
3. **Agent generates plan** → User reviews and approves
4. **Agent creates todos** → User reviews and approves
5. **Agent asks clarifying questions** along the way
6. **Upon approval**, agent executes work on specified git repository
7. **Creates branches and code** (like Claude Code's `claude/*` branches)
8. **All running on AWS infrastructure** using Bedrock
9. **Accessible from anywhere** - iPhone, web browser, desktop

## Why This Approach?

- **Replace Claude Code**: Same workflow, your infrastructure
- **Access anywhere**: Web UI accessible from iPhone, desktop, any browser
- **Self-hosted**: Run on your own AWS account
- **Customizable**: Use your own templates and workflows
- **Multi-repository**: Work with repos containing submodules
- **Cost control**: Pay only for what you use
- **Integration**: Connect to your existing AWS infrastructure
- **Audit trail**: Full logging in CloudWatch

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│  (CLI tool or Web UI - interacts with user via prompts)     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                     Bedrock Agent                            │
│  • Orchestrates workflow (prompt → plan → todo → execute)   │
│  • Asks clarifying questions                                 │
│  • Maintains conversation context                            │
│  • Uses Knowledge Base for templates & codebase patterns    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    Action Groups                             │
│  • template_processor (morph prompt → structured)           │
│  • plan_generator (structured → plan.md)                    │
│  • todo_generator (plan → todos)                            │
│  • git_operations (clone, branch, commit, push)             │
│  • file_operations (read, write, edit)                      │
│  • code_generator (implement todos)                         │
│  • approval_handler (get user confirmation)                 │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Execution Environment (ECS Fargate)             │
│  Container with:                                             │
│  • Git + GitHub CLI                                          │
│  • Python 3.13 + Node.js 22                                  │
│  • Code quality tools (black, eslint, pytest)                │
│  • FastAPI server exposing git/file operations               │
│  • EFS mount for persistent repos                            │
└─────────────────────────────────────────────────────────────┘
```

## Detailed Workflow

### Phase 1: Initial Prompt Processing

**User Input:**
```
"Add passwordless authentication to the web app using email magic links"
```

**Agent Action:**
1. Receives prompt
2. Calls `template_processor` action group
3. Uses prompt-template.md from knowledge base
4. Generates structured prompt with:
   - Context understanding
   - Requirements breakdown
   - Technical considerations
   - Questions for clarification

**User Review:**
```
Generated Structured Prompt:
---
## Context
User wants to add passwordless authentication to web app

## Requirements
- Email-based magic link authentication
- Replace or supplement existing auth?
- Session management approach

## Questions
1. Should this replace current auth or add as option?
2. Which email service? (AWS SES, SendGrid, etc.)
3. Link expiration time?
...

[Approve] [Edit] [Reject]
```

### Phase 2: Plan Generation

**Agent Action (after approval):**
1. Calls `plan_generator` action group
2. Uses plan-template.md from knowledge base
3. Calls `git_operations.explore_codebase` to understand current structure
4. Generates plan with:
   - Architecture decisions
   - Files to modify/create
   - Dependencies needed
   - Testing strategy

**User Review:**
```
Generated Plan:
---
## Architecture
- Use AWS SES for email delivery
- Store magic tokens in DynamoDB with TTL
- JWT session tokens after verification

## Files to Modify
- web/src/components/Auth/Login.tsx
- api-dynamo/app/auth/magic_link.py
- infra/pulumi/ses.py

## Implementation Steps
1. Add SES infrastructure (infra/)
2. Create magic link API endpoint (api-dynamo/)
3. Build magic link UI (web/)
4. Add tests
...

[Approve] [Edit] [Reject]
```

### Phase 3: Todo Generation

**Agent Action (after approval):**
1. Calls `todo_generator` action group
2. Uses todo-template.md from knowledge base
3. Breaks plan into actionable tasks
4. Estimates complexity/dependencies

**User Review:**
```
Generated Todos:
---
INFRA TASKS:
- [ ] Add SES domain verification to infra/pulumi/ses.py
- [ ] Create DynamoDB table for magic tokens with TTL
- [ ] Deploy infra to dev environment

API TASKS:
- [ ] Create magic_link.py with generate_token()
- [ ] Add POST /auth/magic-link endpoint
- [ ] Add GET /auth/verify-magic-link endpoint
- [ ] Add tests for magic link flow

WEB TASKS:
- [ ] Create MagicLinkLogin.tsx component
- [ ] Add "Email me a login link" UI
- [ ] Handle magic link verification route
- [ ] Add loading states and error handling

TESTING:
- [ ] Integration test for full flow
- [ ] Email delivery verification in dev
...

[Approve] [Edit] [Reject]
```

### Phase 4: Execution

**Agent Action (after approval):**
1. Asks for repository URL and target branch
2. Calls `git_operations.clone` with submodules
3. Creates feature branch (e.g., `topic/passwordless-auth`)
4. For each todo:
   - Reads relevant files
   - Generates code changes
   - Writes/edits files
   - Runs tests
   - Updates todo status
5. Commits changes with descriptive messages
6. Pushes to remote
7. Optionally creates PR

**Execution Log:**
```
✓ Cloned repository: traillensdev (with submodules)
✓ Created branch: topic/passwordless-auth
✓ [1/12] Added SES domain verification to infra/pulumi/ses.py
✓ [2/12] Created DynamoDB table for magic tokens
  [3/12] Deploying infra to dev environment...
    Running: cd infra && pulumi up --stack dev
    ✓ Deployed successfully
✓ [4/12] Created magic_link.py...
...
✓ [12/12] Integration tests passing
✓ Committed changes (5 commits)
✓ Pushed to origin/topic/passwordless-auth
✓ Created PR #123

Summary:
- Files modified: 8
- Files created: 3
- Tests added: 12
- All tests passing ✓
```

## Component Details

### 1. User Interfaces

#### Web UI (Primary Interface - iPhone, Desktop, Any Browser)

**Technology:** React + Vite hosted on AWS Amplify or CloudFront + S3

**Access:** `https://code.traillenshq.com` (or custom domain)

**Features:**
- **Responsive design**: Works perfectly on iPhone, iPad, desktop
- **Real-time updates**: WebSocket connection for live progress
- **Session management**: Resume from any device
- **Approval workflow**: Interactive UI for prompt/plan/todo review
- **Code preview**: View generated code before execution
- **Dark mode**: For mobile and desktop
- **Authentication**: Cognito (same as TrailLens)

**Mobile Experience (iPhone):**
```
┌─────────────────────────┐
│  🤖 TrailLens Agent     │
│                         │
│ ┌─────────────────────┐ │
│ │ New Task            │ │
│ │ "Add passwordless   │ │
│ │  auth to web app"   │ │
│ │                     │ │
│ │      [Start] →      │ │
│ └─────────────────────┘ │
│                         │
│ Recent Sessions:        │
│ • Passwordless auth     │
│   (In progress)         │
│ • Dark mode feature     │
│   (Completed)           │
│                         │
└─────────────────────────┘
```

**Web UI Architecture:**
```
┌────────────────────────────────────────────┐
│           CloudFront + S3 / Amplify        │
│  (Static React App - code.traillenshq.com) │
└──────────────┬─────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────┐
│          API Gateway + WebSocket            │
│  (wss://api.code.traillenshq.com)          │
└──────────────┬─────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────┐
│         Lambda (WebSocket Handler)          │
│  - Connects to Bedrock Agent                │
│  - Pushes updates to browser                │
│  - Handles approvals                        │
└──────────────┬─────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────┐
│           Bedrock Agent                     │
│  (Orchestrates workflow)                    │
└─────────────────────────────────────────────┘
```

#### CLI Tool (Optional - Advanced Users)

**Technology:** Python CLI using `click` or `typer`

```bash
# Installation
pip install traillens-bedrock-agent

# Usage
tb-agent init                    # Configure AWS credentials, agent ID
tb-agent start "Add feature X"   # Start new workflow
tb-agent resume <session-id>     # Resume previous session
tb-agent status                  # Check current progress
```

**Features:**
- Interactive prompts for approvals
- Real-time progress display
- Ability to pause/resume sessions
- Session history
- Configuration management

**Note:** CLI and Web UI share the same backend, so you can start on iPhone and resume on desktop CLI.

### 2. Bedrock Agent Configuration

**Agent Instructions:**
```
You are a software development assistant that follows a structured workflow:

1. PROMPT PHASE: Transform user's initial request into a structured prompt
   - Use prompt-template.md format
   - Ask clarifying questions
   - Wait for user approval before proceeding

2. PLAN PHASE: Create detailed implementation plan
   - Use plan-template.md format
   - Explore codebase to understand structure
   - Identify files to modify/create
   - Wait for user approval before proceeding

3. TODO PHASE: Break plan into actionable tasks
   - Use todo-template.md format
   - Create specific, testable tasks
   - Wait for user approval before proceeding

4. EXECUTION PHASE: Implement the todos
   - Clone repository with submodules
   - Create feature branch
   - Implement each todo sequentially
   - Run tests after each change
   - Commit with descriptive messages
   - Push and optionally create PR

Always ask for user approval between phases.
Always provide clear status updates during execution.
Follow coding standards from CLAUDE.md files.
```

**Action Groups:**

1. **template_processor**
   - Lambda → Bedrock API call to process with template
   - Returns structured prompt

2. **plan_generator**
   - Lambda → Calls container to explore codebase
   - Lambda → Bedrock API to generate plan
   - Returns plan in markdown format

3. **todo_generator**
   - Lambda → Bedrock API to convert plan to todos
   - Returns todo list

4. **git_operations**
   - Lambda → Container API
   - Operations: clone, branch, commit, push, pr_create

5. **file_operations**
   - Lambda → Container API
   - Operations: read, write, edit, search

6. **code_generator**
   - Lambda → Bedrock API to generate code
   - Returns code changes

7. **approval_handler**
   - Lambda → DynamoDB to store pending approval
   - Lambda → SNS to notify user (optional)
   - Returns approval status

**Knowledge Base:**
- prompt-template.md
- plan-template.md
- todo-template.md
- CLAUDE.md files from repositories
- CONSTITUTION*.md files
- Codebase documentation

### 3. Container Environment

**Dockerfile:**
```dockerfile
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    python3.13 \
    python3-pip \
    nodejs \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install gh -y

# Install Python tools
RUN pip3 install fastapi uvicorn black isort flake8 pytest

# Install Node.js tools
RUN npm install -g eslint prettier

# Setup workspace
RUN mkdir -p /workspace/repos /workspace/cache /workspace/logs
WORKDIR /workspace

# Copy API server
COPY api_server /app/api_server
WORKDIR /app

# Expose API
EXPOSE 8080

# Run API server
CMD ["uvicorn", "api_server.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**API Server (FastAPI):**
```python
# api_server/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import os

app = FastAPI()

class CloneRequest(BaseModel):
    repo_url: str
    branch: str = "main"
    with_submodules: bool = True

@app.post("/git/clone")
async def clone_repo(req: CloneRequest):
    """Clone repository with optional submodules"""
    try:
        cmd = ["git", "clone"]
        if req.with_submodules:
            cmd.extend(["--recurse-submodules"])
        cmd.extend([req.repo_url, f"/workspace/repos/{repo_name}"])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)

        return {"status": "success", "path": f"/workspace/repos/{repo_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/git/branch")
async def create_branch(repo_name: str, branch_name: str):
    """Create and checkout new branch"""
    # Implementation...

@app.post("/file/read")
async def read_file(repo_name: str, file_path: str):
    """Read file from repository"""
    # Implementation...

@app.post("/file/write")
async def write_file(repo_name: str, file_path: str, content: str):
    """Write content to file"""
    # Implementation...

@app.post("/code/test")
async def run_tests(repo_name: str, test_path: str = None):
    """Run tests in repository"""
    # Implementation...

# Additional endpoints for git operations, code quality checks, etc.
```

### 4. State Management

**DynamoDB Tables:**

**sessions_table:**
```
partition_key: session_id (string)
attributes:
  - user_id
  - status (prompt|plan|todo|executing|completed|failed)
  - current_phase
  - repository_url
  - branch_name
  - created_at
  - updated_at
  - metadata (JSON)
```

**approvals_table:**
```
partition_key: approval_id (string)
attributes:
  - session_id
  - phase (prompt|plan|todo)
  - content (JSON)
  - status (pending|approved|rejected)
  - user_feedback
  - created_at
```

**todos_table:**
```
partition_key: session_id (string)
sort_key: todo_id (number)
attributes:
  - description
  - status (pending|in_progress|completed|failed)
  - files_modified
  - commit_hash
  - error_message
```

### 5. GitHub Integration

**Secrets Manager:**
```
secret: github/pat
value: {
  "token": "ghp_xxx...",
  "username": "your-username"
}
```

**Branch Naming:**
```
topic/bedrock-<feature-description>
# Example: topic/bedrock-passwordless-auth
```

**Commit Messages:**
```
Add passwordless authentication with magic links

- Added SES infrastructure for email delivery
- Created magic token storage in DynamoDB
- Implemented magic link API endpoints
- Added magic link UI components

Automated-By: TrailLens Bedrock Agent
Session-ID: session-abc123
```

**PR Creation:**
```bash
gh pr create \
  --title "Add passwordless authentication" \
  --body "$(cat PR_DESCRIPTION.md)" \
  --label "bedrock-agent" \
  --label "automated"
```

## User Interaction Flow

### Web UI Session Example (iPhone/Desktop)

**Step 1: Start New Session**
```
┌──────────────────────────────────────────────────┐
│ 🤖 TrailLens Code Agent                          │
├──────────────────────────────────────────────────┤
│                                                  │
│  What would you like to build?                   │
│  ┌────────────────────────────────────────────┐  │
│  │ Add passwordless authentication to web app │  │
│  │ using email magic links                    │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  Repository:                                     │
│  ┌────────────────────────────────────────────┐  │
│  │ TrailLensCo/traillensdev            [▼]   │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│                       [Start Session] →          │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Step 2: Agent Asks Questions**
```
┌──────────────────────────────────────────────────┐
│ 📝 Clarifying Questions                          │
├──────────────────────────────────────────────────┤
│                                                  │
│  ❓ Should this replace current auth or add as  │
│     an additional option?                        │
│                                                  │
│  ○ Replace current authentication               │
│  ● Add as optional method (recommended)          │
│  ○ Other                                         │
│                                                  │
│  ❓ Which email service should we use?          │
│                                                  │
│  ● AWS SES (recommended)                         │
│  ○ SendGrid                                      │
│  ○ Other                                         │
│                                                  │
│  ❓ How long should magic links be valid?       │
│                                                  │
│  ┌──────┐ minutes                                │
│  │  15  │                                        │
│  └──────┘                                        │
│                                                  │
│                            [Continue] →          │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Step 3: Review Structured Prompt**
```
┌──────────────────────────────────────────────────┐
│ 📋 Structured Prompt                             │
├──────────────────────────────────────────────────┤
│                                                  │
│  ## Context                                      │
│  Add passwordless authentication using email     │
│  magic links to TrailLens web app                │
│                                                  │
│  ## Requirements                                 │
│  - Implement as optional authentication method   │
│  - Use AWS SES for email delivery                │
│  - Magic links valid for 15 minutes              │
│  - Store tokens in DynamoDB with TTL             │
│                                                  │
│  ## Technical Approach                           │
│  - Backend: FastAPI endpoints                    │
│  - Frontend: React components                    │
│  - Infrastructure: DynamoDB + SES                │
│                                [View Full ↓]     │
│                                                  │
│  [← Back]  [Edit]          [Approve] →          │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Step 4: Review Implementation Plan**
```
┌──────────────────────────────────────────────────┐
│ 📐 Implementation Plan                           │
├──────────────────────────────────────────────────┤
│                                                  │
│  ✓ Phase 1: Infrastructure (infra/)              │
│    - Add DynamoDB table for tokens               │
│    - Configure SES                               │
│                                                  │
│  ✓ Phase 2: API (api-dynamo/)                    │
│    - Create magic link endpoints                 │
│    - Add email sending logic                     │
│    - Add tests                                   │
│                                                  │
│  ✓ Phase 3: Web (web/)                           │
│    - Create MagicLinkLogin component             │
│    - Add verification route                      │
│    - Update Login UI                             │
│                                [View Full ↓]     │
│                                                  │
│  Estimated: 8 files • 12 tasks                   │
│                                                  │
│  [← Back]  [Edit]          [Approve] →          │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Step 5: Review Todos**
```
┌──────────────────────────────────────────────────┐
│ ✅ Todo List (12 tasks)                          │
├──────────────────────────────────────────────────┤
│                                                  │
│  INFRA                                           │
│  □ Add magic_link_tokens DynamoDB table          │
│  □ Deploy infra to dev environment               │
│                                                  │
│  API                                             │
│  □ Create app/auth/magic_link.py                 │
│  □ Add email sending function using SES          │
│  □ Add POST /auth/magic-link endpoint            │
│  □ Add GET /auth/verify/:token endpoint          │
│  □ Add tests for magic link flow                 │
│                                                  │
│  WEB                                             │
│  □ Create MagicLinkLogin component               │
│  □ Add /auth/verify/:token route                 │
│  □ Update Login with magic link option           │
│                                [View All ↓]      │
│                                                  │
│  [← Back]  [Edit]       [Execute] →             │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Step 6: Live Execution Progress**
```
┌──────────────────────────────────────────────────┐
│ 🚀 Executing: topic/bedrock-passwordless-auth    │
├──────────────────────────────────────────────────┤
│                                                  │
│  ✓ Cloned repository with submodules             │
│  ✓ Created branch: topic/bedrock-passwordless-…  │
│                                                  │
│  ⚙️ [3/12] Creating app/auth/magic_link.py...   │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ ▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░ 25%        │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  Recent activity:                                │
│  ✓ Added DynamoDB table definition               │
│  ✓ Deployed to dev environment                   │
│  ⚙️ Writing magic_link.py...                     │
│                                                  │
│  [View Logs]                        [Pause]      │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Step 7: Completion & PR**
```
┌──────────────────────────────────────────────────┐
│ ✅ Execution Complete                            │
├──────────────────────────────────────────────────┤
│                                                  │
│  🎉 All 12 tasks completed successfully!         │
│                                                  │
│  Summary:                                        │
│  • Files created: 3                              │
│  • Files modified: 5                             │
│  • Tests added: 8                                │
│  • All tests passing ✓                           │
│                                                  │
│  Branch: topic/bedrock-passwordless-auth         │
│  Commits: 5                                      │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ 📝 View Changes                            │  │
│  ├────────────────────────────────────────────┤  │
│  │ + infra/pulumi/dynamodb.py                 │  │
│  │ + api-dynamo/app/auth/magic_link.py        │  │
│  │ + web/src/components/Auth/MagicLink…       │  │
│  │   ... 5 more files                         │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  [View Code]  [Create Pull Request] →           │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Notifications:**
- Push notification to iPhone when waiting for approval
- Real-time updates during execution
- Email when PR is created

### Terminal Session Example (CLI)

```
$ tb-agent start "Add passwordless auth to web app"

🤖 TrailLens Bedrock Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Processing your request...

I'll help you add passwordless authentication. Let me ask a few questions:

❓ Should this replace the current authentication or be an additional option?
   1. Replace current auth
   2. Add as optional method (recommended)
   3. Other

> 2

❓ Which email service should we use?
   1. AWS SES (recommended - already in infrastructure)
   2. SendGrid
   3. Other

> 1

❓ How long should magic links be valid?
   Enter minutes (default: 15):

> 15

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 STRUCTURED PROMPT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Context
Add passwordless authentication using email magic links to TrailLens web app

## Requirements
- Implement as optional authentication method alongside existing auth
- Use AWS SES for email delivery
- Magic links valid for 15 minutes
- Store tokens in DynamoDB with TTL
- Maintain session after verification

## Technical Approach
- Backend: FastAPI endpoints for link generation and verification
- Frontend: React components for email input and verification
- Infrastructure: DynamoDB table with TTL, SES configuration

## Questions Answered
1. Auth method: Optional (not replacing existing)
2. Email service: AWS SES
3. Link expiration: 15 minutes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Do you approve this structured prompt?
[A]pprove  [E]dit  [R]eject

> A

✓ Prompt approved

📋 Generating implementation plan...
🔍 Exploring codebase structure...
   - Analyzed web/ submodule
   - Analyzed api-dynamo/ submodule
   - Analyzed infra/ submodule
✓ Plan generated

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📐 IMPLEMENTATION PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Phase 1: Infrastructure (infra/)
- Add DynamoDB table: magic_link_tokens
  - Partition key: token_id
  - TTL attribute: expires_at
  - GSI: email lookup
- Configure SES if not already done

## Phase 2: API (api-dynamo/)
- Create app/auth/magic_link.py
  - generate_magic_link(email) → sends email, stores token
  - verify_magic_link(token) → validates, creates session
- Add routes to app/main.py
- Add tests: tests/auth/test_magic_link.py

## Phase 3: Web (web/)
- Create src/components/Auth/MagicLinkLogin.tsx
- Add route: /auth/verify/:token
- Update Login.tsx to include magic link option
- Add loading/error states

## Phase 4: Testing & Deployment
- Integration tests
- Deploy infra to dev
- Test in dev environment
- Ready for review

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Do you approve this plan?
[A]pprove  [E]dit  [R]eject  [Q]uestions

> A

✓ Plan approved

📋 Generating todo list...
✓ Todos generated

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 TODO LIST (12 tasks)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INFRA:
 1. [ ] Add magic_link_tokens DynamoDB table to infra/pulumi/dynamodb.py
 2. [ ] Deploy infra to dev environment

API:
 3. [ ] Create app/auth/magic_link.py with token generation
 4. [ ] Add email sending function using SES
 5. [ ] Add POST /auth/magic-link endpoint
 6. [ ] Add GET /auth/verify/:token endpoint
 7. [ ] Add tests for magic link flow

WEB:
 8. [ ] Create MagicLinkLogin component
 9. [ ] Add /auth/verify/:token route
10. [ ] Update Login component with magic link option
11. [ ] Add error handling and loading states

TESTING:
12. [ ] Run integration tests for complete flow

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Do you approve these todos?
[A]pprove  [E]dit  [R]eject

> A

✓ Todos approved

🚀 Ready to execute!

Which repository should I work on?
Enter GitHub URL or path:

> https://github.com/TrailLensCo/traillensdev

🔍 Cloning repository...
✓ Cloned traillensdev with submodules

Creating branch: topic/bedrock-passwordless-auth
✓ Branch created

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 EXECUTING TODOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/12] Add magic_link_tokens DynamoDB table...
      📝 Reading infra/pulumi/dynamodb.py
      ✍️  Adding table definition
      ✓ Updated infra/pulumi/dynamodb.py

[2/12] Deploy infra to dev environment...
      🚀 Running: cd infra && pulumi up --stack dev
      ⏳ Deploying...
      ✓ Deployment complete

[3/12] Create app/auth/magic_link.py...
      ✍️  Writing new file
      ✓ Created app/auth/magic_link.py

[4/12] Add email sending function...
      ✍️  Adding SES email function
      ✓ Updated app/auth/magic_link.py

... (continues for all 12 tasks) ...

[12/12] Run integration tests...
       🧪 Running pytest
       ✓ All tests passing (45 passed)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ EXECUTION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary:
  Files created:   3
  Files modified:  5
  Tests added:     8
  Commits:         5

  Branch: topic/bedrock-passwordless-auth
  Status: ✓ Pushed to remote

Would you like me to create a pull request?
[Y]es  [N]o

> Y

Creating PR...
✓ Pull request created: #123
  https://github.com/TrailLensCo/traillensdev/pull/123

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Session complete! 🎉
Session ID: session-abc123

To resume: tb-agent resume session-abc123
```

## Implementation Roadmap

### Milestone 1: Foundation (Week 1-2)
- [ ] Build container image with dev tools
- [ ] Create FastAPI server with basic git operations
- [ ] Set up ECS Fargate + EFS infrastructure
- [ ] Test git clone, branch, commit, push

### Milestone 2: Bedrock Agent Setup (Week 2-3)
- [ ] Create Bedrock agent with basic instructions
- [ ] Set up Knowledge Base with templates
- [ ] Create action groups for template processing
- [ ] Test prompt → structured prompt flow

### Milestone 3: Workflow Integration (Week 3-4)
- [ ] Add plan generation action group
- [ ] Add todo generation action group
- [ ] Implement approval mechanism
- [ ] Test full template workflow

### Milestone 4: Code Execution (Week 4-5)
- [ ] Add file operation action groups
- [ ] Add code generation capabilities
- [ ] Implement test execution
- [ ] Add commit and push functionality

### Milestone 5: CLI Tool (Week 5-6)
- [ ] Build Python CLI with click/typer
- [ ] Implement interactive approval prompts
- [ ] Add session management
- [ ] Add progress tracking

### Milestone 6: Testing & Polish (Week 6-7)
- [ ] End-to-end testing with real repositories
- [ ] Error handling and retry logic
- [ ] Logging and monitoring
- [ ] Documentation

### Milestone 7: Advanced Features (Week 7-8)
- [ ] PR creation integration
- [ ] Code review integration
- [ ] Multi-repository support
- [ ] Template customization

## Cost Estimate (Monthly)

### AWS Services:
- **ECS Fargate**: $0.04048/hour × ~50 hours/month = **~$2**
- **EFS**: $0.30/GB × 20GB + I/O = **~$7**
- **Bedrock Agent**:
  - Orchestration: ~100K tokens/month × $0.002 = **~$0.20**
  - Code generation: ~500K tokens/month × $0.008 = **~$4**
- **DynamoDB**: On-demand, minimal = **~$1**
- **Lambda**: Minimal usage = **~$0.50**
- **CloudWatch**: Logs/metrics = **~$2**

**Total: ~$16-20/month for moderate usage**

### Scaling Costs:
- Heavy usage (daily use): ~$40-60/month
- Enterprise (team of 5): ~$150-200/month

## Security Considerations

1. **GitHub Credentials**: Store in AWS Secrets Manager
2. **IAM Roles**: Least privilege for Lambda, ECS, Bedrock
3. **VPC**: Run ECS in private subnet
4. **Encryption**: Encrypt EFS, enable encryption at rest for DynamoDB
5. **Audit**: CloudTrail for all Bedrock API calls
6. **Rate Limiting**: Implement rate limits on API endpoints
7. **Code Review**: All generated code should be reviewed before merge

## Comparison with Claude Code

| Feature | Claude Code | Bedrock Alternative |
|---------|------------|---------------------|
| Hosting | Claude.ai cloud | Self-hosted AWS |
| Cost | Included in Pro | ~$16-60/month |
| Customization | Limited | Full control |
| Templates | Fixed | Custom templates |
| Submodules | Supported | Supported |
| Approval Flow | Basic | Custom (prompt→plan→todo) |
| Integration | GitHub only | Any git provider |
| Audit Trail | Limited | Full CloudWatch logs |
| Team Usage | Individual | Team-friendly |

## Success Criteria

✅ Agent can:
- Take a natural language prompt
- Generate structured prompt with clarifying questions
- Create detailed implementation plan
- Break plan into actionable todos
- Execute todos on a git repository
- Handle repos with submodules
- Create branches and commits
- Run tests and verify changes
- Create pull requests
- Provide clear status updates
- Allow user approval at each phase

## Next Steps

1. **Prototype** (This Week):
   - Build basic container with git
   - Create simple FastAPI server
   - Test git operations manually

2. **MVP** (Next 2 Weeks):
   - Create minimal Bedrock agent
   - Implement prompt → plan flow
   - Test with simple single-file change

3. **Beta** (Next Month):
   - Full template workflow
   - CLI tool for interaction
   - Test with real TrailLens features

4. **Production** (Next 2 Months):
   - Polish UX
   - Add error recovery
   - Team access controls
   - Documentation

---

*Document Created: 2026-02-06*
*Use Case: Self-hosted AWS Bedrock alternative to Claude Code*
*Target: TrailLens development workflow automation*
