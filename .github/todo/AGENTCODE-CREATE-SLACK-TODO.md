# AGENTCODE-CREATE-SLACK-TODO

## Task Summary

Add Slack integration to the existing agentcore system to enable:
- Remote control of EC2 spot instances from Slack
- Real-time progress monitoring in dedicated Slack channels
- Cost tracking and guardrails enforcement (6hr max runtime, $30 max spend)
- Emergency shutdown with work preservation
- Comprehensive cost monitoring with Slack notifications

This extends the current agentcore infrastructure (EC2 spot instances running OpenCode agents) with Slack-based visibility and control, enabling monitoring from mobile devices.

---

## Phase 1: Infrastructure Setup

### TODO 1.1: Add Slack secrets to AWS Secrets Manager
- [ ] Create secret for Slack bot token
- [ ] Create secret for Slack signing secret
- [ ] Create secret for GitHub Personal Access Token (for commits)
- [ ] Add Pulumi code to create secrets in `pulumi/components/secrets.py`
- [ ] Export secret ARNs for Lambda access

**Files affected:**
- `pulumi/components/secrets.py` (new)
- `pulumi/__main__.py` (import and create secrets)

**Acceptance criteria:**
- Secrets exist in AWS Secrets Manager
- Secrets are tagged with Environment and Project
- Secret ARNs exported from Pulumi stack

**Dependencies:** None

---

### TODO 1.2: Create DynamoDB table for instance tracking
- [ ] Define table schema:
  - PK: `instance_id` (string)
  - Attributes: `slack_channel_id`, `slack_thread_ts`, `task_description`, `launched_at`, `status`, `ec2_cost`, `bedrock_cost`, `tokens_used`, `runtime_seconds`, `guardrails` (map)
- [ ] Add GSI for querying by status
- [ ] Add Pulumi code in `pulumi/components/dynamodb.py`
- [ ] Export table name and ARN

**Files affected:**
- `pulumi/components/dynamodb.py` (new)
- `pulumi/__main__.py`

**Acceptance criteria:**
- DynamoDB table created with proper schema
- GSI for status queries exists
- Table ARN exported

**Dependencies:** None

---

### TODO 1.3: Create S3 bucket for task files (if not exists)
- [ ] Check if S3 bucket component already exists
- [ ] If not, create bucket with lifecycle policies
- [ ] Enable versioning for task file history
- [ ] Add bucket policy for Lambda access

**Files affected:**
- `pulumi/components/s3.py` (new or modify existing)

**Acceptance criteria:**
- S3 bucket exists and is accessible by Lambda functions
- Bucket name exported from stack

**Dependencies:** None

---

## Phase 2: Slack Bot Lambda Functions

### TODO 2.1: Create Lambda function for Slack command handler
- [ ] Create `lambda/slack_bot/handler.py`
- [ ] Implement `/agentcore run <prompt>` command
- [ ] Implement `/agentcore stop <instance-id>` command
- [ ] Implement `/agentcore status [instance-id]` command
- [ ] Implement `/agentcore list` command (active instances)
- [ ] Verify Slack signature for security
- [ ] Parse command arguments
- [ ] Return acknowledgment to Slack within 3 seconds

**Files affected:**
- `lambda/slack_bot/handler.py` (new)
- `lambda/slack_bot/requirements.txt` (new - slack-bolt, boto3)
- `lambda/slack_bot/__init__.py` (new)

**Acceptance criteria:**
- Lambda responds to Slack commands within timeout
- Slack signature verification works
- Commands parsed correctly
- Error messages returned for invalid commands

**Dependencies:** 1.1 (secrets), 1.2 (DynamoDB)

---

### TODO 2.2: Implement task launch logic in Lambda
- [ ] Generate unique instance ID
- [ ] Create Slack channel for monitoring (or thread)
- [ ] Store instance metadata in DynamoDB
- [ ] Generate task file from prompt (or use template)
- [ ] Upload task file to S3
- [ ] Trigger EC2 instance launch via RunInstances API
  - Use existing launch template from current agentcore
  - Pass S3 task location via user-data
  - Pass Slack webhook URL via user-data
  - Pass DynamoDB table name via user-data
  - Pass instance ID via tags
- [ ] Post confirmation message to Slack with channel link

**Files affected:**
- `lambda/slack_bot/task_launcher.py` (new)
- `lambda/slack_bot/handler.py` (call task_launcher)

