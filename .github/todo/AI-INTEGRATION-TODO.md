# AI Integration Enhancement TODO List

**Created:** 2026-02-06
**Source Prompt:** `ai/INTEGRATION_RECOMMENDATIONS.md`
**Status:** 🔲 Not Started
**Project Phase:** Planning

## Overview
Enhance the AWS Bedrock integration for Claude Code and Continue.dev IDE extensions with security, monitoring, caching, multi-model support, and developer experience improvements. Implementation follows a phased approach from essential security features through performance optimization to advanced developer tools.

## Prerequisites
- [ ] AWS Bedrock infrastructure deployed (traillens-ai submodule)
- [ ] API Gateway proxy configured (ai.dev.traillenshq.com)
- [ ] IAM roles with appropriate permissions
- [ ] Python virtual environment configured (`.venv/`)
- [ ] Pulumi stack access for ai deployment (dev stack)

## Assumptions & Constraints
- Using existing Pulumi infrastructure in `traillens-ai` submodule
- Development environment only (no production deployment for ai project)
- DynamoDB for pay-per-request caching layer (cost-effective for dev)
- CloudWatch for monitoring and metrics
- S3 for long-term storage and static hosting
- Multi-region support in ca-central-1

## Implementation Phases

### Phase 1: Security & Monitoring (High Priority)

- [ ] **Implement API Gateway API Key authentication** `(Priority: P0, Complexity: M, Owner: DevOps)`
  - **Acceptance Criteria:**
    - API Gateway API Key created and enabled
    - Usage plan configured with 10k requests/month quota
    - Throttle settings: 50 burst limit, 100 rate limit
    - API key exported as Pulumi output
    - API key stored in AWS Secrets Manager
    - Documentation updated in README with API key usage
  - **Dependencies:** None
  - **Affected Files:**
    - `ai/pulumi/components/api.py` (modify - add API key, usage plan)
    - `ai/pulumi/__main__.py` (modify - export API key ARN)
    - `ai/README.md` (modify - add API key configuration)
    - `ai/tests/test_api_key.py` (create - test API key validation)
  - **Testing Requirements:** Integration tests for API key authentication
  - **Risks:** Medium - Changes authentication flow, test thoroughly in dev
  - **Rollback Plan:** Remove API key requirement from API Gateway stage
  - **Notes:** Never commit actual API key values, use Secrets Manager references only

- [ ] **Create Lambda authorizer for custom authentication logic** `(Priority: P1, Complexity: M, Owner: Backend)`
  - **Acceptance Criteria:**
    - Lambda function validates API keys from Secrets Manager
    - Returns IAM policy allowing/denying API access
    - Handles invalid/expired keys with 403 response
    - Logs all authentication attempts to CloudWatch
    - Caches authorization decisions for 300 seconds
  - **Dependencies:** TODO #1 (API key infrastructure)
  - **Affected Files:**
    - `ai/lambda/authorizer/handler.py` (create)
    - `ai/pulumi/components/lambda_authorizer.py` (create)
    - `ai/pulumi/components/api.py` (modify - attach authorizer)
    - `ai/tests/test_authorizer.py` (create)
  - **Testing Requirements:** Unit + Integration + Security testing
  - **Risks:** High - Security critical, peer review required
  - **Rollback Plan:** Disable authorizer in API Gateway, revert to IAM auth
  - **Notes:** Follow OWASP API security guidelines, implement rate limiting

- [ ] **Create DynamoDB table for request/response logging** `(Priority: P1, Complexity: S, Owner: DevOps)`
  - **Acceptance Criteria:**
    - DynamoDB table created with request_id (hash) and timestamp (range)
    - DynamoDB streams enabled for analytics
    - TTL configured for 90-day retention
    - GSI on user_id for per-user queries
    - Table tagged with cost allocation tags
  - **Dependencies:** None
  - **Affected Files:**
    - `ai/pulumi/components/logging.py` (create)
    - `ai/pulumi/__main__.py` (modify - add logging component)
    - `ai/tests/test_logging_table.py` (create)
  - **Testing Requirements:** Manual table creation validation
  - **Risks:** Low - No data dependencies, new table only
  - **Rollback Plan:** Delete table if not used
  - **Notes:** Consider GDPR compliance for request logging

