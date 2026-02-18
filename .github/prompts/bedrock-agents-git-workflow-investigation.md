# AWS Bedrock Agents for Git-Based Development Workflow

## Investigation Summary

This document explores the feasibility of using AWS Bedrock Agents to automate a git-based development workflow that processes templates, manages repositories with submodules, and creates code changes in branches.

## Workflow Requirements

The target workflow involves:
1. Template processing (prompt-template.md → plan-template.md → todo-template.md)
2. GitHub repository checkout
3. Git submodule operations
4. Branch creation and management
5. Code file modifications
6. Git operations (add, commit, push)

## Can Bedrock Agents Support This Workflow?

**Yes, technically feasible but requires significant custom infrastructure.**

### Bedrock Agents Capabilities Match

**✅ What Bedrock Agents CAN do:**
- Multi-step orchestration across template workflow
- Call external APIs via action groups
- Invoke Lambda functions for custom operations
- Maintain session context throughout the process
- Use knowledge bases to understand codebase patterns

**⚠️ What requires custom implementation:**
- **Git operations** - Need Lambda functions or EC2 to execute git commands
- **File system access** - Lambda has limited /tmp storage; complex repos may need EFS or EC2
- **Submodule handling** - Git submodules require recursive clone/update operations
- **Credential management** - GitHub access tokens via AWS Secrets Manager
- **Execution environment** - May need container-based Lambda or EC2 for full git tooling

## Container-Based Architecture (Recommended Approach)

### How It Works

**The Bedrock Agent doesn't "live inside" the container** - instead:

1. **Bedrock Agent** (managed AWS service) orchestrates the workflow
2. **Container** (Fargate/ECS/EKS) acts as the execution environment
3. **Communication** happens via action groups (API calls)

```
Bedrock Agent → Action Group → API/Lambda → Container Environment → Tools (git, continue.dev, etc.)
                                                ↓
                                    Your Working Environment:
                                    - Git + submodules
                                    - GitHub CLI
                                    - continue.dev CLI
                                    - Python/Node.js
                                    - Full file system
```

### Container Image Setup

**✅ You CAN include:**
- Git + full git tooling
- GitHub CLI (`gh`)
- continue.dev CLI (if available)
- Claude Code CLI (if available)
- Python, Node.js, any runtimes
- Custom scripts
- Code quality tools (black, eslint, etc.)

**Container would expose REST API endpoints like:**
- `POST /repo/clone` - Clone repo with submodules
- `POST /branch/create` - Create topic branch
- `POST /file/edit` - Modify files
- `POST /git/commit` - Commit changes
- `POST /git/push` - Push to GitHub
- `POST /tools/continue` - Invoke continue.dev CLI
- `GET /repo/status` - Get git status

## Hosting Options Comparison

### ECS Fargate
**✅ Pros:**
- No server management
- Pay per task runtime
- Good for ephemeral workspaces
- Auto-scaling

**⚠️ Cons:**
- 20GB ephemeral storage limit
- Need EFS for persistent workspace
- Cold starts for new tasks

### ECS on EC2
**✅ Pros:**
- More storage options
- Can mount EFS easily
- Persistent instances
- Better for large repos

**⚠️ Cons:**
- Need to manage EC2 instances
- Pay for running instances

### EKS (Kubernetes)
**✅ Pros:**
- Advanced orchestration
- Job queuing
- Resource management

**⚠️ Cons:**
- More complex setup
- Overkill for single-agent workflow

### EC2 with Long-Running Container
**✅ Pros:**
- Full control
- Easy EFS mounting
- Persistent workspace across sessions
- Can keep git repos checked out

**⚠️ Cons:**
- Pay for idle time
- Need to manage instance

## Recommended Architecture

```yaml
Components:
  Bedrock Agent:
    Purpose: Orchestration and reasoning
    Responsibilities:
      - Parse prompt/plan/todo templates
      - Decide what actions to take
      - Call action groups in sequence

  Container Environment (ECS Fargate + EFS):
    Base Image: ubuntu:22.04 or amazonlinux:2023
    Installed Tools:
      - git
      - gh (GitHub CLI)
      - continue.dev CLI
      - Python 3.13 + pip
      - Node.js 22 + npm
      - Custom scripts

    Mounted Storage:
      - EFS volume for persistent workspace
      - Keeps cloned repos between invocations

    API Server:
      - FastAPI or Express.js
      - Exposes endpoints for git operations
      - Handles file system operations
      - Invokes CLI tools

  Action Groups:
    - Lambda proxy → ECS Task API
    - Or: API Gateway → Container API directly

  State Management:
    - DynamoDB for workflow state
    - EFS for git repositories
    - S3 for artifacts/logs
```