**Acceptance criteria:**
- Instance launches successfully
- Slack channel/thread created
- DynamoDB entry created with initial status
- Confirmation posted to Slack with monitoring link

**Dependencies:** 2.1, 1.2, 1.3, existing launch template

---

### TODO 2.3: Implement emergency stop logic in Lambda
- [ ] Lookup instance ID in DynamoDB
- [ ] Send SSM command to instance to commit changes
  - Run git add, commit, push to GitHub
  - Wait for completion (with timeout)
- [ ] Terminate EC2 instance via API
- [ ] Update DynamoDB status to "stopped"
- [ ] Post final summary to Slack channel

**Files affected:**
- `lambda/slack_bot/emergency_stop.py` (new)
- `lambda/slack_bot/handler.py`

**Acceptance criteria:**
- Instance receives stop signal
- Work is committed to GitHub (best effort)
- Instance terminates
- Status updated in DynamoDB
- Slack notified of shutdown

**Dependencies:** 2.1, 2.2

---

### TODO 2.4: Create Pulumi component for Slack bot Lambda
- [ ] Create `pulumi/components/slack_lambda.py`
- [ ] Define Lambda function resource
  - Runtime: Python 3.14
  - Handler: slack_bot.handler.handle_slack_event
  - Environment variables: DynamoDB table, S3 bucket, Secrets ARN
  - IAM role with policies:
    - SecretsManager:GetSecretValue
    - DynamoDB:PutItem, GetItem, UpdateItem, Query
    - S3:PutObject
    - EC2:RunInstances, TerminateInstances, DescribeInstances
    - SSM:SendCommand
    - IAM:PassRole (for instance profile)
- [ ] Create API Gateway HTTP endpoint
  - POST /slack/events
  - Integrate with Lambda
- [ ] Export API Gateway URL

**Files affected:**
- `pulumi/components/slack_lambda.py` (new)
- `pulumi/__main__.py`

**Acceptance criteria:**
- Lambda deployed successfully
- API Gateway endpoint accessible
- Environment variables configured correctly
- IAM permissions granted

**Dependencies:** 2.1, 2.2, 2.3, existing IAM instance profile

---

## Phase 3: On-Instance Progress Reporter

### TODO 3.1: Create Slack reporter service for EC2 instance
- [ ] Create `runner/slack_reporter.py`
- [ ] Read Slack webhook URL from environment/user-data
- [ ] Read instance ID from EC2 metadata
- [ ] Read DynamoDB table name from environment
- [ ] Implement post_update(message) function
  - Posts to Slack channel via webhook
  - Updates DynamoDB with latest status
  - Handles rate limiting (max 1 msg/5sec)
- [ ] Implement progress tracking functions:
  - report_launch()
  - report_task_started(description)
  - report_progress(message)
  - report_checkpoint(milestone)
  - report_commit(commit_hash, message)
  - report_completion(success, summary)
  - report_error(error_message)

**Files affected:**
- `runner/slack_reporter.py` (new)
- `runner/requirements.txt` (add requests, boto3)

**Acceptance criteria:**
- Reporter can post to Slack successfully
- DynamoDB updates work
- Rate limiting prevents spam
- All report functions implemented

**Dependencies:** 1.2, 2.2 (webhook URL passed to instance)

---

### TODO 3.2: Integrate reporter into existing task runner
- [ ] Read existing `runner/task_runner.py` (or equivalent)
- [ ] Initialize SlackReporter at startup
- [ ] Call reporter.report_launch() after environment setup
- [ ] Call reporter.report_task_started() before task execution
- [ ] Parse task output for progress indicators
  - OpenCode checkpoints (if available)
  - Git commits (detect git commit in output)
  - Test results (detect pytest/test output)
  - File changes (detect file modifications)
- [ ] Call reporter.report_progress() on checkpoints
- [ ] Call reporter.report_commit() when git commits detected
- [ ] Call reporter.report_completion() on task finish
- [ ] Call reporter.report_error() on exceptions

**Files affected:**
- `runner/task_runner.py` (modify existing or create new)
- `pulumi/scripts/user-data.sh` (pass Slack webhook URL, DynamoDB table)

**Acceptance criteria:**
- Task runner successfully uses reporter
- Progress updates posted to Slack during execution
- Commits reported when detected
- Completion/error messages sent

**Dependencies:** 3.1, existing task runner

---