- [ ] **Implement Lambda function for asynchronous request logging** `(Priority: P1, Complexity: M, Owner: Backend)`
  - **Acceptance Criteria:**
    - Lambda triggered by API Gateway logs
    - Writes request metadata to DynamoDB (request_id, timestamp, user, model, tokens)
    - Publishes custom CloudWatch metrics (requests/min, tokens, latency)
    - Handles errors gracefully without blocking main request flow
    - Redacts sensitive data from logs (API keys, credentials)
  - **Dependencies:** TODO #3 (DynamoDB logging table)
  - **Affected Files:**
    - `ai/lambda/logger/handler.py` (create)
    - `ai/pulumi/components/lambda_logger.py` (create)
    - `ai/pulumi/components/api.py` (modify - add logging integration)
    - `ai/tests/test_logger_lambda.py` (create)
  - **Testing Requirements:** Unit + Integration tests
  - **Risks:** Medium - Must not impact main request latency
  - **Rollback Plan:** Disable Lambda trigger, logs stop but API continues
  - **Notes:** Use async invocation, no impact on request response time

- [ ] **Configure CloudWatch alarms for monitoring** `(Priority: P1, Complexity: S, Owner: DevOps)`
  - **Acceptance Criteria:**
    - Alarm for error rate >1% of requests (5 min evaluation)
    - Alarm for slow responses >5s p95 latency
    - Alarm for high costs >$100/day
    - Alarm for API quota exhaustion (>80% used)
    - SNS topic for alarm notifications
    - Email notifications configured for team
  - **Dependencies:** TODO #4 (CloudWatch metrics from logger)
  - **Affected Files:**
    - `ai/pulumi/components/alarms.py` (create)
    - `ai/pulumi/__main__.py` (modify - add alarms component)
    - `ai/tests/test_alarms.py` (create)
  - **Testing Requirements:** Manual alarm triggering validation
  - **Risks:** Low - Monitoring only, no functional impact
  - **Rollback Plan:** Disable alarms via Pulumi
  - **Notes:** Use existing SNS topic from infra if available

- [ ] **Add cost allocation tags to all AI resources** `(Priority: P2, Complexity: XS, Owner: DevOps)`
  - **Acceptance Criteria:**
    - Tags applied: Project=TrailLens, Environment=dev, Team=Engineering, CostCenter=R&D, ManagedBy=Pulumi
    - All Lambda functions, API Gateway, DynamoDB tables tagged
    - Tags visible in Cost Explorer
    - Cost allocation report configured in AWS Billing
  - **Dependencies:** None (can run in parallel)
  - **Affected Files:**
    - `ai/pulumi/components/api.py` (modify - add tags)
    - `ai/pulumi/components/lambda_authorizer.py` (modify - add tags)
    - `ai/pulumi/components/logging.py` (modify - add tags)
  - **Testing Requirements:** Manual verification in AWS Console
  - **Risks:** Low - Tags only, no functional changes
  - **Rollback Plan:** Remove tags via Pulumi
  - **Notes:** Constitution requires ManagedBy=Pulumi tag

### Phase 2: Performance & Cost Optimization (Medium Priority)

- [ ] **Create DynamoDB table for response caching** `(Priority: P1, Complexity: S, Owner: DevOps)`
  - **Acceptance Criteria:**
    - DynamoDB table created with cache_key (hash) as primary key
    - TTL attribute configured for automatic cache expiration (24 hours)
    - Pay-per-request billing mode (cost-effective for low traffic)
    - Table tagged with cost allocation tags
    - Table ARN exported as Pulumi output
  - **Dependencies:** None (infrastructure setup)
  - **Affected Files:**
    - `ai/pulumi/components/cache.py` (create)
    - `ai/pulumi/__main__.py` (modify - add cache component)
    - `ai/tests/test_cache_table.py` (create)
  - **Testing Requirements:** Manual table creation validation
  - **Risks:** Low - Pay-per-request, minimal cost for dev traffic
  - **Rollback Plan:** Delete table via Pulumi, caching disabled
  - **Notes:** DynamoDB TTL automatically removes expired cache entries

