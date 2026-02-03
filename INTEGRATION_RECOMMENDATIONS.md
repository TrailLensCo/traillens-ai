# Integration Recommendations for Claude Code and Continue.dev

This document provides recommendations for additional components and configurations to enhance the integration of Claude Code and Continue.dev with AWS Bedrock.

## Current Implementation

The current infrastructure deploys:
- AWS Bedrock with Claude Sonnet 4.5 model access
- API Gateway as a proxy for Bedrock API calls
- Custom domains with HTTPS (ai.traillenshq.com)
- IAM roles with appropriate permissions

## Recommended Additional Components

### 1. API Key Management

**Purpose**: Secure access control for IDE extensions without exposing AWS credentials.

**Implementation**:
- API Gateway API Keys for authentication
- Usage plans to control rate limits and quotas
- Lambda authorizer for custom authentication logic

**Benefits**:
- Developers can use simple API keys instead of AWS credentials
- Centralized usage tracking and billing
- Rate limiting prevents abuse

**Code Addition**:
```python
# In components/api.py
api_key = aws.apigateway.ApiKey(
    f"{stack_name}-api-key",
    name=f"{stack_name}-dev-key",
    enabled=True,
)

usage_plan = aws.apigateway.UsagePlan(
    f"{stack_name}-usage-plan",
    api_stages=[aws.apigateway.UsagePlanApiStageArgs(
        api_id=api.id,
        stage=stage.stage_name,
    )],
    quota_settings=aws.apigateway.UsagePlanQuotaSettingsArgs(
        limit=10000,  # 10k requests per month
        period="MONTH",
    ),
    throttle_settings=aws.apigateway.UsagePlanThrottleSettingsArgs(
        burst_limit=50,
        rate_limit=100,
    ),
)
```

### 2. Request Caching Layer

**Purpose**: Reduce costs and improve response times for repeated queries.

**Implementation**:
- ElastiCache (Redis) for caching common requests
- Lambda function to check cache before calling Bedrock
- TTL configuration for cache invalidation

**Benefits**:
- 50-80% cost reduction for repeated queries
- Sub-100ms response times for cached requests
- Reduced load on Bedrock service

**Architecture**:
```text
IDE Request → API Gateway → Lambda (cache check) → ElastiCache
                                 ↓ (cache miss)
                              Bedrock API
```

### 3. Request/Response Logging and Analytics

**Purpose**: Monitor usage patterns, debug issues, and optimize performance.

**Implementation**:
- DynamoDB table for request logs
- CloudWatch custom metrics
- Lambda function to log requests asynchronously
- S3 for long-term storage of request/response pairs

**Benefits**:
- Track which developers use which features
- Identify performance bottlenecks
- Debug integration issues
- Compliance and audit trail

**Schema**:
```python
logs_table = aws.dynamodb.Table(
    f"{stack_name}-request-logs",
    attributes=[
        aws.dynamodb.TableAttributeArgs(
            name="request_id",
            type="S",
        ),
        aws.dynamodb.TableAttributeArgs(
            name="timestamp",
            type="N",
        ),
    ],
    hash_key="request_id",
    range_key="timestamp",
    stream_enabled=True,
    stream_view_type="NEW_AND_OLD_IMAGES",
)
```

### 4. WebSocket API for Streaming Responses

**Purpose**: Enable real-time streaming of Claude responses for better UX.

**Implementation**:
- API Gateway WebSocket API
- Lambda function to handle WebSocket connections
- Bedrock streaming API integration

**Benefits**:
- Real-time response streaming (tokens appear as generated)
- Better user experience in IDE
- Lower perceived latency

**Code**:
```python
ws_api = aws.apigatewayv2.Api(
    f"{stack_name}-ws-api",
    name=f"{stack_name}-websocket",
    protocol_type="WEBSOCKET",
    route_selection_expression="$request.body.action",
)
```

### 5. Multi-Model Support

**Purpose**: Support different Claude models for different use cases.

**Implementation**:
- Configuration for multiple Bedrock models (Haiku, Sonnet, Opus)
- Lambda routing logic based on request parameters
- Cost tracking per model

**Benefits**:
- Use Haiku for simple autocomplete (faster, cheaper)
- Use Sonnet for general coding tasks
- Use Opus for complex architectural decisions
- Optimize cost vs. performance

**Configuration**:
```yaml
models:
  - id: anthropic.claude-3-haiku-20240307-v1:0
    name: haiku
    use_case: autocomplete
  - id: anthropic.claude-sonnet-4-5-v2:0
    name: sonnet
    use_case: coding
  - id: anthropic.claude-opus-4-5-v1:0
    name: opus
    use_case: architecture
```

### 6. Developer Dashboard

**Purpose**: Provide visibility into usage, costs, and performance.

**Implementation**:
- Static website hosted on S3 + CloudFront
- API for fetching metrics from CloudWatch
- Charts for requests, costs, latency
- User management (API key generation)

**Benefits**:
- Self-service API key management
- Usage visibility for budget planning
- Performance monitoring
- Team metrics

### 7. Request Context Injection

**Purpose**: Automatically inject project context (repo name, branch, file path) into requests.

**Implementation**:
- Lambda function to parse and enrich requests
- DynamoDB table for project metadata
- Context template library

**Benefits**:
- Claude gets better context about the project
- More relevant responses
- Consistent code style across the team

**Example**:
```json
{
  "prompt": "Add error handling to this function",
  "context": {
    "repo": "traillens-ai",
    "branch": "main",
    "file": "pulumi/components/api.py",
    "language": "python",
    "standards": ["CONSTITUTION-PYTHON.md"]
  }
}
```