### TODO 3.3: Parse OpenCode output for detailed progress
- [ ] Research OpenCode CLI output format
- [ ] Identify progress indicators in stdout/stderr
  - Agent thoughts/reasoning
  - Tool usage (Read, Write, Bash, etc.)
  - File modifications
  - Test execution
- [ ] Create parser in `runner/opencode_parser.py`
  - parse_line(line) → ProgressEvent or None
  - Extract meaningful checkpoints
- [ ] Integrate parser into task runner
- [ ] Map events to Slack messages

**Files affected:**
- `runner/opencode_parser.py` (new)
- `runner/task_runner.py`

**Acceptance criteria:**
- Parser extracts meaningful progress from OpenCode output
- Events mapped to user-friendly Slack messages
- No spam - only significant checkpoints reported

**Dependencies:** 3.2, OpenCode documentation research

---

## Phase 4: Cost Tracking System

### TODO 4.1: Implement EC2 cost calculator
- [ ] Create `runner/cost_tracker.py`
- [ ] Query EC2 instance metadata for:
  - Instance type
  - Launch time
  - Current time (calculate uptime)
- [ ] Query EC2 Spot pricing history via Boto3
  - Get current spot price for instance type and AZ
- [ ] Calculate cost: `spot_price * uptime_hours`
- [ ] Cache spot price (refresh every 10 minutes)

**Files affected:**
- `runner/cost_tracker.py` (new - EC2CostCalculator class)

**Acceptance criteria:**
- Accurate spot price retrieval
- Correct uptime calculation
- Cost calculation matches expected formula
- Efficient (cached pricing)

**Dependencies:** None (uses existing EC2 metadata and Boto3)

---

### TODO 4.2: Implement Bedrock cost calculator
- [ ] Research Bedrock CloudWatch metrics for token usage
- [ ] Identify metric names:
  - InputTokens
  - OutputTokens
  - Model ID (claude-sonnet, etc.)
- [ ] Query CloudWatch metrics via Boto3
  - Aggregate tokens from launch time to now
- [ ] Hardcode Bedrock pricing table or query Pricing API
  - Claude Sonnet 4.5: $3 per 1M input, $15 per 1M output (example)
- [ ] Calculate cost: `(input_tokens * input_price + output_tokens * output_price) / 1M`
- [ ] Cache metrics (refresh every 5 minutes)

**Files affected:**
- `runner/cost_tracker.py` (add BedrockCostCalculator class)
- `runner/bedrock_pricing.py` (new - pricing constants)

**Acceptance criteria:**
- Token usage retrieved from CloudWatch
- Pricing table accurate
- Cost calculation correct
- Efficient (cached metrics)

**Dependencies:** None

**Questions:**
- How are Bedrock calls tagged/tracked to this instance? Need to ensure metrics filtered correctly.
- CloudWatch metrics may lag by 1-5 minutes - acceptable?

---

### TODO 4.3: Implement periodic cost reporting
- [ ] Create background thread/process in task runner
- [ ] Every 30 minutes during execution:
  - Calculate current EC2 cost
  - Calculate current Bedrock cost
  - Calculate total cost
  - Post update to Slack via reporter
    - Format: "💰 Cost update: $X.XX EC2 + $Y.YY Bedrock = $Z.ZZ total (Nh NNm elapsed)"
  - Update DynamoDB with latest costs
- [ ] On task completion:
  - Calculate final costs
  - Post final summary to Slack
  - Update DynamoDB

**Files affected:**
- `runner/cost_tracker.py` (add PeriodicReporter class)
- `runner/task_runner.py` (start background reporter)

**Acceptance criteria:**
- Cost updates posted every 30 minutes
- Final cost summary accurate
- DynamoDB updated with costs
- No crashes if cost calculation fails (degrade gracefully)

**Dependencies:** 4.1, 4.2, 3.1 (SlackReporter)

---

## Phase 5: Guardrails Enforcement

### TODO 5.1: Create guardrails configuration system
- [ ] Define guardrails schema:
  ```python
  {
    "max_runtime_seconds": 21600,  # 6 hours
    "max_cost_dollars": 30.0,
    "warning_runtime_seconds": 19800,  # 5.5 hours
    "warning_cost_dollars": 25.0,
    "auto_commit_interval_seconds": 1800  # 30 min
  }
  ```
- [ ] Store default guardrails in config file
- [ ] Allow per-task override via Slack command args
  - `/agentcore run --max-runtime 7200 "task description"`