- [ ] **Implement Lambda cache-check layer with DynamoDB** `(Priority: P1, Complexity: M, Owner: Backend)`
  - **Acceptance Criteria:**
    - Lambda checks DynamoDB for cached responses before calling Bedrock
    - Cache key: SHA256 hash of (model, prompt, temperature, max_tokens)
    - TTL: 24 hours for cached responses (DynamoDB auto-expires)
    - Cache miss triggers Bedrock API call and stores response in DynamoDB
    - CloudWatch metrics for cache hit rate and DynamoDB request count
    - Graceful degradation if DynamoDB unavailable (bypass cache, log error)
  - **Dependencies:** TODO #7 (DynamoDB cache table)
  - **Affected Files:**
    - `ai/lambda/proxy/handler.py` (modify - add cache logic)
    - `ai/lambda/proxy/cache_utils.py` (create)
    - `ai/tests/test_cache_logic.py` (create)
    - `ai/requirements.txt` (modify - add boto3 if not present)
  - **Testing Requirements:** Unit + Integration tests
  - **Risks:** Medium - Critical path change, test thoroughly
  - **Rollback Plan:** Feature flag ENABLE_CACHE=false, bypass cache layer
  - **Notes:** DynamoDB TTL handles automatic cache invalidation, no manual cleanup needed

- [ ] **Add multi-model support configuration** `(Priority: P1, Complexity: M, Owner: Backend)`
  - **Acceptance Criteria:**
    - Support 3 models: Haiku (autocomplete), Sonnet (coding), Opus (architecture)
    - Request header "X-Model-Type" selects model (default: sonnet)
    - Lambda routes to appropriate Bedrock model ID
    - CloudWatch metrics per model (usage, cost, latency)
    - Documentation updated with model selection guide
  - **Dependencies:** None (can run in parallel with caching)
  - **Affected Files:**
    - `ai/lambda/proxy/handler.py` (modify - add model routing)
    - `ai/lambda/proxy/models.py` (create - model configuration)
    - `ai/pulumi/components/bedrock.py` (modify - enable all 3 models)
    - `ai/README.md` (modify - document model selection)
    - `ai/tests/test_multi_model.py` (create)
  - **Testing Requirements:** Integration tests for all 3 models
  - **Risks:** Medium - Cost implications, monitor usage closely
  - **Rollback Plan:** Remove header parsing, default to Sonnet only
  - **Notes:** Haiku for cost optimization, Opus for complex tasks only

- [ ] **Implement WebSocket API for streaming responses** `(Priority: P2, Complexity: L, Owner: Backend)`
  - **Acceptance Criteria:**
    - API Gateway WebSocket API created
    - Lambda handles $connect, $disconnect, $default routes
    - Bedrock streaming API integration (tokens stream as generated)
    - Connection state stored in DynamoDB
    - WebSocket URL exported as Pulumi output
    - Client SDK example provided (TypeScript)
  - **Dependencies:** None (parallel track)
  - **Affected Files:**
    - `ai/pulumi/components/websocket_api.py` (create)
    - `ai/lambda/websocket/handler.py` (create)
    - `ai/lambda/websocket/connections_table.py` (create)
    - `ai/examples/websocket_client.ts` (create)
    - `ai/tests/test_websocket.py` (create)
  - **Testing Requirements:** Integration + Manual testing with IDE extension
  - **Risks:** High - Complex, new protocol, extensive testing needed
  - **Rollback Plan:** Deploy WebSocket as separate optional endpoint
  - **Notes:** Lower perceived latency for users, better UX

### Phase 3: Developer Experience (Low Priority)

