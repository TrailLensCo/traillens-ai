# AI Infrastructure Greenfield Deployment TODO List

**Created:** 2026-02-21
**Updated:** 2026-02-22
**Source Prompt:** `.github/prompts/ai-migration-canada-prompt.md`
**Status:** 🔲 Not Started
**Project Phase:** Planning

## Overview

**GREENFIELD DEPLOYMENT** - Deploy TrailLens AI infrastructure to AWS Canada (ca-central-1) from scratch. No existing infrastructure to migrate. Phase 1 deploys Bedrock IAM, AWS Budgets, and multi-region model access. Phase 2 tests deployed infrastructure locally. Phase 3 deploys EC2-based self-hosted infrastructure with LiteLLM, OpenCode, and automated scheduling. **Production stack only** (no dev environment).

## Revision History

**2026-02-22:** Revised from migration TODO to greenfield deployment TODO based on confirmation that AI infrastructure was never deployed to AWS. Key changes:

- **Changed all "update" language to "create"** - No existing resources to update
- **Removed DNS CNAME deletion** - DNS component never deployed, removing from code only (TODO #6)
- **Added stack initialization step** - Must run `pulumi stack init prod` (TODO #9)
- **Updated verification steps** - Verifying NEW resources, not updates (TODO #11)
- **Clarified IAM credentials** - New IAM user and access keys created, not existing ones
- **Updated all risk mitigations** - Reflect greenfield deployment risks vs migration risks
- **Production stack only** - No dev environment to deploy or migrate

## Prerequisites
- [ ] AWS CLI configured with admin credentials
- [ ] Pulumi CLI installed and logged in
- [ ] Local testing environment functional (ai/server/ with LiteLLM, OpenCode, PostgreSQL, Redis)
- [ ] SSH key pair created in AWS ca-central-1 for future EC2 access
- [ ] Email address configured for AWS Budget alerts

## Assumptions & Constraints
- **Single production stack only** - No dev environment to reduce costs
- Local testing with real AWS credentials required before production deployment
- Claude Sonnet 4.6 and Opus 4.6 may require manual AWS console approval (model access request)
- Haiku 4.5 already approved in ca-central-1
- Amazon Titan Image Generator V2 available in us-east-1 only
- Image generation acceptable to leave Canada (us-east-1) as trade-off
- EC2 instance will run 17 hours/day (7 AM - 12 AM ET) for cost optimization

## Implementation Phases

---

## PHASE 1: Pulumi Infrastructure Deployment (Greenfield)

**Goal:** Prepare Pulumi code for greenfield deployment (Bedrock IAM policies, AWS Budgets, remove DNS component), preview infrastructure, deploy to prod stack, and verify deployment. **No existing AWS resources - this is first deployment.**

### 1.1: Pulumi Code Changes (Bedrock, Budgets, DNS)

- [ ] **TODO #1: Update Bedrock IAM policy to support Claude Sonnet 4.6** `(Priority: P0, Complexity: S, Owner: DevOps)`
  - **Acceptance Criteria:**
    - **GREENFIELD:** Code currently has `anthropic.claude-sonnet-4-5-v2:0`, update to `anthropic.claude-sonnet-4-6-v2:0`
    - Policy allows `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` for Sonnet 4.6
    - ARN format verified: `arn:aws:bedrock:ca-central-1::foundation-model/anthropic.claude-sonnet-4-6-v2:0`
    - Changes committed to git (not deployed yet - no existing infrastructure)
  - **Dependencies:** None
  - **Affected Files:**
    - `ai/pulumi/components/bedrock.py` (modify line 74 - update Sonnet ARN from 4.5 to 4.6)
  - **Testing Requirements:** Code review, verify ARN format matches AWS documentation
  - **Risks:** Low - Code change only, greenfield deployment
  - **Rollback Plan:** Revert git commit before first deployment
  - **Notes:** May require manual approval via AWS console for Sonnet 4.6 model access after deployment

- [ ] **TODO #2: Verify Claude Opus 4.6 ARN is correct** `(Priority: P0, Complexity: XS, Owner: DevOps)`
  - **Acceptance Criteria:**
    - **GREENFIELD:** Current code (line 72) has: `arn:aws:bedrock:ca-central-1::foundation-model/anthropic.claude-opus-4-6`
    - Verify ARN format matches AWS Bedrock documentation for ca-central-1
    - No changes needed if ARN is correct
    - Update if ARN format differs (e.g., needs version suffix)
  - **Dependencies:** None
  - **Affected Files:**
    - `ai/pulumi/components/bedrock.py` (verify line 72, modify if incorrect)
  - **Testing Requirements:** Manual verification via AWS Bedrock documentation or console
  - **Risks:** Low - Verification only, no deployment yet
  - **Rollback Plan:** Update ARN if incorrect before first deployment
  - **Notes:** Opus 4.6 may require manual approval via AWS console after first deployment

- [ ] **TODO #3: Add IAM permissions for Amazon Titan Image Generator V2** `(Priority: P1, Complexity: M, Owner: DevOps)`
  - **Acceptance Criteria:**
    - **GREENFIELD:** Current code only has ca-central-1 models, need to add us-east-1 region
    - New IAM policy statement added for us-east-1 region (image generation)
    - ARN: `arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-image-generator-v2:0`
    - Policy allows `bedrock:InvokeModel` for Titan Image V2
    - Multi-region policy structure: separate statements for ca-central-1 (text) and us-east-1 (images)
    - Policy includes `bedrock:ListFoundationModels` and `bedrock:GetFoundationModel` for both regions
    - Changes committed to git (not deployed yet - greenfield)
  - **Dependencies:** None
  - **Affected Files:**
    - `ai/pulumi/components/bedrock.py` (modify policy JSON - add us-east-1 statement after line 90)
  - **Testing Requirements:** Code review for multi-region policy structure
  - **Risks:** Low - Code change only, greenfield deployment
  - **Rollback Plan:** Revert git commit before first deployment
  - **Notes:** Image generation data leaves Canada (us-east-1 only) - acceptable per requirements

- [ ] **TODO #4: Create AWS Budget Pulumi component** `(Priority: P1, Complexity: M, Owner: DevOps)`
  - **Acceptance Criteria:**
    - **GREENFIELD:** New file `ai/pulumi/components/budget.py` created (doesn't exist)
    - Component creates SNS topic for budget alerts
    - Component creates AWS Budget for Bedrock service
    - Budget threshold: $75/month
    - Alerts at 80% ($60) and 100% ($75) of budget
    - Forecast alert at 100%
    - Budget filters by Service = "Amazon Bedrock"
    - Email subscription parameter configurable via Pulumi config
    - Changes committed to git (not deployed yet - greenfield)
  - **Dependencies:** None
  - **Affected Files:**
    - `ai/pulumi/components/budget.py` (create new file)
  - **Testing Requirements:** Code review for AWS Budgets API usage
  - **Risks:** Low - Budget monitoring doesn't block operations, greenfield deployment
  - **Rollback Plan:** Remove component from __main__.py before first deployment
  - **Notes:** Based on template in migration prompt lines 804-876

- [ ] **TODO #5: Integrate budget component into Pulumi stack** `(Priority: P1, Complexity: S, Owner: DevOps)`
  - **Acceptance Criteria:**
    - **GREENFIELD:** Import budget component in `ai/pulumi/__main__.py`
    - Call `create_budget_stack()` function after Bedrock stack (after line 63)
    - Pass email address from Pulumi config: `budgetAlertEmail`
    - Export SNS topic ARN and budget ID (after line 94)
    - Stack deployment will include budget resources
    - Set budget email via: `pulumi config set budgetAlertEmail "mark@buckaway.ca"`
    - Changes committed to git (not deployed yet - greenfield)
  - **Dependencies:** TODO #4 (budget component created)
  - **Affected Files:**
    - `ai/pulumi/__main__.py` (modify - import and call budget component, update exports)
    - `ai/pulumi/Pulumi.yaml` (no changes needed - config set via CLI)
  - **Testing Requirements:** Code review for proper integration
  - **Risks:** Low - Greenfield deployment, no existing resources affected
  - **Rollback Plan:** Revert changes before first deployment
  - **Notes:** Budget email must be configured before running pulumi preview/up for first time

- [ ] **TODO #6: Remove DNS CNAME component from code before first deployment** `(Priority: P2, Complexity: S, Owner: DevOps)`
  - **Acceptance Criteria:**
    - **GREENFIELD:** DNS component exists in code but never deployed to AWS
    - Comment out or delete `ai/pulumi/components/dns.py`
    - Remove DNS component import from `ai/pulumi/__main__.py` (line 21)
    - Remove DNS stack creation call (lines 69-77)
    - Remove DNS exports from __main__.py (lines 88-89: bedrock_endpoint, custom_domain)
    - Changes committed to git (not deployed yet - greenfield)
  - **Dependencies:** None
  - **Affected Files:**
    - `ai/pulumi/components/dns.py` (delete or comment out - nothing to remove from AWS)
    - `ai/pulumi/__main__.py` (modify - remove DNS import, call, exports)
  - **Testing Requirements:** Code review to ensure all DNS references removed
  - **Risks:** Low - DNS CNAME never deployed, removing from code only
  - **Rollback Plan:** Restore dns.py component and __main__.py import from git before first deployment
  - **Notes:** Keep dns.py in git history for reference when creating EC2 DNS (A record) in Phase 3

### 1.2: Python Code Validation

- [ ] **TODO #7: Validate Python code with validate-python.py** `(Priority: P0, Complexity: M, Owner: DevOps)`
  - **Acceptance Criteria:**
    - Navigate to `ai/` directory
    - Activate Python virtual environment: `source scripts/setup-env.sh`
    - Run Python validation: `scripts/validate-python.py`
    - **If validation succeeds:**
      - All Python files pass syntax checks
      - No import errors in Pulumi components
      - Type hints validated where present
      - No linting errors from validation script
      - Output shows "Validation passed" or equivalent success message
    - **If validation fails:**
      - Review validation errors in output
      - Fix issues in affected files (`bedrock.py`, `budget.py`, `__main__.py`)
      - Re-run `scripts/validate-python.py` until it succeeds
      - Common errors: Syntax errors, missing imports, type hint issues, undefined variables
    - All Pulumi components pass validation before proceeding to deployment
  - **Dependencies:** TODO #1-#6 (all code changes complete)
  - **Affected Files:**
    - `ai/pulumi/components/bedrock.py` (may need fixes if validation fails)
    - `ai/pulumi/components/budget.py` (may need fixes if validation fails)
    - `ai/pulumi/__main__.py` (may need fixes if validation fails)
  - **Testing Requirements:** `scripts/validate-python.py` must succeed with no errors
  - **Risks:** Medium - Validation may reveal syntax errors, import issues, or type problems
  - **Rollback Plan:** Fix code errors, revert to previous commit if needed, re-run validation
  - **Notes:** **CRITICAL**: Python validation must pass before running pulumi preview. This catches errors early before deployment.

### 1.3: Deployment & Verification

- [ ] **TODO #8: Configure budget alert email** `(Priority: P0, Complexity: XS, Owner: User)`
  - **Acceptance Criteria:**
    - Navigate to `ai/pulumi/` directory
    - Activate Python virtual environment: `source ../scripts/setup-env.sh`
    - Set budget email: `pulumi config set budgetAlertEmail "mark@buckaway,ca"`
    - Verify config saved: `pulumi config get budgetAlertEmail`
    - Email address must be valid to receive SNS subscription confirmation
  - **Dependencies:** TODO #5 (budget component integrated into stack), TODO #7 (Python validation passed)
  - **Affected Files:**
    - `ai/pulumi/Pulumi.prod.yaml` (Pulumi config)
  - **Testing Requirements:** Verify config value is set correctly
  - **Risks:** Low - Configuration only
  - **Rollback Plan:** Update email address if incorrect
  - **Notes:** **USER ACTION REQUIRED**: Must be completed before running pulumi preview

- [ ] **TODO #9: Run pulumi preview for greenfield deployment and fix errors** `(Priority: P0, Complexity: M, Owner: DevOps)`
  - **Acceptance Criteria:**
    - **GREENFIELD:** First time running pulumi for this project - no existing stack
    - Navigate to `ai/pulumi/` directory (if not already there)
    - Activate Python virtual environment: `source ../scripts/setup-env.sh` (if not already activated)
    - Initialize stack if needed: `pulumi stack init prod` (first time only)
    - Run `pulumi preview --stack prod`
    - **If preview succeeds:**
      - Document NEW resources that will be created (greenfield):
        - IAM user for Bedrock access
        - IAM access keys
        - IAM policy (Bedrock Sonnet 4.6, Opus 4.6, Haiku 4.5, Titan Image V2)
        - AWS Budget ($75/month threshold)
        - SNS topic and email subscription for budget alerts
      - Verify ONLY greenfield resources shown (no updates/deletions - nothing exists)
      - Save preview output for user review
    - **If preview fails:**
      - Fix errors in Pulumi components (`bedrock.py`, `budget.py`) or config files
      - Re-run `pulumi preview` until it succeeds
      - Common errors: Invalid ARN format, missing Pulumi config, IAM syntax errors, missing budgetAlertEmail, stack not initialized
    - Preview output shows ONLY: New resource creation (no updates, no deletions)
  - **Dependencies:** TODO #1-#6 (all code changes complete), TODO #7 (Python validation passed), TODO #8 (budget email configured)
  - **Affected Files:**
    - `ai/pulumi/components/bedrock.py` (may need fixes if preview fails)
    - `ai/pulumi/components/budget.py` (may need fixes if preview fails)
    - Pulumi config files (may need updates)
  - **Testing Requirements:** `pulumi preview` must succeed with no errors
  - **Risks:** Medium - Preview may reveal errors in IAM policy structure, Budget API usage, ARN format, or stack initialization
  - **Rollback Plan:** Fix code errors, revert to previous commit if needed, re-run preview
  - **Notes:** **CRITICAL**: DO NOT run `pulumi up` yet - preview only. User will manually deploy after reviewing preview output. This is GREENFIELD - all resources are NEW.

- [ ] **TODO #10: Manual greenfield deployment by user (pulumi up)** `(Priority: P0, Complexity: M, Owner: User)`
  - **Acceptance Criteria:**
    - **GREENFIELD DEPLOYMENT:** First time deploying - no existing AWS resources
    - **USER ACTION REQUIRED:** User reviews `pulumi preview` output from TODO #9
    - User manually runs: `cd ai/pulumi && pulumi up --stack prod`
    - User confirms deployment when Pulumi prompts: "Do you want to perform this update? yes"
    - Pulumi deployment completes without errors
    - CloudFormation stack created successfully (check AWS Console - first time)
    - All NEW resources created successfully:
      - IAM user and access keys (Bedrock access)
      - IAM policy (Bedrock Sonnet 4.6, Opus 4.6, Haiku 4.5, Titan Image V2)
      - AWS Budget ($75/month)
      - SNS topic and subscription
    - No drift detected in Pulumi state
    - Deployment summary shows ALL resources as "created" (no updates, no deletions)
    - SNS subscription confirmation email received
  - **Dependencies:** TODO #9 (pulumi preview succeeded)
  - **Affected Files:**
    - AWS IAM user (created via Pulumi - GREENFIELD)
    - AWS IAM policies (created via Pulumi - GREENFIELD)
    - AWS Budget resources (created via Pulumi - GREENFIELD)
    - AWS SNS topic and subscription (created via Pulumi - GREENFIELD)
    - Pulumi state (backend S3 - first state file)
    - CloudFormation stack (created - GREENFIELD)
  - **Testing Requirements:** Manual `pulumi up` execution by user
  - **Risks:** Medium - First production deployment, creates Bedrock access and billing alerts
  - **Rollback Plan:** If deployment fails: `pulumi refresh && pulumi cancel`, then `pulumi destroy --stack prod` to remove partial deployment, fix code, redeploy
  - **Notes:** **USER MUST EXECUTE THIS MANUALLY.** User must confirm SNS subscription via email link. Claude will wait for confirmation before proceeding to Phase 2 testing. This is GREENFIELD - all resources are NEW.

- [ ] **TODO #11: Verify greenfield deployment succeeded** `(Priority: P0, Complexity: M, Owner: DevOps)`
  - **Acceptance Criteria:**
    - **GREENFIELD VERIFICATION:** First deployment - verifying NEW resources only
    - **Pulumi Verification:**
      - Pulumi stack shows "update succeeded" message (first deployment)
      - Check Pulumi exports: `pulumi stack output` (verify IAM user ARN, access keys, budget ID, SNS topic ARN)
      - Pulumi state matches deployed resources (no drift)
      - No CloudFormation rollback occurred (check AWS Console → CloudFormation - first stack)
    - **Bedrock IAM Verification:**
      - Verify IAM user created in AWS Console: IAM → Users → Search for ai-bedrock-user
      - Verify IAM policy attached to user in AWS Console
      - Policy document includes Sonnet 4.6, Opus 4.6, Haiku 4.5, Titan Image V2 ARNs
      - Policy includes both ca-central-1 and us-east-1 regions
      - Verify models accessible via AWS CLI (may require manual approval first):

        ```bash
        aws bedrock list-foundation-models --region ca-central-1 --by-provider anthropic
        aws bedrock list-foundation-models --region us-east-1 --by-provider amazon | grep titan-image
        ```

      - Confirm Sonnet 4.6, Opus 4.6, Haiku 4.5 appear in ca-central-1 list
      - Confirm Titan Image V2 appears in us-east-1 list
    - **Budget Verification:**
      - AWS Budget created in AWS Budgets console (first budget)
      - Budget name, threshold ($75/month), and filters (Service = Amazon Bedrock) correct
      - Alerts configured at 80% and 100%
      - Forecast alert configured at 100%
    - **SNS Verification:**
      - SNS topic created in AWS SNS console (first topic)
      - Email subscription exists and shows "Confirmed" status
      - User has confirmed subscription via email link
    - **DNS Verification:**
      - SKIP - DNS component removed from code before deployment (TODO #6)
      - No DNS records created (greenfield deployment without DNS component)
  - **Dependencies:** TODO #10 (manual greenfield deployment completed by user)
  - **Affected Files:** None (verification only)
  - **Testing Requirements:** AWS CLI + AWS Console verification across multiple services
  - **Risks:** Low - Verification only, does not modify resources
  - **Rollback Plan:** If verification fails, execute TODO #10 rollback plan (pulumi destroy + git revert + fix code + redeploy)
  - **Notes:** If Bedrock models show as unavailable, they may require manual approval via AWS Bedrock console (expected for Opus/Sonnet 4.6). SNS subscription MUST be confirmed before proceeding to Phase 2. This is GREENFIELD - all resources are NEW.

---

## PHASE 2: Testing with Deployed Infrastructure

**Goal:** Test LiteLLM connection to deployed Bedrock infrastructure, verify all models work, confirm cost tracking, and document model access status.

- [ ] **TODO #12: Update local LiteLLM config with greenfield deployed model ARNs** `(Priority: P1, Complexity: XS, Owner: DevOps)`
  - **Acceptance Criteria:**
    - **GREENFIELD:** Using newly deployed infrastructure from Phase 1
    - `ai/server/config/litellm-config.yaml` updated with Sonnet 4.6 ARN
    - Opus 4.6 ARN verified (no change if correct)
    - Titan Image V2 added with us-east-1 region
    - All 4 models configured: Opus 4.6, Sonnet 4.6, Haiku 4.5, Titan Image V2
    - Model names match: `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5`, `titan-image-v2`
  - **Dependencies:** TODO #11 (greenfield deployment verified successful)
  - **Affected Files:**
    - `ai/server/config/litellm-config.yaml` (modify - update model ARNs)
  - **Testing Requirements:** Manual verification of YAML syntax
  - **Risks:** Low - Configuration file only
  - **Rollback Plan:** Restore previous litellm-config.yaml from git
  - **Notes:** Using production AWS credentials from greenfield deployed IAM user (Phase 1)

- [ ] **TODO #13: Test LiteLLM connection to Bedrock with greenfield deployed credentials** `(Priority: P1, Complexity: M, Owner: DevOps)`
  - **Acceptance Criteria:**
    - **GREENFIELD:** Using IAM access keys from newly deployed infrastructure (TODO #11)
    - Verify `ai/server/.env` has production IAM access keys from `pulumi stack output`
    - Start local services: `cd ai/server && ./manage.sh start`
    - LiteLLM health check responds: `curl http://localhost:8000/health/liveliness`
    - Models listed via API: `curl -H "Authorization: Bearer sk-test-1234567890" http://localhost:8000/v1/models`
    - All 4 models appear in response: `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5`, `titan-image-v2`
    - No connection errors in LiteLLM logs
  - **Dependencies:** TODO #12 (LiteLLM config updated)
  - **Affected Files:**
    - `ai/server/.env` (verify credentials present, DO NOT COMMIT)
  - **Testing Requirements:** Manual API testing with curl
  - **Risks:** Medium - Testing production Bedrock access for first time
  - **Rollback Plan:** Restart services if connection fails
  - **Notes:** **CRITICAL**: Never commit .env with real credentials. Verify `.env` in `.gitignore`. Get access keys from `pulumi stack output`

- [ ] **TODO #14: Test Claude Haiku 4.5 text completion (baseline)** `(Priority: P1, Complexity: S, Owner: DevOps)`
  - **Acceptance Criteria:**
    - **Test Command:**
      ```bash
      curl -X POST http://localhost:8000/v1/chat/completions \
        -H "Authorization: Bearer sk-test-1234567890" \
        -H "Content-Type: application/json" \
        -d '{
          "model": "claude-haiku-4-5",
          "messages": [{"role": "user", "content": "Say hello"}],
          "max_tokens": 50
        }'
      ```
    - **HTTP Status:** 200 OK
    - **Response Validation:**
      - Contains `model`, `choices`, `usage` fields
      - `choices[0].message.content` has generated text
      - `usage.prompt_tokens` and `usage.completion_tokens` populated
    - **Cost Verification:**
      ```bash
      podman exec litellm-db psql -U llmproxy -d litellm -c \
        "SELECT model, \"totalCost\", \"promptTokens\", \"completionTokens\" \
         FROM \"LiteLLM_SpendLogs\" ORDER BY \"startTime\" DESC LIMIT 1;"
      ```
    - Expected cost: < $0.01 per test
  - **Dependencies:** TODO #13 (LiteLLM connected to Bedrock)
  - **Affected Files:** None (testing only)
  - **Testing Requirements:** Manual API call OR use `./test-bedrock-models.sh`
  - **Risks:** Low - Haiku already approved, minimal cost
  - **Rollback Plan:** N/A (testing only)
  - **Notes:** Test Haiku FIRST as baseline (already approved, lowest cost)

- [ ] **TODO #15: Test Claude Opus 4.6 text completion** `(Priority: P1, Complexity: S, Owner: DevOps)`
  - **Acceptance Criteria:**
    - **Test Command:**
      ```bash
      curl -X POST http://localhost:8000/v1/chat/completions \
        -H "Authorization: Bearer sk-test-1234567890" \
        -H "Content-Type: application/json" \
        -d '{
          "model": "claude-opus-4-6",
          "messages": [{"role": "user", "content": "What is 2+2?"}],
          "max_tokens": 50
        }'
      ```
    - **HTTP Status:** 200 OK (if 403, model requires approval - see Notes)
    - **Response Validation:**
      - Contains `model: "claude-opus-4-6"` in response
      - Generated text answers the question correctly
      - `usage` object shows token counts
    - **Cost Verification:** Check PostgreSQL for Opus 4.6 entry
    - Expected cost: ~$0.015 per test (higher than Haiku)
    - No Bedrock throttling errors (429)
  - **Dependencies:** TODO #14 (Haiku baseline test passed)
  - **Affected Files:** None (testing only)
  - **Testing Requirements:** Manual API call OR use `./test-bedrock-models.sh`
  - **Risks:** Medium - Model may require manual approval, higher cost than Haiku
  - **Rollback Plan:** N/A (testing only)
  - **Notes:** If model access denied (HTTP 403), manually request access via AWS Bedrock console before continuing

- [ ] **TODO #16: Test Claude Sonnet 4.6 text completion** `(Priority: P1, Complexity: S, Owner: DevOps)`
  - **Acceptance Criteria:**
    - **Test Command:**
      ```bash
      curl -X POST http://localhost:8000/v1/chat/completions \
        -H "Authorization: Bearer sk-test-1234567890" \
        -H "Content-Type: application/json" \
        -d '{
          "model": "claude-sonnet-4-6",
          "messages": [{"role": "user", "content": "Name one color"}],
          "max_tokens": 50
        }'
      ```
    - **HTTP Status:** 200 OK (if 403, model requires approval - see Notes)
    - **Response Validation:**
      - Contains `model: "claude-sonnet-4-6"` in response
      - Generated text names a color
      - Response time < 5 seconds
    - **Cost Verification:** Check PostgreSQL for Sonnet 4.6 entry
    - Expected cost: ~$0.003 per test (between Haiku and Opus)
  - **Dependencies:** TODO #14 (Haiku baseline test passed)
  - **Affected Files:** None (testing only)
  - **Testing Requirements:** Manual API call OR use `./test-bedrock-models.sh`
  - **Risks:** Medium - Model may require manual approval
  - **Rollback Plan:** Use Haiku 4.5 as fallback
  - **Notes:** Sonnet 4.6 may have different approval status than Opus. If denied (HTTP 403), request access via console.

- [ ] **TODO #17: Test Amazon Titan Image Generator V2 (us-east-1)** `(Priority: P1, Complexity: M, Owner: DevOps)`
  - **Acceptance Criteria:**
    - **Test Command:**
      ```bash
      curl -X POST http://localhost:8000/v1/images/generations \
        -H "Authorization: Bearer sk-test-1234567890" \
        -H "Content-Type: application/json" \
        -d '{
          "model": "titan-image-v2",
          "prompt": "A red ball",
          "n": 1,
          "size": "512x512"
        }'
      ```
    - **HTTP Status:** 200 OK (if 403, model requires approval)
    - **Response Validation:**
      - Contains `data` array with image objects
      - Each image has `b64_json` or `url` field
      - Can decode base64 and verify it's a valid image
    - **Region Verification:**
      ```bash
      podman logs litellm 2>&1 | grep -i "us-east-1" | tail -5
      ```
    - **Cost Verification:** Check PostgreSQL for Titan Image V2 entry
    - Expected cost: ~$0.008 per image
  - **Dependencies:** TODO #14 (Haiku baseline test passed)
  - **Affected Files:** None (testing only)
  - **Testing Requirements:** Manual API call + visual image verification OR use `./test-bedrock-models.sh`
  - **Risks:** Medium - Cross-region access (us-east-1), may require approval, higher cost
  - **Rollback Plan:** Remove Titan Image from config if not approved or too expensive
  - **Notes:** Data leaves Canada for image generation - acceptable per requirements. Image generation test is TODO in test script.

- [ ] **TODO #18: Verify LiteLLM cost tracking in PostgreSQL** `(Priority: P2, Complexity: S, Owner: DevOps)`
  - **Acceptance Criteria:**
    - **Query Recent Logs:**
      ```bash
      podman exec litellm-db psql -U llmproxy -d litellm -c \
        "SELECT model, \"startTime\", \"totalCost\", \"promptTokens\", \"completionTokens\" \
         FROM \"LiteLLM_SpendLogs\" ORDER BY \"startTime\" DESC LIMIT 10;"
      ```
    - **Verify All Models Logged:**
      - `claude-haiku-4-5` entry exists
      - `claude-opus-4-6` entry exists (if test passed)
      - `claude-sonnet-4-6` entry exists (if test passed)
      - `titan-image-v2` entry exists (if test passed)
    - **Calculate Total Cost:**
      ```bash
      podman exec litellm-db psql -U llmproxy -d litellm -t -c \
        "SELECT COALESCE(SUM(\"totalCost\"), 0) as total \
         FROM \"LiteLLM_SpendLogs\" \
         WHERE \"startTime\" > NOW() - INTERVAL '1 hour';"
      ```
    - Total cost from all tests < $5 (should be < $0.05)
    - Multi-region costs tracked correctly (ca-central-1 and us-east-1)
    - Cost data includes request/response tokens and pricing
  - **Dependencies:** TODO #14, #15, #16, #17 (all model tests completed)
  - **Affected Files:** None (database query only)
  - **Testing Requirements:** Manual PostgreSQL query
  - **Risks:** Low - Verification only
  - **Rollback Plan:** N/A (read-only operation)
  - **Notes:** PostgreSQL logs confirm LiteLLM is tracking costs correctly for budget monitoring

- [ ] **TODO #19: Run automated test script (optional comprehensive test)** `(Priority: P3, Complexity: S, Owner: DevOps)`
  - **Acceptance Criteria:**
    - **Run Test Script:**
      ```bash
      cd ai/server
      ./test-bedrock-models.sh
      ```
    - All health checks pass
    - All model tests pass (or show clear error if approval needed)
    - PostgreSQL cost tracking verification passes
    - Script outputs summary with pass/fail counts
    - Total cost < $0.10 for full test suite
  - **Dependencies:** TODO #13 (LiteLLM connected to Bedrock)
  - **Affected Files:**
    - `ai/server/test-bedrock-models.sh` (already created)
  - **Testing Requirements:** Execute test script
  - **Risks:** Low - Same tests as individual TODOs, just automated
  - **Rollback Plan:** N/A (testing only)
  - **Notes:** Optional - provides automated testing instead of manual curl commands for TODOs #14-#18

- [ ] **TODO #20: Document Bedrock model access status** `(Priority: P2, Complexity: XS, Owner: Documentation)`
  - **Acceptance Criteria:**
    - Create `ai/BEDROCK-MODELS.md` with current model status
    - Document which models required manual approval (if any)
    - List exact ARNs for all models in ca-central-1 and us-east-1
    - Include cost per 1M tokens for each model
    - Add instructions for requesting new model access via AWS Bedrock console
    - Note multi-region setup (ca-central-1 for text, us-east-1 for images)
    - Include example curl commands for each model
    - Document any throttling limits or quotas encountered
  - **Dependencies:** TODO #18 (all testing complete)
  - **Affected Files:**
    - `ai/BEDROCK-MODELS.md` (create)
  - **Testing Requirements:** Manual review of documentation accuracy
  - **Risks:** Low - Documentation only
  - **Rollback Plan:** N/A
  - **Notes:** Update this doc whenever new models are added or ARNs change

---

## PHASE 3: EC2 Infrastructure (Future Phase - NOT STARTED)

**Status:** 🔲 Deferred to next iteration

**Goal:** Deploy EC2 instance with LiteLLM, OpenCode, automated scheduling, and CloudWatch monitoring.

### Components to Create (Detailed TODOs in next iteration):
- `ai/pulumi/components/ec2.py` - EC2 instance, EBS volume, IAM instance profile
- `ai/pulumi/components/networking.py` - Elastic IP, Security Group, Route53 A record
- `ai/pulumi/components/scheduler.py` - EventBridge schedules (7 AM start, 12 AM stop)
- User data script for EC2 bootstrap (Podman, Nginx, LiteLLM, OpenCode, SSL)
- SSH key configuration via Pulumi config
- Trusted IP configuration for SSH access

### Key Decisions Before Phase 3:
- [ ] Confirm EC2 instance type: t4g.xlarge (16GB RAM) vs t4g.2xlarge (32GB RAM) based on memory analysis in plan
- [ ] Decide on GitHub Actions runner: Deploy now or defer to later phase
- [ ] Confirm SSH key pair name in ca-central-1
- [ ] Determine trusted SSH IP ranges (Bell Canada residential IPs)
- [ ] Verify OpenCode memory leak mitigation strategy (container limits, monitoring, restarts)

**See plan file for full Phase 3 details:** `/Users/mark/.claude/plans/serialized-herding-charm.md`

---

---

## Risks & Mitigation (Greenfield Deployment)

- **Risk:** No dev environment to test before production | **Impact:** Critical - Errors go directly to prod | **Mitigation:** Validate Python code (TODO #7), run `pulumi preview` (TODO #9) before first deployment, test with deployed infrastructure (Phase 2, TODOs #12-#20), keep rollback commands ready (pulumi destroy)
- **Risk:** Python syntax or import errors in Pulumi code | **Impact:** High - First deployment fails | **Mitigation:** Run `scripts/validate-python.py` (TODO #7) before deployment to catch errors early
- **Risk:** Claude Opus 4.6 / Sonnet 4.6 require manual approval | **Impact:** High - Blocks testing after deployment | **Mitigation:** Request access immediately via AWS Bedrock console after deployment, use Haiku 4.5 as fallback for testing
- **Risk:** Titan Image Generator V2 not available in ca-central-1 | **Impact:** Medium - Multi-region complexity | **Mitigation:** Use us-east-1 for images only (acceptable per requirements), policy already supports multi-region
- **Risk:** Real AWS credentials committed to git | **Impact:** Critical - Security breach | **Mitigation:** Verify `.env` in `.gitignore`, never commit credentials, use pre-commit hooks
- **Risk:** Bedrock cost exceeds $75 budget during testing | **Impact:** Medium - Cost overrun | **Mitigation:** Monitor spending daily, use minimal test prompts (< 100 tokens), budget alerts deployed in Phase 1 (TODO #10)
- **Risk:** LiteLLM cost tracking not functioning | **Impact:** Medium - No visibility into spend | **Mitigation:** Verify PostgreSQL logs after each test (TODO #18)
- **Risk:** Multi-region IAM policy errors | **Impact:** High - Bedrock access blocked on first deployment | **Mitigation:** Run `pulumi preview` (TODO #9) to catch errors, verify with AWS CLI after deployment (TODO #11), use specific ARNs not wildcards
- **Risk:** Greenfield deployment fails partially | **Impact:** High - Incomplete infrastructure | **Mitigation:** Validate Python code (TODO #7), run `pulumi preview` (TODO #9) to verify all resources, manual `pulumi up` by user (TODO #10), use `pulumi destroy` to clean up if partial failure, redeploy after fixes
- **Risk:** Budget alerts not configured before deployment | **Impact:** Medium - No cost visibility from first deployment | **Mitigation:** Budget email configuration is mandatory (TODO #8) before first deployment
- **Risk:** Stack initialization errors | **Impact:** High - Cannot deploy | **Mitigation:** Run `pulumi stack init prod` before preview (TODO #9), verify Pulumi backend configured correctly

## Open Questions

- [ ] Has Claude Opus 4.6 model access been requested/approved in ca-central-1? (Check AWS console)
- [ ] Has Claude Sonnet 4.6 model access been requested/approved in ca-central-1? (Check AWS console)
- [ ] What is the exact ARN format for Sonnet 4.6? (Verify in Bedrock console after approval)
- [ ] Should we request Amazon Nova model access for future use? (Deferred to later)
- [ ] What email address should receive budget alerts? (Set via Pulumi config)
- [ ] Should we set up CloudWatch alarms for Bedrock throttling (429 errors)? (Defer to Phase 4)

---

## Constitution Compliance Checklist

- [ ] Python operations use `.venv/` virtual environment (Pulumi in venv)
- [ ] No shell-based file editing (sed/awk/cat) - all changes via Edit tool
- [ ] AWS CLI used for verification, not curl for AWS APIs
- [ ] All file paths use absolute paths or `pathlib.Path`
- [ ] Real credentials NEVER committed to git (`.env` in `.gitignore`)
- [ ] README.md updates included when architecture changes (TODO #15)
- [ ] Pulumi state in S3 backend (verify: `pulumi about`)
- [ ] Copyright headers in all new Python files (bedrock.py, budget.py)

---

---

## Progress Tracking

### Phase 1: Pulumi Infrastructure Deployment (Greenfield)


- **Status:** 🔲 Not Started
- **TODOs:** 11 items (#1-#11)
  - Section 1.1: Pulumi code changes (6 items: #1-#6)
    - Bedrock IAM policy updates for Sonnet 4.6 (#1-#2)
    - Add multi-region support for Titan Image V2 (#3)
    - AWS Budget component creation and integration (#4-#5)
    - DNS CNAME removal from code (#6)
  - Section 1.2: Python code validation (1 item: #7)
    - Validate Python syntax and imports with `scripts/validate-python.py`
  - Section 1.3: Deployment & verification (4 items: #8-#11)
    - Budget email configuration (#8)
    - Pulumi stack initialization, preview and deployment (#9-#10)
    - Greenfield deployment verification (#11)
- **Blocking:** Phase 2
- **Critical Order:** All code changes → Validate Python → Configure → Initialize Stack → Preview → Deploy → Verify
- **Note:** **GREENFIELD** - All resources created new in one `pulumi up` command by user. No existing infrastructure.
- **Resources Created:** IAM user + access keys, IAM policy (Bedrock Sonnet 4.6, Opus 4.6, Haiku 4.5, Titan Image V2 multi-region), AWS Budget ($75/month), SNS topic/subscription

### Phase 2: Testing with Greenfield Deployed Infrastructure


- **Status:** 🔲 Not Started
- **TODOs:** 9 items (#12-#20)
  - LiteLLM configuration and connection (#12-#13)
  - Model testing (#14-#17): Haiku 4.5, Opus 4.6, Sonnet 4.6, Titan Image V2
  - Cost verification and documentation (#18-#20)
- **Blocking:** Phase 3
- **Dependencies:** Phase 1 complete (greenfield infrastructure deployed)
- **Testing Tools:** Manual curl commands AND automated test script (`ai/server/test-bedrock-models.sh`)
- **Note:** **GREENFIELD** - Testing newly deployed infrastructure for first time. Use deployed IAM access keys from Phase 1.

### Phase 3: EC2 Infrastructure


- **Status:** 🔲 Deferred
- **TODOs:** TBD (will be detailed in next iteration)
- **Prerequisites:** Phase 1-2 complete, memory analysis reviewed, EC2 instance type decision made

---

## Next Steps (After Phase 2 Complete)

1. **Verify all models accessible:** Confirm Opus 4.6, Sonnet 4.6, Haiku 4.5, Titan Image V2 working with greenfield infrastructure
2. **Review cost tracking:** Check PostgreSQL logs for accurate spend data from first tests
3. **Verify budget alerts:** Confirm SNS subscription active and receiving budget notifications
4. **Save IAM credentials securely:** Store access keys from `pulumi stack output` in password manager
5. **Memory analysis review:** Re-read plan file for EC2 instance sizing before Phase 3
6. **Create Phase 3 detailed TODO:** Break down EC2 greenfield deployment into granular tasks

---

## Summary

### END OF PHASE 1-2 TODO LIST (GREENFIELD DEPLOYMENT)

*Phase 3 (EC2 Infrastructure) will be detailed in a separate iteration after Phase 1 greenfield deployment and Phase 2 testing are complete and successful.*

### Key Points

- This is a **GREENFIELD** deployment - no existing AWS infrastructure
- All resources will be **created new** in production stack only
- No dev environment - production only
- Must initialize Pulumi stack before first deployment
- IAM credentials will be created fresh (not updating existing)
- DNS component removed from code (never deployed)