- [ ] Pass guardrails to instance via user-data or DynamoDB
- [ ] Load guardrails in task runner

**Files affected:**
- `lambda/slack_bot/guardrails_config.py` (new - default config)
- `lambda/slack_bot/task_launcher.py` (parse overrides, pass to instance)
- `runner/guardrails.py` (new - load and validate config)

**Acceptance criteria:**
- Default guardrails defined
- Per-task overrides work
- Guardrails loaded on instance
- Invalid configs rejected

**Dependencies:** None

---

### TODO 5.2: Implement runtime limit enforcement
- [ ] In task runner, start timer on task start
- [ ] Check elapsed time every 60 seconds
- [ ] When approaching warning threshold (e.g., 5.5 hrs):
  - Post warning to Slack: "⚠️ Approaching 6hr limit (30min remaining)"
- [ ] When limit reached:
  - Post alert to Slack: "🛑 Runtime limit reached (6hrs)"
  - Trigger emergency shutdown sequence:
    1. Stop task execution (SIGTERM)
    2. Commit all work to GitHub
    3. Generate summary of progress
    4. Post summary to Slack
    5. Update DynamoDB
    6. Terminate instance
- [ ] Handle case where commit/push fails (timeout after 5 min)

**Files affected:**
- `runner/guardrails.py` (add RuntimeLimitEnforcer class)
- `runner/task_runner.py` (integrate enforcer)
- `runner/emergency_shutdown.py` (new - shutdown sequence)

**Acceptance criteria:**
- Runtime tracked accurately
- Warning posted at threshold
- Hard stop at limit
- Work committed before shutdown (best effort)
- Summary posted to Slack

**Dependencies:** 5.1, 3.1 (SlackReporter), 4.3 (cost data for summary)

---

### TODO 5.3: Implement cost limit enforcement
- [ ] In cost tracker, check total cost every 5 minutes
- [ ] When approaching warning threshold (e.g., $25):
  - Post warning to Slack: "⚠️ Approaching $30 cost limit ($5 remaining)"
- [ ] When limit reached:
  - Post alert to Slack: "🛑 Cost limit reached ($30)"
  - Trigger emergency shutdown sequence (same as runtime limit)
- [ ] Handle race condition (cost calculated async from enforcement)

**Files affected:**
- `runner/guardrails.py` (add CostLimitEnforcer class)
- `runner/cost_tracker.py` (integrate check)
- `runner/emergency_shutdown.py` (reuse shutdown sequence)

**Acceptance criteria:**
- Cost tracked and checked regularly
- Warning posted at threshold
- Hard stop at limit
- Work committed before shutdown

**Dependencies:** 5.1, 5.2, 4.3

---

### TODO 5.4: Implement periodic auto-commit
- [ ] Create background process to commit work every N minutes (default 30)
- [ ] On each interval:
  - Check if there are uncommitted changes (git status)
  - If yes:
    - Commit with message: "Auto-commit: WIP at [timestamp]"
    - Push to GitHub (current branch or new branch)
    - Post commit hash to Slack
    - Update DynamoDB with latest commit
  - If no changes, skip
- [ ] Ensure commit doesn't disrupt running task
- [ ] Handle merge conflicts (abort and notify)

**Files affected:**
- `runner/auto_committer.py` (new)
- `runner/task_runner.py` (start auto-committer thread)

**Acceptance criteria:**
- Commits happen on schedule
- Work pushed to GitHub
- No disruption to task execution
- Errors handled gracefully

**Dependencies:** 5.1, 3.1

---

## Phase 6: Control Prompt Injection

### TODO 6.1: Create system prompt template
- [ ] Design prompt template with placeholders:
  ```
  SYSTEM GUARDRAILS:
  - Maximum runtime: {max_runtime_hours} hours
  - Maximum cost: ${max_cost_dollars}
  - You will be automatically shut down when limits are reached
  - Commit your work frequently (every 30 minutes)
  - Focus on completing the task within constraints

  USER TASK:
  {user_task_description}

  INSTRUCTIONS:
  - Work efficiently to complete the task within time/cost limits
  - Commit changes incrementally with descriptive messages
  - If you encounter blockers, document them and move on
  - Prioritize working code over perfect code
  - Run tests frequently to validate changes
  ```
- [ ] Store template in `lambda/slack_bot/prompt_template.txt`
- [ ] Add template customization support (per-user preferences)