### 8. Cost Allocation Tags

**Purpose**: Track and allocate costs by team, project, or developer.

**Implementation**:
- Tag all resources with cost allocation tags
- Lambda function to tag requests with user/project info
- Cost Explorer reports

**Benefits**:
- Accurate cost attribution
- Budget alerts per team
- ROI analysis

**Tags**:
```python
tags = {
    "Project": "TrailLens",
    "Environment": environment,
    "Team": "Engineering",
    "CostCenter": "R&D",
    "ManagedBy": "Pulumi",
}
```

### 9. Prompt Template Library

**Purpose**: Standardize common prompts across the team.

**Implementation**:
- S3 bucket for template storage
- Lambda function to fetch and render templates
- Template versioning

**Benefits**:
- Consistent code generation
- Best practices enforcement
- Easy updates to coding standards

**Templates**:
- `python-function`: Generate Python function with type hints
- `unit-test`: Generate pytest test cases
- `code-review`: Review code against CONSTITUTION files
- `refactor`: Refactor code following best practices

### 10. Local Development Proxy

**Purpose**: Enable local development without AWS credentials.

**Implementation**:
- Docker container with local Bedrock proxy
- LocalStack integration for testing
- Environment variable switching

**Benefits**:
- Faster development iteration
- No AWS costs for testing
- Works offline

**Docker Compose**:
```yaml
services:
  bedrock-proxy:
    image: traillens/bedrock-proxy:latest
    ports:
      - "8080:8080"
    environment:
      - BEDROCK_ENDPOINT=http://localstack:4566
```

## Priority Recommendations

Based on impact and implementation complexity:

### High Priority (Implement First)
1. **API Key Management** - Essential for security and usability
2. **Request/Response Logging** - Critical for debugging and monitoring
3. **Multi-Model Support** - Cost optimization and flexibility

### Medium Priority (Implement Next)
4. **Request Caching Layer** - Significant cost savings
5. **WebSocket API** - Better UX for developers
6. **Cost Allocation Tags** - Important for budget management

### Low Priority (Nice to Have)
7. **Developer Dashboard** - Self-service management
8. **Request Context Injection** - Enhanced AI responses
9. **Prompt Template Library** - Standardization
10. **Local Development Proxy** - Development experience

## Implementation Phases

### Phase 1: Security & Monitoring (Week 1-2)
- API Key Management
- Request/Response Logging
- Cost Allocation Tags

### Phase 2: Performance & Cost (Week 3-4)
- Request Caching Layer
- Multi-Model Support
- WebSocket API (streaming)

### Phase 3: Developer Experience (Week 5-6)
- Developer Dashboard
- Prompt Template Library
- Request Context Injection

### Phase 4: Development Tools (Week 7-8)
- Local Development Proxy
- Enhanced debugging tools
- Team analytics

## Configuration Examples

### Claude Code Configuration

Create `~/.claude/config.json`:

```json
{
  "api": {
    "endpoint": "https://ai.traillenshq.com",
    "key": "${CLAUDE_API_KEY}",
    "region": "ca-central-1"
  },
  "models": {
    "default": "sonnet",
    "autocomplete": "haiku",
    "architecture": "opus"
  },
  "context": {
    "inject_repo_info": true,
    "include_constitution": true
  }
}
```

### Continue.dev Configuration

Add to `.vscode/settings.json`:

```json
{
  "continue.telemetryEnabled": false,
  "continue.models": [
    {
      "title": "Claude Sonnet (TrailLens)",
      "provider": "bedrock",
      "model": "anthropic.claude-sonnet-4-5-v2:0",
      "apiKey": "${BEDROCK_API_KEY}",
      "apiBase": "https://ai.traillenshq.com",
      "contextLength": 200000,
      "completionOptions": {
        "temperature": 0.2,
        "topP": 0.9,
        "maxTokens": 4096
      }
    }
  ]
}
```

## Monitoring and Alerting

### CloudWatch Alarms

Set up alarms for:
- High error rate (>1% of requests)
- Slow response times (>5s p95)
- High costs (>$100/day)
- API quota exhaustion

### Metrics to Track

- Requests per minute
- Token usage (input/output)
- Response latency (p50, p95, p99)
- Error rate by type
- Cost per request
- Cache hit rate (if caching enabled)

## Security Considerations

1. **API Keys**: Rotate regularly, store in Secrets Manager
2. **Rate Limiting**: Prevent abuse and control costs
3. **Input Validation**: Sanitize prompts before sending to Bedrock
4. **Output Filtering**: Remove sensitive data from responses
5. **Audit Logging**: Log all requests for compliance
6. **VPC Endpoints**: Use VPC endpoints for Bedrock to avoid internet traffic

## Cost Optimization

1. **Cache common queries**: 50-80% cost reduction
2. **Use appropriate models**: Haiku for simple tasks
3. **Implement request batching**: Reduce API overhead
4. **Set token limits**: Prevent runaway costs
5. **Monitor usage patterns**: Identify and optimize expensive queries

## Next Steps

1. Review recommendations with the team
2. Prioritize based on immediate needs
3. Create implementation tickets
4. Set up monitoring and alerting
5. Document integration patterns
6. Train team on new features

## Resources

- AWS Bedrock Documentation: https://docs.aws.amazon.com/bedrock/
- API Gateway Best Practices: https://docs.aws.amazon.com/apigateway/latest/developerguide/best-practices.html
- Claude API Documentation: https://docs.anthropic.com/
- Continue.dev Documentation: https://continue.dev/docs
