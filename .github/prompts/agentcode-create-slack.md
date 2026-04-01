<!--
═══════════════════════════════════════════════════════════════════════════════
ORIGINAL USER PROMPTS
═══════════════════════════════════════════════════════════════════════════════

Prompt 1:
"The agentcode project allows me to setup a system in AWS to run tasks on my
codebase. I used the attached prompt to create it. Now, I want to add some code
to allow me to monitor my progress in slack. I had claude look into it on my iPhone.

I want to use slack to:
- kick off a new instance and run a prompt on the system
- monitor an existing instance on a slack channel and its progress
- immediately shut down an instance after saving all the work (to github)

There must be some guardrails in place. There must be a prompt to be injected
into every run to allow me some control, such as no instance can run over 6 hrs,
no token use can exceed $30 on bedrock, etc.

There must be some kind of monitoring for cost usage as well with notiications
to slack.

UPdate the attached, and run it through the prompt-template.md in the agentcode
project to generate a plan. Use the current code as a starting point, but do not
limit yourself to what is currently written."

Prompt 2:
"Regenerte the prompt attached using what you learned, but use the
prompt-to-todo-prompt.md template to generate it. Be more detailed. I want to
see implementation details, code samples, unit tests detailts, etc.

Also, ALL code must be generated using Test Driven Developmemnt. YOu must write
the tests first to spec, and then write the code to make the tests pass. Make
sure this is strictly mentioned and observered."

Prompt 3:
"Add all my manual prompts to the HTML comments section"

Prompt 4:
"The attached prompt is good. The TODO files generated are good. But it lacks
the detail on the current code in the agentcore project. I want to see how the
instance is created, how the programs, code, servers are installed and from where,
how it will be managed, etc.. Update the attached general prompt with more detail
on how we intend to instaitate the instance and control it. We will re-generate
the todo files from this updsated prompt. Review the codebase when thinking about
the update. Be sure to include my manual prompts in the html comments in the file."

═══════════════════════════════════════════════════════════════════════════════
-->

# Unstructured Prompt: AgentCore Slack Integration & Guardrails

## Unstructured Prompt

I have an existing AWS-based agentcore system that runs AI coding tasks on EC2 spot instances. The system currently works by uploading task files to S3, launching spot instances via launch templates, executing tasks, and auto-terminating when done. It uses Python 3.14, Node.js latest, VS Code Server, and OpenCode SDK on ARM instances (c7g.4xlarge) with Amazon Linux 2023.

The agentcode project allows me to setup a system in AWS to run tasks on my codebase. I used the attached prompt to create it. Now, I want to add some code to allow me to monitor my progress in slack. I had claude look into it on my iPhone.

## Current AgentCore Implementation (Detailed)

**CRITICAL CONTEXT:** Understanding the current implementation is essential for integrating Slack functionality. The Slack integration will build on top of this existing infrastructure.

### 1. Infrastructure Layer (Pulumi)

**Files:** `pulumi/__main__.py`, `pulumi/components/spot_instance.py`, `pulumi/utils/config.py`

**What Pulumi Creates:**

1. **Security Group** (`traillens-{env}-agentcore-sg`):
   - Port 22: SSH access (0.0.0.0/0)
   - Port 8080: VS Code Server (0.0.0.0/0)
   - Port 4096: OpenCode Server (0.0.0.0/0)
   - Egress: All outbound traffic allowed

2. **IAM Role & Instance Profile** (`traillens-{env}-agentcore-role`):
   - Assume role policy for EC2 service
   - Attached policy: `AmazonEC2FullAccess` (enables self-termination)
   - Instance profile for EC2 to assume role

3. **EC2 Key Pair** (`traillens-{env}-agentcore-keypair`):
   - Created or reused if exists
   - Used for SSH access to instances

4. **Launch Template** (`traillens-{env}-agentcore-template`):
   - AMI: Latest Amazon Linux 2023 ARM64 (`al2023-ami-2023.*-arm64`)
   - Instance type: `c7g.4xlarge` (16 vCPU, 32GB RAM, ARM)
   - Spot configuration:
     - Market type: spot
     - Max price: $0.40 (dev), $0.50 (prod)
     - Spot instance type: one-time
     - Interruption behavior: terminate
   - User data: Base64-encoded `user-data.sh` script (embedded)
   - Monitoring: Enabled (CloudWatch detailed monitoring)
   - Tags: Environment, Project, ManagedBy, Component