**Files affected:**
- `lambda/slack_bot/prompt_template.txt` (new)
- `lambda/slack_bot/prompt_injector.py` (new - template engine)

**Acceptance criteria:**
- Template includes all necessary guardrails
- Placeholders replaced with actual values
- Customization supported

**Dependencies:** 5.1 (guardrails config)

---

### TODO 6.2: Inject prompt into task file
- [ ] In task launcher, before uploading to S3:
  - Load prompt template
  - Replace placeholders with guardrails and user task
  - Generate final prompt
  - Wrap in task execution script (Python/shell)
  - Upload to S3
- [ ] Ensure injected prompt is passed to OpenCode correctly
- [ ] Test that OpenCode respects the system instructions

**Files affected:**
- `lambda/slack_bot/task_launcher.py` (modify to inject prompt)
- `lambda/slack_bot/prompt_injector.py`

**Acceptance criteria:**
- Prompt injected before task upload
- OpenCode receives full prompt with guardrails
- System instructions influence agent behavior

**Dependencies:** 6.1, 2.2

---

## Phase 7: Slack Interaction Enhancements

### TODO 7.1: Create dedicated Slack channel per run (vs threads)
- [ ] Research Slack API for creating channels programmatically
- [ ] In task launcher:
  - Create channel with name pattern: `agentcore-{instance_id_short}`
  - Set channel topic with task description
  - Invite user to channel (if not default member)
  - Post welcome message with instance details
  - Store channel ID in DynamoDB
- [ ] Cleanup: Archive channels after 7 days (optional)

**Files affected:**
- `lambda/slack_bot/slack_channel_manager.py` (new)
- `lambda/slack_bot/task_launcher.py`

**Acceptance criteria:**
- Channel created per run
- User added to channel
- Channel ID stored
- Welcome message posted

**Dependencies:** 2.2

**Questions:**
- Channels vs threads? Channels = better notifications, more visible. Threads = less clutter. Need to decide.
- Archiving strategy - immediate after task? 7 days? Never?

---

### TODO 7.2: Implement interactive Slack messages
- [ ] Add interactive buttons to key messages:
  - On launch: [Stop Instance] [View Logs]
  - On warnings: [Extend Limit] [Stop Now]
  - On completion: [View PR] [Restart Task]
- [ ] Create Lambda to handle button clicks (interactive messages)
- [ ] Implement button actions:
  - Stop Instance → trigger emergency stop
  - View Logs → post link to CloudWatch Logs
  - Extend Limit → update guardrails (with confirmation)
  - View PR → post link to GitHub PR

**Files affected:**
- `lambda/slack_bot/interactive_handler.py` (new)
- `lambda/slack_bot/handler.py` (route interactive messages)
- `pulumi/components/slack_lambda.py` (add route for interactive endpoint)

**Acceptance criteria:**
- Buttons appear in messages
- Clicks handled correctly
- Actions executed successfully

**Dependencies:** 7.1, 2.3

**Complexity:** Medium - Slack interactive messages can be tricky

---

### TODO 7.3: Add rich formatting to Slack messages
- [ ] Use Slack Block Kit for formatted messages
- [ ] Design message templates:
  - Launch message (with instance details, estimated cost)
  - Progress update (with progress bar, current file)
  - Cost update (with breakdown and chart)
  - Completion message (with summary, PR link, final cost)
- [ ] Implement formatting functions in SlackReporter
- [ ] Add emoji indicators:
  - 🚀 Launch
  - 📝 Progress
  - 💰 Cost update
  - ⚠️ Warning
  - 🛑 Error/limit
  - ✅ Success
  - ❌ Failure

**Files affected:**
- `runner/slack_reporter.py` (add format_message methods)
- `lambda/slack_bot/message_templates.py` (new - Block Kit templates)

**Acceptance criteria:**
- Messages well-formatted and readable
- Emojis used consistently
- Important info highlighted

**Dependencies:** 3.1

---

## Phase 8: Error Handling & Edge Cases

### TODO 8.1: Handle Slack rate limits
- [ ] Implement exponential backoff for Slack API calls
- [ ] Queue messages if rate limited (max queue size: 100)
- [ ] Batch messages if queue fills up (summarize multiple updates)
- [ ] Post warning to Slack if messages dropped

**Files affected:**
- `runner/slack_reporter.py` (add rate limit handling)
- `lambda/slack_bot/task_launcher.py` (handle rate limits)