- [ ] **Create S3 bucket for prompt template library** `(Priority: P2, Complexity: S, Owner: DevOps)`
  - **Acceptance Criteria:**
    - S3 bucket created with versioning enabled
    - Bucket policy allows read access from Lambda
    - Folder structure: templates/{python-function,unit-test,code-review,refactor}/
    - Sample templates uploaded for each category
    - Bucket ARN exported as Pulumi output
  - **Dependencies:** None
  - **Affected Files:**
    - `ai/pulumi/components/template_storage.py` (create)
    - `ai/templates/python-function.txt` (create)
    - `ai/templates/unit-test.txt` (create)
    - `ai/templates/code-review.txt` (create)
    - `ai/templates/refactor.txt` (create)
    - `ai/tests/test_template_storage.py` (create)
  - **Testing Requirements:** Manual S3 access validation
  - **Risks:** Low - Storage only, no runtime dependencies
  - **Rollback Plan:** Delete bucket via Pulumi
  - **Notes:** Templates should reference CONSTITUTION files

- [ ] **Implement Lambda function for template fetching** `(Priority: P2, Complexity: M, Owner: Backend)`
  - **Acceptance Criteria:**
    - Lambda fetches templates from S3 by name
    - Template rendering with Jinja2 (variable substitution)
    - API endpoint: GET /templates/{name}
    - Returns 404 for missing templates
    - CloudWatch logs for template usage
    - Template versioning support (query param ?version=X)
  - **Dependencies:** TODO #11 (S3 template bucket)
  - **Affected Files:**
    - `ai/lambda/templates/handler.py` (create)
    - `ai/pulumi/components/api.py` (modify - add /templates route)
    - `ai/requirements.txt` (modify - add Jinja2)
    - `ai/tests/test_template_lambda.py` (create)
  - **Testing Requirements:** Unit + Integration tests
  - **Risks:** Low - Read-only operation, no data modification
  - **Rollback Plan:** Remove /templates route from API Gateway
  - **Notes:** Cache templates in Lambda memory for performance

- [ ] **Implement request context injection Lambda** `(Priority: P2, Complexity: M, Owner: Backend)`
  - **Acceptance Criteria:**
    - Lambda parses request for repo name, branch, file path
    - Fetches project metadata from DynamoDB (language, standards)
    - Injects context into prompt: "You are working on {repo} in {language}. Follow {standards}."
    - Context injection optional via header "X-Inject-Context: true"
    - Metadata table populated with TrailLens projects
  - **Dependencies:** None (parallel track)
  - **Affected Files:**
    - `ai/lambda/proxy/handler.py` (modify - add context injection)
    - `ai/lambda/proxy/context.py` (create)
    - `ai/pulumi/components/context_metadata.py` (create - DynamoDB table)
    - `ai/data/project_metadata.json` (create - seed data)
    - `ai/tests/test_context_injection.py` (create)
  - **Testing Requirements:** Unit + Integration tests
  - **Risks:** Medium - Changes prompt content, may affect responses
  - **Rollback Plan:** Feature flag ENABLE_CONTEXT_INJECTION=false
  - **Notes:** Include CONSTITUTION-*.md files in context for standards

- [ ] **Create developer dashboard static website** `(Priority: P3, Complexity: L, Owner: Frontend)`
  - **Acceptance Criteria:**
    - React dashboard with usage charts (requests, costs, latency)
    - S3 bucket for static hosting + CloudFront distribution
    - API endpoint for fetching metrics from CloudWatch
    - User management: API key generation, rotation, revocation
    - Authentication: Cognito user pool integration
    - Responsive design, works on mobile
  - **Dependencies:** TODO #4 (CloudWatch metrics), TODO #1 (API keys)
  - **Affected Files:**
    - `ai/dashboard/src/*` (create - React app)
    - `ai/pulumi/components/dashboard.py` (create - S3 + CloudFront)
    - `ai/lambda/dashboard_api/handler.py` (create - metrics API)
    - `ai/tests/test_dashboard.py` (create)
  - **Testing Requirements:** E2E tests + Manual QA
  - **Risks:** Medium - User-facing, UI/UX quality important
  - **Rollback Plan:** Remove CloudFront distribution, dashboard offline
  - **Notes:** Use existing Cognito from infra submodule for auth

### Phase 4: Development Tools (Optional)