**Stack Configuration** (`Pulumi.dev.yaml`, `Pulumi.prod.yaml`):

```yaml
config:
  aws:region: ca-central-1
  agentcore:environment: dev
  agentcore:project_name: traillens
  agentcore:instance_type: c7g.4xlarge
  agentcore:max_spot_price: "0.40"
  agentcore:enable_auto_shutdown: "true"
  agentcore:task_timeout_minutes: "120"
```

**Pulumi Outputs:**

- `security_group_id`: For referencing in Lambda/other resources
- `instance_role_arn`: For IAM policies
- `instance_profile_name`: For EC2 launch
- `launch_template_id`: For launching instances
- `launch_template_latest_version`: For versioning

### 2. Instance Bootstrap Process (user-data.sh)

**File:** `pulumi/scripts/user-data.sh`

**Execution:** Runs once on first boot, embedded in launch template as base64-encoded user data.

**What Gets Installed (in order):**

1. **System Update:**

   ```bash
   dnf update -y
   ```

2. **Build Dependencies:**

   ```bash
   dnf install -y gcc gcc-c++ make git curl wget tar gzip \
       openssl-devel bzip2-devel libffi-devel zlib-devel \
       readline-devel sqlite-devel tk-devel xz-devel ncurses-devel
   ```

3. **Python 3.14 (compiled from source):**
   - Downloads: `https://www.python.org/ftp/python/3.14.0/Python-3.14.0.tar.xz`
   - Compiles with: `--enable-optimizations --with-lto`
   - Installs to: `/usr/local/bin/python3.14`
   - Symlinks: `/usr/local/bin/python3` → `python3.14`, `/usr/local/bin/pip3` → `pip3.14`
   - **Why source:** Amazon Linux 2023 doesn't have Python 3.14 in repos yet

4. **Node.js (via NodeSource repository):**
   - Adds NodeSource LTS repo: `https://rpm.nodesource.com/setup_lts.x`
   - Installs: `dnf install -y nodejs`
   - Version: Latest LTS (currently Node 22.x)
   - **Why NodeSource:** Official Node.js recommended installation for RPM-based systems

5. **VS Code Server (code-server):**
   - Downloads latest ARM64 RPM from GitHub: `https://github.com/coder/code-server/releases`
   - Installs: `dnf install -y code-server-{version}-arm64.rpm`
   - Creates user: `coder` with home `/home/coder`
   - Config: `/home/coder/.config/code-server/config.yaml`
     - Bind address: `0.0.0.0:8080`
     - Auth: password (random 32-char base64)
     - No TLS (use SSH tunnel for secure access)

6. **OpenCode CLI (via npm):**

   ```bash
   npm install -g @opencode-ai/cli
   ```

   - Installs globally to `/usr/local/lib/node_modules/@opencode-ai/cli`
   - Creates binary: `/usr/local/bin/opencode`

7. **Task Runner User & Directories:**
   - Creates user: `taskrunner` with home `/home/taskrunner`
   - Creates directories:
     - `/home/taskrunner/tasks/` - Task Python files downloaded here
     - `/home/taskrunner/logs/` - Execution logs written here

8. **Task Runner Script (embedded):**
   - File: `/opt/agentcore/task_runner.py`
   - **Embedded directly in user-data.sh** (heredoc between `RUNNER_EOF` markers)
   - Made executable: `chmod +x`
   - Owner: `taskrunner:taskrunner`
   - Functionality:
     - Downloads tasks from S3 (future: will be modified by dynamic user-data)
     - Executes Python task files with timeout
     - Logs to `/home/taskrunner/logs/{task}_{timestamp}.log`
     - Auto-shutdowns instance via boto3 EC2 API
     - Uses EC2 metadata service to get instance ID: `http://169.254.169.254/latest/meta-data/instance-id`