**Acceptance criteria:**
- No 429 errors from Slack
- Messages queued and sent eventually
- Batching works when needed

**Dependencies:** 3.1, 2.2

---

### TODO 8.2: Handle spot instance interruptions
- [ ] Listen for EC2 spot interruption warnings (2-minute notice)
  - Poll EC2 metadata endpoint every 5 seconds
  - Check for spot interruption notice
- [ ] On interruption warning:
  - Post urgent message to Slack: "⚠️ Spot instance being interrupted!"
  - Trigger emergency shutdown sequence immediately
  - Try to commit/push all work
  - Mark instance as "interrupted" in DynamoDB
- [ ] Option to resume task on new instance (stretch goal)

**Files affected:**
- `runner/spot_monitor.py` (new)
- `runner/task_runner.py` (start spot monitor)
- `runner/emergency_shutdown.py`

**Acceptance criteria:**
- Interruption detected within 5 seconds
- Emergency shutdown triggered
- Work committed (best effort)
- Slack notified

**Dependencies:** 5.2 (emergency shutdown)

**Questions:**
- Should we support task resumption? Would need to checkpoint progress.

---

### TODO 8.3: Handle GitHub commit failures
- [ ] In auto-commit and emergency shutdown:
  - Retry git push up to 3 times with exponential backoff
  - If all retries fail:
    - Create git bundle file: `git bundle create backup.bundle HEAD`
    - Upload bundle to S3 backup bucket
    - Post S3 URL to Slack with instructions
- [ ] Test scenarios:
  - Network failure
  - Authentication failure (bad PAT)
  - Merge conflicts
  - Branch protection rules

**Files affected:**
- `runner/auto_committer.py`
- `runner/emergency_shutdown.py`
- `runner/git_backup.py` (new)

**Acceptance criteria:**
- Retries work correctly
- Bundle created on failure
- S3 backup stored
- User notified with recovery instructions

**Dependencies:** 5.4, 5.2

---

### TODO 8.4: Handle task execution failures
- [ ] Catch exceptions in task runner
- [ ] On failure:
  - Capture error message and stack trace
  - Post error to Slack with details
  - Mark task as "failed" in DynamoDB
  - Commit any partial work
  - Save logs to S3
  - Do NOT terminate instance (allow for debugging via SSH)
  - Post SSH instructions to Slack
- [ ] Auto-terminate after 1 hour if no user action

**Files affected:**
- `runner/task_runner.py`
- `runner/error_handler.py` (new)

**Acceptance criteria:**
- Errors caught and logged
- Slack notified with details
- Partial work committed
- Instance left running for debugging (time-limited)

**Dependencies:** 3.1, 5.4

---

## Phase 9: Testing & Validation

### TODO 9.1: Create unit tests for Lambda functions
- [ ] Test slack_bot.handler:
  - Valid Slack commands
  - Invalid commands
  - Signature verification
- [ ] Test task_launcher:
  - S3 upload
  - EC2 launch
  - DynamoDB write
  - Slack channel creation
- [ ] Test emergency_stop:
  - SSM command send
  - Instance termination
  - DynamoDB update

**Files affected:**
- `lambda/tests/test_handler.py` (new)
- `lambda/tests/test_task_launcher.py` (new)
- `lambda/tests/test_emergency_stop.py` (new)
- `lambda/tests/conftest.py` (new - pytest fixtures)

**Acceptance criteria:**
- 80%+ code coverage on Lambda functions
- All edge cases tested
- Mocked AWS services (moto)

**Dependencies:** Phase 2 complete

---

### TODO 9.2: Create integration tests for instance workflow
- [ ] Test end-to-end flow:
  1. Send Slack command
  2. Verify instance launches
  3. Verify Slack channel created
  4. Verify progress messages posted
  5. Verify cost updates posted
  6. Verify task completion message
  7. Verify instance terminated
- [ ] Test emergency stop flow
- [ ] Test guardrails enforcement (mock time/cost)
- [ ] Test spot interruption handling

**Files affected:**
- `tests/integration/test_e2e_workflow.py` (new)
- `tests/integration/test_guardrails.py` (new)

**Acceptance criteria:**
- Full workflow tested in staging environment
- All critical paths covered
- Tests pass reliably

**Dependencies:** All phases

---