## Continue.dev / Claude Code CLI Integration

**If these tools have CLI interfaces:**

```dockerfile
# In your container
RUN npm install -g @continuedev/cli  # If available
RUN pip install claude-code-cli      # If available

# Your API endpoint
POST /tools/continue
{
  "command": "continue edit src/App.tsx --instruction 'Add dark mode'"
}

# Container executes:
cd /workspace/repo && continue edit src/App.tsx --instruction "..."
```

## Session Management Pattern

```python
# Bedrock Agent workflow:
1. Agent: "I need to implement feature X"
2. Call action: initialize_workspace(repo_url, branch)
   → Container: git clone, git checkout -b topic/feature-x

3. Agent: "Read current code"
4. Call action: read_files(patterns)
   → Container: returns file contents

5. Agent: "Plan the changes" (using plan-template.md)
6. Call action: create_plan(plan_content)
   → Container: writes PLAN.md

7. Agent: "Create todo items" (using todo-template.md)
8. Call action: create_todos(items)
   → Container: writes TODO.md

9. Agent: "Implement changes"
10. Call action: edit_file(path, changes)
    → Container: modifies files

11. Agent: "Commit and push"
12. Call action: git_commit_push(message)
    → Container: git add, commit, push
```

## Storage Strategy

**For repositories with submodules:**

```
EFS Volume Structure:
/workspace/
  ├── repos/
  │   ├── traillensdev/          # Main repo
  │   │   ├── infra/              # Submodule
  │   │   ├── api-dynamo/         # Submodule
  │   │   └── web/                # Submodule
  │   └── other-repos/
  ├── cache/
  │   └── git/                    # Git credential cache
  └── logs/
```

## Cost Considerations

**Fargate + EFS:**
- Fargate task: ~$0.04048/hour (0.5 vCPU, 1GB RAM)
- EFS: ~$0.30/GB-month + $0.03/GB for I/O
- Bedrock Agent: ~$0.002/1K input tokens, ~$0.008/1K output tokens

**For occasional use (10 sessions/day, 30min each):**
- Fargate: ~$6/month
- EFS: ~$5/month (assuming 10GB)
- Bedrock: ~$20-50/month (depending on usage)

**Total: ~$30-60/month for automated development workflow**

## Implementation Checklist

### Phase 1: Container Environment
- [ ] Build container image with git, gh, Python, Node.js
- [ ] Create FastAPI server with git operation endpoints
- [ ] Test git clone with submodules
- [ ] Test branch creation and file modifications
- [ ] Test commit and push operations

### Phase 2: ECS/Fargate Setup
- [ ] Create ECS cluster
- [ ] Configure EFS volume for persistent workspace
- [ ] Create task definition with EFS mount
- [ ] Deploy container to Fargate
- [ ] Configure security groups and IAM roles

### Phase 3: Bedrock Agent Configuration
- [ ] Create Bedrock agent
- [ ] Define action groups for git operations
- [ ] Create Lambda proxies to ECS API
- [ ] Configure GitHub credentials in Secrets Manager
- [ ] Test agent orchestration

### Phase 4: Workflow Integration
- [ ] Load prompt/plan/todo templates into knowledge base
- [ ] Create agent instructions for template processing
- [ ] Test end-to-end workflow
- [ ] Add error handling and logging
- [ ] Create monitoring dashboards

## Conclusion

**Yes, this architecture is viable:**
1. ✅ Build container with full dev environment
2. ✅ Run in Fargate (or ECS/EKS/EC2)
3. ✅ Include continue.dev CLI, gh CLI, git, etc.
4. ✅ Bedrock Agent uses these tools via API calls
5. ✅ Handle submodules properly
6. ✅ Create branches, commit, push

**The agent orchestrates, the container executes.**

This provides clean separation of concerns - the Bedrock Agent handles reasoning and workflow orchestration, while the container provides a full-featured development environment for executing git operations and running development tools.

## Alternative Approach

**Simpler Alternative:** Use GitHub Actions or AWS CodeBuild triggered by Bedrock Agents rather than having agents execute git operations directly. The agent could orchestrate the workflow while delegating actual git operations to purpose-built CI/CD tools.

## Next Steps

1. Prototype container image with git tooling
2. Build simple FastAPI server with basic git endpoints
3. Test manual git operations in container
4. Create minimal Bedrock agent with single action group
5. Iterate and expand based on results

---

*Investigation Date: 2026-02-06*
*Context: TrailLens AI infrastructure using AWS Bedrock*
