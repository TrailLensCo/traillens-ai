# CLAUDE.md - TrailLens AI Infrastructure

This file provides guidance to Claude Code when working with the TrailLens AI infrastructure repository.

## AI Model Requirement

**CRITICAL**: All code generation, documentation, refactoring, and AI-assisted development work **MUST** use **the latest Claude Sonnet** model exclusively.

**If the latest Claude Sonnet is not available or any other model is selected, STOP ALL GENERATION IMMEDIATELY and inform the user to switch to the latest Claude Sonnet.**

## Repository Overview

TrailLens AI Infrastructure - AWS Bedrock deployment with the latest Claude Sonnet for AI-assisted development.

**CRITICAL PYTHON REQUIREMENT**: This project **REQUIRES Python 3.14**. This is the current Python version and MUST be used for all development, testing, and deployment. Do NOT use older Python versions.

This repository deploys:

- AWS Bedrock with direct IAM user access
- IAM roles and policies for secure Bedrock access
- AWS Budget for cost monitoring and alerts
- LiteLLM proxy for OpenAI-compatible API (local/Docker)

## Architecture

### Components

1. **Bedrock** ([components/bedrock.py](pulumi/components/bedrock.py))
   - IAM user with programmatic access
   - IAM policies for Bedrock model access
   - Access credentials for direct API calls

2. **Budget** ([components/budget.py](pulumi/components/budget.py))
   - AWS Budget for cost monitoring
   - SNS topic for budget alerts
   - Email notifications for cost thresholds

### Environment Setup

**Development**: `ai.dev.traillenshq.com`
**Production**: `ai.traillenshq.com`

Both environments use the `ca-central-1` region exclusively.

## Essential Commands

### Setup

```bash
# Initialize environment (one-time)
cd pulumi
source ../scripts/setup-env.sh

# Install dependencies
pip install -r requirements.txt
```

### Deployment

```bash
# Deploy to dev
cd pulumi
source ../scripts/setup-env.sh
pulumi stack select dev
pulumi up

# Deploy to prod
cd pulumi
source ../scripts/setup-env.sh
pulumi stack select prod
pulumi up
```

### Verification

```bash
# Check stack outputs
pulumi stack output

# Test API endpoint
curl https://ai.dev.traillenshq.com/health

# View logs
aws logs tail /aws/apigateway/traillens-ai-dev --follow
```

## Pulumi Configuration

Configuration is managed via stack files:
- [Pulumi.dev.yaml](pulumi/Pulumi.dev.yaml) - Development environment
- [Pulumi.prod.yaml](pulumi/Pulumi.prod.yaml) - Production environment

### Key Configuration Values

- `bedrock_model_id`: Model identifier (use the latest Claude Sonnet model ID available in AWS Bedrock)
- `domain`: Custom domain name
- `region`: AWS region (must be `ca-central-1`)

## Integration with Claude Code / Continue.dev

### Environment Variables

To configure VSCode extensions to use the deployed Bedrock endpoint:

```bash
# For Continue.dev
export CONTINUE_API_ENDPOINT="https://ai.traillenshq.com"
export CONTINUE_MODEL="<latest-claude-sonnet-model-id>"

# For Claude Code (if custom endpoint supported)
export CLAUDE_API_BASE_URL="https://ai.traillenshq.com"
```

### API Authentication

The deployed API uses AWS IAM authentication. Configure your AWS credentials:

```bash
# Using AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="ca-central-1"
```

## Development Workflow

### Making Infrastructure Changes

1. Create topic branch:
   ```bash
   git checkout -b topic/feature-name
   ```

2. Make changes to Pulumi code

3. Test in dev environment:
   ```bash
   cd pulumi
   source ../scripts/setup-env.sh
   pulumi stack select dev
   pulumi preview  # Review changes
   pulumi up       # Deploy
   ```

4. Commit and push:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin topic/feature-name
   ```

5. Create PR:
   ```bash
   gh pr create --fill
   ```

6. After PR approval → **MANUAL PRODUCTION DEPLOYMENT REQUIRED** (see Production Deployment Policy below)

### 🚨 PRODUCTION DEPLOYMENT RESTRICTION (CRITICAL)

**IMMUTABLE RULE:** NEVER deploy to production automatically or via AI assistance.

Production deployments are **STRICTLY MANUAL ONLY** and require explicit human approval and execution.

**ABSOLUTE PROHIBITIONS:**

- ❌ **NEVER** run `pulumi up` on production AI stack
- ❌ **NEVER** run `pulumi up -s prod` or deployment scripts targeting production
- ❌ **NEVER** update production Bedrock IAM configuration automatically
- ❌ **NEVER** suggest or recommend production deployments

**PERMITTED ACTIONS:**

- ✅ Run `pulumi preview -s prod` to see what WOULD change (read-only)
- ✅ Deploy to dev environment with user confirmation
- ✅ Prepare deployment plans and document changes
- ✅ Review and validate infrastructure code

**IF PRODUCTION DEPLOYMENT IS REQUESTED:**

1. **STOP** and confirm the target environment
2. If target is production → **REFUSE** and explain this policy
3. Provide instructions for manual deployment instead
4. Document what needs to be deployed and why

**Violating this policy could result in AI service outages affecting all applications.**

### Code Standards

Follow Python standards from main repository [CONSTITUTION-PYTHON.md](../.github/CONSTITUTION-PYTHON.md):
- Type hints on all functions
- Google/NumPy docstrings
- Black formatting (88 char lines)
- Import order: stdlib → third-party → local
- Copyright headers on all source files

## Troubleshooting

### Certificate Validation Issues

If ACM certificate validation fails:
```bash
# Check validation records
aws acm describe-certificate --certificate-arn <arn>

# Verify DNS propagation
dig ai.dev.traillenshq.com
```

### Bedrock Access Denied

Ensure Bedrock model access is enabled in AWS Console:
```
AWS Console → Bedrock → Model access → Manage model access
Enable: Latest Claude Sonnet model
```

## Outputs

After deployment, these outputs are available:

- `iam_user_name`: IAM user for Bedrock access
- `iam_user_arn`: ARN of the IAM user
- `access_key_id`: AWS access key ID (sensitive)
- `secret_access_key`: AWS secret access key (sensitive)
- `region`: AWS region (ca-central-1)
- `budget_topic_arn`: SNS topic for budget alerts
- `budget_id`: AWS Budget identifier
- `models`: Supported Bedrock model IDs

## Related Documentation

- Main repository: [../CLAUDE.md](../CLAUDE.md)
- Infrastructure repo: [../infra/CLAUDE.md](../infra/CLAUDE.md)
- Python standards: [../.github/CONSTITUTION-PYTHON.md](../.github/CONSTITUTION-PYTHON.md)
- AWS Bedrock documentation: https://docs.aws.amazon.com/bedrock/

## Important Rules

- **Never commit to main** - Use `topic/*` branches
- **Deploy to dev first** - Test before production
- **Region enforcement** - All resources in `ca-central-1`
- **No AI advertising** - No promotional content in commits
- **Copyright headers** - Required in all source files
- **Virtual envs** - Named `venv/` in pulumi directory, never committed