### TODO 9.3: Create manual test plan and documentation
- [ ] Document manual test scenarios:
  - Launch task from Slack
  - Monitor progress from mobile
  - Trigger emergency stop
  - Test cost limit
  - Test runtime limit
  - Test spot interruption (simulate)
- [ ] Create test checklist in `.github/testing/AGENTCODE-SLACK-TEST-PLAN.md`
- [ ] Execute manual tests and document results

**Files affected:**
- `.github/testing/AGENTCODE-SLACK-TEST-PLAN.md` (new)

**Acceptance criteria:**
- Comprehensive test plan documented
- All scenarios tested manually
- Results documented

**Dependencies:** 9.2

---

## Phase 10: Documentation & Deployment

### TODO 10.1: Update README.md
- [ ] Add section on Slack integration
- [ ] Document Slack commands:
  - `/agentcore run <prompt>`
  - `/agentcore stop <instance-id>`
  - `/agentcore status [instance-id]`
  - `/agentcore list`
- [ ] Document guardrails system
- [ ] Add cost tracking explanation
- [ ] Include setup instructions for Slack app

**Files affected:**
- `README.md`

**Acceptance criteria:**
- README comprehensive and up-to-date
- Examples included
- Setup instructions clear

**Dependencies:** All phases

---

### TODO 10.2: Create Slack app setup guide
- [ ] Document Slack app creation:
  - Create new Slack app
  - Add slash commands
  - Add bot scopes (chat:write, channels:manage, etc.)
  - Install to workspace
  - Get bot token and signing secret
- [ ] Document secret setup in AWS
- [ ] Document API Gateway URL configuration in Slack

**Files affected:**
- `docs/SLACK-SETUP.md` (new)

**Acceptance criteria:**
- Step-by-step guide complete
- Screenshots included
- Tested by following guide

**Dependencies:** All phases

---

### TODO 10.3: Deploy to staging environment
- [ ] Create `Pulumi.staging.yaml` config
- [ ] Deploy infrastructure: `pulumi up -s staging`
- [ ] Verify all components deployed:
  - Lambda functions
  - API Gateway
  - DynamoDB table
  - Secrets Manager secrets
  - IAM roles and policies
- [ ] Test in staging with sample task
- [ ] Fix any deployment issues

**Files affected:**
- `Pulumi.staging.yaml` (new)

**Acceptance criteria:**
- Staging environment deployed successfully
- All resources created
- Basic smoke tests pass

**Dependencies:** All phases

---

### TODO 10.4: Deploy to production environment
- [ ] Review staging deployment and test results
- [ ] Create `Pulumi.prod.yaml` config (if not exists)
- [ ] Deploy to production: `pulumi up -s prod`
- [ ] Verify production deployment
- [ ] Configure production Slack app
- [ ] Announce availability to team

**Files affected:**
- `Pulumi.prod.yaml`

**Acceptance criteria:**
- Production environment deployed
- All resources verified
- Team notified and trained

**Dependencies:** 10.3

---

## Phase 11: Monitoring & Operations

### TODO 11.1: Setup CloudWatch alarms
- [ ] Create alarms for:
  - Lambda errors (>5 in 5 minutes)
  - Lambda throttling
  - DynamoDB throttling
  - API Gateway 5xx errors
  - High cost (>$50/day)
- [ ] Send alarms to SNS topic
- [ ] Configure SNS to post to Slack ops channel

**Files affected:**
- `pulumi/components/monitoring.py` (new)
- `pulumi/__main__.py`

**Acceptance criteria:**
- Alarms created and active
- SNS notifications work
- Slack ops channel receives alerts

**Dependencies:** None

---

### TODO 11.2: Create operational dashboard
- [ ] Create CloudWatch dashboard with:
  - Active instances count
  - Daily cost by instance
  - Lambda invocation counts
  - DynamoDB operations
  - Slack message volume
- [ ] Export dashboard URL

**Files affected:**
- `pulumi/components/monitoring.py`

**Acceptance criteria:**
- Dashboard created
- All key metrics visible
- URL accessible

**Dependencies:** 11.1

---

### TODO 11.3: Document operational procedures
- [ ] Create runbook for common scenarios:
  - User reports Slack bot not responding
  - Instance stuck (not terminating)
  - Cost overrun
  - Spot interruptions frequent
  - GitHub commits failing
- [ ] Document debugging steps
- [ ] Document recovery procedures

**Files affected:**
- `docs/OPERATIONS.md` (new)

