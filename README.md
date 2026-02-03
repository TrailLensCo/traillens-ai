# TrailLens AI Infrastructure

AWS Bedrock deployment for Claude Sonnet 4.5, enabling AI-assisted development with Claude Code and Continue.dev VSCode extensions.

## Quick Start

```bash
# Setup environment
cd pulumi
source ../scripts/setup-env.sh

# Deploy to dev
pulumi stack select dev
pulumi up

# Deploy to prod
pulumi stack select prod
pulumi up
```

## What This Deploys

- **AWS Bedrock**: Claude Sonnet 4.5 model access
- **API Gateway**: REST API proxy for Bedrock
- **Custom Domains**:
  - Development: `ai.dev.traillenshq.com`
  - Production: `ai.traillenshq.com`
- **IAM Roles**: Secure access policies for Bedrock
- **DNS**: Route53 A records and ACM certificates

## Usage

### Configure VSCode Extensions

#### Continue.dev

Add to your Continue configuration (`~/.continue/config.json`):

```json
{
  "models": [
    {
      "title": "Claude Sonnet 4.5 (Bedrock)",
      "provider": "bedrock",
      "model": "anthropic.claude-sonnet-4-5-v2:0",
      "region": "ca-central-1",
      "endpoint": "https://ai.traillenshq.com"
    }
  ]
}
```

#### Claude Code

Set environment variables:

```bash
export CLAUDE_API_BASE_URL="https://ai.traillenshq.com"
export AWS_REGION="ca-central-1"
```

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                     ai.traillenshq.com                      │
│                    (Route53 + ACM Cert)                     │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                            │
│                   (Regional Endpoint)                       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      AWS Bedrock                            │
│              Claude Sonnet 4.5 v2 Model                     │
└─────────────────────────────────────────────────────────────┘
```

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development guidance.

## License

Copyright (c) 2025 TrailLensCo. All rights reserved.