- [ ] **Create Docker container for local Bedrock proxy** `(Priority: P3, Complexity: M, Owner: DevOps)`
  - **Acceptance Criteria:**
    - Dockerfile creates local proxy server on port 8080
    - Proxy intercepts Bedrock API calls
    - Returns mock responses for testing (no AWS costs)
    - Supports all 3 models (Haiku, Sonnet, Opus)
    - Docker Compose file for easy startup
    - Documentation for local development setup
  - **Dependencies:** None (parallel track)
  - **Affected Files:**
    - `ai/local/Dockerfile` (create)
    - `ai/local/docker-compose.yml` (create)
    - `ai/local/proxy_server.py` (create)
    - `ai/local/mock_responses/` (create - sample responses)
    - `ai/README.md` (modify - local development section)
  - **Testing Requirements:** Manual Docker testing
  - **Risks:** Low - Development tool only, no production impact
  - **Rollback Plan:** Delete local/ directory
  - **Notes:** Use .devcontainer integration for seamless experience

- [ ] **Create configuration examples for IDE extensions** `(Priority: P2, Complexity: XS, Owner: Documentation)`
  - **Acceptance Criteria:**
    - Claude Code config example (~/.claude/config.json)
    - Continue.dev config example (.vscode/settings.json)
    - Environment variable setup instructions
    - Troubleshooting guide for common issues
    - Video walkthrough of setup process
  - **Dependencies:** All previous TODOs (needs API keys, endpoints)
  - **Affected Files:**
    - `ai/docs/claude-code-setup.md` (create)
    - `ai/docs/continue-dev-setup.md` (create)
    - `ai/examples/claude-config.json` (create)
    - `ai/examples/vscode-settings.json` (create)
    - `ai/README.md` (modify - link to setup guides)
  - **Testing Requirements:** Manual validation with both IDE extensions
  - **Risks:** Low - Documentation only
  - **Rollback Plan:** N/A - documentation can be updated anytime
  - **Notes:** Include screenshots, step-by-step instructions

## Risks & Mitigation

- **Risk:** API key leakage | **Impact:** Critical | **Mitigation:** Store in Secrets Manager, rotate regularly, never commit to git, use IAM policies for access control
- **Risk:** Unexpected AWS costs | **Impact:** High | **Mitigation:** CloudWatch alarms for cost thresholds, usage quotas, rate limiting, regular cost reviews, DynamoDB pay-per-request mode
- **Risk:** Cache poisoning | **Impact:** Low | **Mitigation:** Hash-based cache keys (SHA256), DynamoDB TTL auto-expiration (24h), IAM permissions restrict write access
- **Risk:** WebSocket connection limits | **Impact:** Medium | **Mitigation:** DynamoDB connection tracking, connection timeout, graceful degradation to REST API
- **Risk:** Bedrock API rate limits | **Impact:** High | **Mitigation:** Request queueing, exponential backoff, fallback to different models, user notifications
- **Risk:** Lambda cold starts affecting latency | **Impact:** Medium | **Mitigation:** DynamoDB caching reduces Bedrock calls, connection pooling for DynamoDB

## Open Questions

- [ ] What is the team size and expected daily request volume?
- [ ] Should we implement OAuth2 provider support (GitHub, Google) for dashboard?
- [ ] Do we need request batching for cost optimization?
- [ ] Should we support custom fine-tuned models in the future?
- [ ] What is the data retention policy for request logs (GDPR compliance)?
- [ ] Should we implement prompt injection detection/filtering?

## Constitution Compliance Checklist

- [ ] Python operations use `.venv/` virtual environment
- [ ] No shell-based file editing (sed/awk/cat) in any scripts
- [ ] All HTTP calls use requests/httpx libraries, not subprocess
- [ ] README.md updates included for all new features
- [ ] All file paths use `pathlib.Path` or `os.path.join`
- [ ] Infrastructure code ONLY in ai/ submodule (proper separation)
- [ ] No Makefiles - use Python scripts or npm scripts
- [ ] All source files include TrailLensCo copyright headers
- [ ] Type hints on all Python function signatures
- [ ] Lambda functions follow Python coding standards (black, isort, flake8)
- [ ] DynamoDB tables use consistent naming: {stack_name}-{resource}
- [ ] All resources tagged with cost allocation tags
- [ ] Development environment only (no production deployment)
- [ ] Git commits follow submodule-first workflow
- [ ] No AI promotional content in code/comments/commits