**Acceptance criteria:**
- Runbook comprehensive
- Debugging steps clear
- Recovery procedures tested

**Dependencies:** None

---

## Questions & Unknowns

1. **Slack channels vs threads:** Which is better for monitoring? Channels are more visible but create clutter. Threads are cleaner but less noticeable on mobile.

2. **OpenCode progress events:** Does OpenCode provide structured progress events, or do we need to parse stdout/stderr? Need to research the SDK.

3. **Bedrock cost tracking:** How to attribute Bedrock API calls to a specific instance? Need to ensure CloudWatch metrics are properly tagged/filtered.

4. **Task resumption:** Should we support resuming tasks after spot interruptions? Would require checkpointing agent state - complex.

5. **Guardrails overrides:** Should users be able to override limits per-task? If so, what are the safety bounds (max 12 hours? max $100?)?

6. **GitHub authentication:** Use SSH keys or PAT? SSH keys more secure but harder to manage. PAT easier but riskier if leaked.

7. **CloudWatch metrics lag:** Bedrock/EC2 metrics may lag by 1-5 minutes. Acceptable for cost tracking, or need real-time?

8. **Concurrent instances:** How many simultaneous instances should we support? Need DynamoDB capacity planning.

9. **Channel archiving:** When to archive Slack channels? Immediately? 7 days? Never?

10. **Cost alerts:** Should we alert on high cost-per-hour (e.g., >$5/hr) as a potential issue, or only on total cost limit?

---

## Success Criteria

- [ ] User can launch a coding task from Slack on their phone
- [ ] User receives real-time progress updates in a dedicated Slack channel/thread
- [ ] User can see current costs at any time during execution
- [ ] Instance auto-stops at 6 hours OR $30 spent, whichever comes first
- [ ] User receives warning before limits are reached (30 min before runtime, $5 before cost)
- [ ] User can emergency-stop an instance from Slack, and work is committed to GitHub
- [ ] All costs are tracked accurately (EC2 + Bedrock) and reported in Slack
- [ ] Progress updates are meaningful and user-friendly (not spam)
- [ ] System handles errors gracefully (spot interruptions, GitHub failures, etc.)
- [ ] Comprehensive documentation and operational procedures exist
- [ ] System deployed to production and tested end-to-end

---

## Complexity Estimate

**Overall complexity: HIGH**

- Infrastructure changes: MEDIUM (Pulumi, Lambda, DynamoDB, Secrets)
- Slack integration: MEDIUM (Slack API, webhooks, interactive messages)
- Cost tracking: HIGH (CloudWatch metrics, pricing, real-time calculation)
- Guardrails enforcement: MEDIUM (timers, thresholds, emergency shutdown)
- Progress reporting: HIGH (parsing OpenCode output, meaningful updates)
- Error handling: MEDIUM (many edge cases to handle)
- Testing: MEDIUM (unit tests, integration tests, manual testing)

**Estimated implementation time:**
- Phase 1-2 (Infrastructure + Slack bot): 3-5 days
- Phase 3 (Progress reporting): 2-3 days
- Phase 4 (Cost tracking): 2-3 days
- Phase 5 (Guardrails): 2-3 days
- Phase 6 (Prompt injection): 1 day
- Phase 7 (Slack enhancements): 1-2 days
- Phase 8 (Error handling): 2-3 days
- Phase 9 (Testing): 2-3 days
- Phase 10 (Documentation + Deployment): 1-2 days
- Phase 11 (Monitoring): 1-2 days

**Total: ~20-30 days** (assuming focused, full-time work)

---

## Dependencies Graph

```
Phase 1 (Infrastructure)
  ↓
Phase 2 (Slack Bot) ← Phase 1
  ↓
Phase 3 (Progress Reporter) ← Phase 2
  ↓
Phase 4 (Cost Tracking) ← Phase 3
  ↓
Phase 5 (Guardrails) ← Phase 4
  ↓
Phase 6 (Prompt Injection) ← Phase 5
  ↓
Phase 7 (Slack Enhancements) ← Phase 2, Phase 3
  ↓
Phase 8 (Error Handling) ← Phase 5
  ↓
Phase 9 (Testing) ← All phases
  ↓
Phase 10 (Documentation + Deployment) ← All phases
  ↓
Phase 11 (Monitoring) ← Phase 10
```

---

**Next Step:** Review this TODO list, answer open questions, then begin implementation starting with Phase 1.