9. **Systemd Service:**
   - File: `/etc/systemd/system/agentcore-runner.service`
   - Type: `oneshot` (runs once, then exits)
   - User: `taskrunner`
   - ExecStart: `/opt/agentcore/task_runner.py`
   - Restart: `no` (doesn't restart on failure)
   - Enabled: `systemctl enable agentcore-runner.service`
   - **Note:** Service is enabled but NOT started by user-data. Dynamic user-data (from launch-task.sh) starts it after downloading task.

**Bootstrap Timeline:**

- Total time: ~10-15 minutes
- Python compilation: ~8 minutes (largest component)
- Node.js + OpenCode: ~2 minutes
- VS Code Server: ~1 minute
- Everything else: ~2-3 minutes

### 3. Current Task Launch & Execution Flow

**File:** `scripts/launch-task.sh`

**Current Workflow:**

1. **User invokes:**

   ```bash
   ./scripts/launch-task.sh -t my_task.py [-s dev|prod] [-c count] [-n]
   ```

2. **Script gets Pulumi outputs:**

   ```bash
   cd pulumi/
   source scripts/setup-env.sh
   pulumi stack select dev
   LAUNCH_TEMPLATE_ID=$(pulumi stack output launch_template_id)
   ```

3. **Script creates/verifies S3 bucket:**
   - Bucket name: `{AWS_ACCOUNT_ID}-agentcore-tasks`
   - Region: `ca-central-1`
   - Creates if doesn't exist: `aws s3 mb s3://{bucket}`

4. **Script uploads task to S3:**
   - Key: `tasks/{filename}-{timestamp}`
   - Command: `aws s3 cp my_task.py s3://{bucket}/{key}`

5. **Script generates dynamic user-data:**

   ```bash
   USER_DATA=$(cat <<EOF | base64
   #!/bin/bash
   set -euo pipefail

   # Wait for base user-data to complete
   sleep 30

   # Download task from S3
   aws s3 cp "s3://{bucket}/{key}" /home/taskrunner/tasks/task.py
   chown taskrunner:taskrunner /home/taskrunner/tasks/task.py

   # Start task runner service
   systemctl start agentcore-runner.service
   EOF
   )
   ```

   - **Critical:** This runs AFTER the base user-data.sh embedded in launch template
   - Downloads specific task to `/home/taskrunner/tasks/task.py`
   - Starts the systemd service which executes task_runner.py

6. **Script launches EC2 instance:**

   ```bash
   aws ec2 run-instances \
       --launch-template "LaunchTemplateId={template_id}" \
       --user-data "$USER_DATA" \
       --count 1
   ```

   - Uses launch template (contains base user-data, AMI, instance type, spot config, IAM profile)
   - Passes dynamic user-data (merged with base user-data by EC2)
   - Returns instance ID: `i-abc123def456`

7. **Optionally waits for completion:**

   ```bash
   aws ec2 wait instance-terminated --instance-ids $INSTANCE_ID
   ```

**Task Execution on Instance:**

1. Instance boots with Amazon Linux 2023 ARM64
2. Base user-data runs (installs Python, Node, OpenCode, creates taskrunner service)
3. Dynamic user-data runs (downloads task, starts service)
4. Systemd starts `agentcore-runner.service`
5. Service executes `/opt/agentcore/task_runner.py`
6. Task runner:
   - Finds task files in `/home/taskrunner/tasks/` (e.g., `task.py`)
   - Executes: `python3 /home/taskrunner/tasks/task.py`
   - Timeout: 120 minutes (dev) or 180 minutes (prod)
   - Logs to: `/home/taskrunner/logs/task_{timestamp}.log`
   - On completion: calls `boto3.client('ec2').terminate_instances([instance_id])`
7. Instance terminates automatically

**Key Points:**

- **Two-stage user-data:** Base (embedded in template) + dynamic (from launch-task.sh)
- **S3 for task distribution:** Tasks uploaded before launch, downloaded on instance
- **Auto-shutdown:** Task runner terminates instance via boto3 EC2 API
- **IAM permissions:** Instance has EC2FullAccess to terminate itself
- **No persistent storage:** Everything on instance is ephemeral (spot instance)

### 4. How Slack Integration Will Build On This

**CRITICAL CHANGES NEEDED:**

1. **Replace manual launch-task.sh with Slack Lambda:**
   - Lambda receives `/agentcore run <prompt>` from Slack
   - Lambda creates task file (or uses OpenCode to generate task from prompt)
   - Lambda uploads task to S3
   - Lambda launches instance with enhanced dynamic user-data
   - Lambda creates Slack channel for monitoring
   - Lambda writes instance metadata to DynamoDB

2. **Enhanced dynamic user-data:**

   ```bash
   #!/bin/bash
   set -euo pipefail

   # Download task from S3
   aws s3 cp "s3://{bucket}/{key}" /home/taskrunner/tasks/task.py

   # Download guardrails config from S3
   aws s3 cp "s3://{bucket}/guardrails/{instance_id}.json" /home/taskrunner/guardrails.json

   # Download Slack reporter script
   aws s3 cp "s3://{bucket}/slack_reporter.py" /home/taskrunner/slack_reporter.py

   # Install Python dependencies
   pip3 install boto3 slack-sdk

   # Start Slack reporter (background)
   nohup python3 /home/taskrunner/slack_reporter.py \
       --instance-id {instance_id} \
       --slack-channel {channel_id} \
       --guardrails /home/taskrunner/guardrails.json &

   # Start task runner (foreground)
   systemctl start agentcore-runner.service
   ```

3. **Modify task_runner.py:**
   - Add guardrails enforcement (runtime, cost limits)
   - Add progress hooks (post to Slack via slack_reporter.py)
   - Add emergency shutdown handler (listens for DynamoDB signal)
   - Add GitHub commit automation (commit every 30 min, on shutdown)

4. **New slack_reporter.py on instance:**
   - Monitors task_runner.py output (tail logs)
   - Parses OpenCode output for progress events
   - Queries Bedrock CloudWatch metrics for token usage
   - Calculates EC2 cost (instance uptime * spot price)
   - Posts updates to Slack channel via Slack SDK
   - Rate-limited (max 1 message per 5 seconds)

5. **New DynamoDB table:**
   - Track instance state, costs, Slack channels
   - Enable emergency shutdown (Lambda writes stop signal, instance polls)

6. **New Lambda functions:**
   - `slack_bot/handler.py`: Handle `/agentcore run` and `/agentcore stop`
   - `cost_tracker/handler.py`: Periodic cost aggregation and alerts

7. **Secrets Manager:**
   - Store Slack bot token
   - Store Slack signing secret
   - Store GitHub PAT for auto-commits

I want to use slack to:

- kick off a new instance and run a prompt on the system
- monitor an existing instance on a slack channel and its progress
- immediately shut down an instance after saving all the work (to github)

There must be some guardrails in place. There must be a prompt to be injected into every run to allow me some control, such as no instance can run over 6 hrs, no token use can exceed $30 on bedrock, etc.

There must be some kind of monitoring for cost usage as well with notiications to slack.

UPdate the attached, and run it through the prompt-template.md in the agentcode project to generate a plan. Use the current code as a starting point, but do not limit yourself to what is currently written.

**What I want to add:**

I need to integrate Slack into this system to make it controllable and observable from my phone. Specifically:

1. **Slack Bot for Control**
   - Kick off new instances directly from Slack with a prompt/task description
   - User types something like `/agentcore run <prompt>` in Slack
   - Bot acknowledges, uploads the task, launches the instance
   - Returns instance ID and monitoring channel link

2. **Real-Time Progress Monitoring**
   - Each running instance gets its own dedicated Slack channel (or thread)
   - The bot posts progress updates to that channel as the task runs
   - Updates should include:
     - Instance launch status
     - Task execution started
     - Progress checkpoints from the agent (if OpenCode provides them)
     - Token usage stats (running total)
     - Cost estimates (running total)
     - Completion status (success/failure)
     - Links to any GitHub commits/PRs created
   - If I'm away, I can open Slack on my phone and see exactly what's happening

3. **Emergency Shutdown**
   - Command in Slack to immediately terminate an instance
   - Something like `/agentcore stop <instance-id>`
   - Must save all work to GitHub first (commit current changes)
   - Then gracefully shutdown the instance
   - Post confirmation to the monitoring channel

4. **Guardrails System**
   - Every task run must have these limits enforced:
     - **Max runtime: 6 hours** - Hard stop, no exceptions
     - **Max Bedrock token spend: $30** - Hard stop when hit
     - Limits should be configurable per-task but defaulting to these
   - When approaching limits (e.g., 5.5 hrs or $25 spent), warn in Slack
   - When limit hit, auto-save work to GitHub, then terminate
   - Post detailed summary of what was accomplished before shutdown

5. **Injected Control Prompt**
   - Every task execution should have a "system prompt" injected
   - This prompt contains the guardrails, user preferences, constraints
   - Something like: "You have max 6 hours and $30 budget. Focus on X. Commit frequently. If you hit limits, summarize progress."
   - Should be customizable per-run but have sensible defaults
   - Maybe stored in config and/or passed from Slack command

6. **Cost & Usage Monitoring**
   - Track all costs in real-time:
     - EC2 spot instance costs (per second)
     - Bedrock API costs (token usage)
     - S3 storage/transfer (minimal but track it)
   - Post cost updates to Slack:
     - Every 30 minutes during execution
     - When task completes
     - Daily summary of all runs
   - Warnings when approaching budget limits
   - Alert if cost/hour is unusually high (maybe > $5/hr)

**How I envision the Slack workflow:**

```
User: /agentcore run "Fix the auth bug in api-dynamo and add tests"

Bot: ✅ Task queued
     Instance: i-abc123def
     Channel: #agentcore-i-abc123def
     Estimated cost: $2-4
     Max runtime: 6hrs

[In #agentcore-i-abc123def channel]
Bot: 🚀 Instance launching (c7g.4xlarge spot, $0.35/hr)
Bot: 📦 Environment setup complete (Python 3.14, Node.js 22, OpenCode)
Bot: 🤖 Starting task: "Fix the auth bug in api-dynamo and add tests"
Bot: 💰 Cost so far: $0.12 | Bedrock tokens: 15K ($0.45)
Bot: 📝 Progress: Analyzing auth code in api/auth.py
Bot: 💰 Cost so far: $0.58 | Bedrock tokens: 142K ($4.26) | 47 minutes elapsed
Bot: ✅ Committed: Fix auth token validation (commit abc123)
Bot: 📝 Running tests... 12/15 passing
Bot: 💰 Cost so far: $1.05 | Bedrock tokens: 289K ($8.67) | 1hr 24min elapsed
Bot: ✅ All tests passing! Created PR #42
Bot: 🎉 Task complete! Total: $1.23 EC2 + $9.12 Bedrock = $10.35
Bot: 🛑 Instance terminated

User: (can monitor this from phone while away)
```

**Technical approach ideas:**

- Use AWS Lambda functions triggered by Slack events (slash commands, interactive messages)
- Lambda writes task config to S3, triggers EC2 launch via launch template
- EC2 instance has a "reporter" service that posts to Slack via webhook
  - Reporter reads CloudWatch logs from OpenCode
  - Reporter tracks token usage via Bedrock CloudWatch metrics
  - Reporter posts updates on interval (every 5-10 min) plus checkpoints
- Use DynamoDB to track:
  - Active instances and their Slack channels
  - Cost/usage per instance
  - Guardrails config per run
- Slack bot token stored in AWS Secrets Manager
- Cost calculation:
  - EC2: instance uptime * spot price (get from EC2 API)
  - Bedrock: sum of token usage from CloudWatch metrics * pricing
  - S3: track via CloudWatch metrics (minimal)

**Constraints and concerns:**

- Need to handle Slack rate limits (posting too frequently)
- OpenCode might not expose progress events - may need to parse logs
- Bedrock cost tracking needs to be accurate and real-time
- GitHub commit/push from instance needs proper credentials (maybe SSH key or PAT in Secrets Manager)
- Emergency shutdown must ensure work is committed (could lose uncommitted work)
- Spot instance interruptions - handle gracefully, notify Slack
- Multiple concurrent instances - each needs its own channel/thread

**What I'm NOT sure about yet:**

- Best way to parse OpenCode output for progress updates
- Whether to use Slack channels or threads for monitoring (channels = better notifications, threads = less clutter)
- How granular to make progress updates (every agent action? every 5 min? on checkpoints only?)
- Whether to support resuming a task if instance gets interrupted
- How to handle tasks that need human input mid-execution

## Quick Capture

**What I'm trying to achieve:**

- Monitor and control AI coding tasks from my phone via Slack
- Prevent runaway costs with hard guardrails (6hr max, $30 max)
- Get real-time visibility into what the agent is doing
- Emergency shutdown with work preservation
- Track all costs accurately in real-time

**Files/components probably involved:**

- New: `lambda/slack_bot.py` - Slack event handler
- New: `lambda/reporter.py` - Posts updates to Slack
- New: `components/slack_integration.py` - Pulumi for Lambda, API Gateway
- New: `components/guardrails.py` - Enforce limits
- New: `runner/slack_reporter.py` - On-instance Slack poster
- Modify: `runner/task_runner.py` - Add guardrails enforcement, progress reporting
- Modify: `pulumi/__main__.py` - Add Lambda, Secrets Manager, DynamoDB
- New: `pulumi/scripts/inject_control_prompt.py` - Add system prompt to tasks

**Technology/tools I think we'll need:**

- Slack Bolt for Python (Lambda runtime)
- AWS Lambda (Python 3.14)
- API Gateway (Slack webhook endpoint)
- DynamoDB (track instances, costs, channels)
- AWS Secrets Manager (Slack bot token, GitHub PAT)
- CloudWatch Logs Insights (parse OpenCode output)
- CloudWatch Metrics (Bedrock token usage, EC2 costs)
- Bedrock pricing API or hardcoded pricing table
- GitHub API or git commands (commit/push from instance)

**Things I'm concerned about:**

- Accurate real-time cost tracking for Bedrock (CloudWatch metrics might lag)
- Slack rate limiting if posting too frequently
- Handling spot instance interruptions gracefully
- Ensuring emergency shutdown actually saves work (git commit might fail)
- Securing Slack bot token and GitHub credentials
- Parsing unstructured OpenCode logs for progress

**Things I'm not sure about yet:**

- Channels vs threads for monitoring
- How to get progress events from OpenCode (might need to modify OpenCode or parse stdout)
- Supporting task resumption after interruption
- Handling tasks that need human decisions mid-execution
- Whether to create one Slack channel per run or reuse channels

**Related resources:**

- Current agentcore code in this repo
- Slack Bolt for Python: <https://slack.dev/bolt-python/>
- Bedrock pricing: <https://aws.amazon.com/bedrock/pricing/>
- OpenCode SDK docs (need to research progress events)

## Notes & Context

**Current system:**

- Pulumi deploys launch templates, security groups, IAM roles
- Launch instances via `launch-task.sh` script
- Instances run Amazon Linux 2023 ARM with Python 3.14, Node.js, OpenCode
- Task runner downloads task from S3, executes, auto-terminates
- No current monitoring except SSH + journalctl

**Why Slack:**

- I'm often away from desk but have phone
- Slack gives me push notifications
- Can check progress anytime
- Can emergency-stop if needed

**Guardrails rationale:**

- 6 hours: Most coding tasks should finish in 1-3 hrs, 6 is safety margin
- $30: Based on c7g.4xlarge spot ($0.35/hr * 6hr = $2.10) + Bedrock (avg $20-25 for heavy usage)
- Together these prevent a runaway agent from costing hundreds

**Cost estimation assumptions:**

- c7g.4xlarge spot: ~$0.35/hr in ca-central-1
- Bedrock Claude Sonnet: ~$3 per million input tokens, ~$15 per million output
- Typical task: 500K input + 200K output ≈ $4.50 Bedrock
- Total typical task: $2 EC2 + $5 Bedrock = $7
- Max task (6hr): $2.10 EC2 + $28 Bedrock = $30.10 (right at limit)

**Implementation phases (suggested):**

1. **Phase 1: Basic Slack bot**
   - Lambda function handles `/agentcore run` command
   - Creates task file, uploads to S3, launches instance
   - Posts confirmation with instance ID

2. **Phase 2: Monitoring channel**
   - Create dedicated Slack channel per run
   - Instance posts status updates via webhook
   - Basic updates: launch, running, complete

3. **Phase 3: Progress parsing**
   - Parse OpenCode logs for detailed progress
   - Post meaningful updates (files changed, tests run, commits made)

4. **Phase 4: Cost tracking**
   - Query CloudWatch for EC2 and Bedrock costs
   - Post periodic cost updates to Slack

5. **Phase 5: Guardrails enforcement**
   - Runtime limit enforced by systemd timer or cron
   - Token limit tracked via CloudWatch, checked periodically
   - Auto-shutdown when limits hit

6. **Phase 6: Emergency shutdown**
   - `/agentcore stop` command
   - Commit all changes, push to GitHub, terminate

7. **Phase 7: Control prompt injection**
   - System prompt prepended to every task
   - Configurable guardrails, preferences

**Success criteria:**

- I can launch a task from my phone via Slack
- I receive regular progress updates in a dedicated channel
- I can see current costs at any time
- Instance auto-stops at 6hrs or $30, whichever comes first
- I can emergency-stop and work is saved
- All costs are tracked accurately

---

## Next Steps

Use `prompt-to-todo-prompt.md` to organize this into a structured implementation plan with:

- Detailed requirements for each component
- Acceptance criteria for Slack commands, monitoring, guardrails
- Technical specifications for Lambda, DynamoDB schema, CloudWatch queries
- Cost calculation formulas
- Error handling and edge cases
- Testing strategy
