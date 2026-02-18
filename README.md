# TrailLens AI Infrastructure

Simplified AWS Bedrock infrastructure for single developer use with Continue.dev.

Supports **Claude Opus 4.6**, **Claude Sonnet 4.5**, and **Claude Haiku 4.5** for AI-assisted development.

## Quick Start

```bash
# Setup environment
cd pulumi
source ../scripts/setup-env.sh

# Deploy
pulumi stack select prod
pulumi up

# Get credentials
pulumi stack output access_key_id
pulumi stack output secret_access_key --show-secrets
```

## What This Deploys

- **IAM User** - Dedicated user for Bedrock API access
- **IAM Policies** - Permissions for Claude Opus 4.6, Sonnet 4.5, and Haiku 4.5
- **Access Keys** - AWS credentials for authentication
- **DNS CNAME** - `ai.traillenshq.com` → `bedrock-runtime.ca-central-1.amazonaws.com`

## Supported Models

| Model                   | Use Case                 | Best For                                      |
| ----------------------- | ------------------------ | --------------------------------------------- |
| **Claude Opus 4.6**     | Planning & Architecture  | Complex design, system architecture           |
| **Claude Sonnet 4.5**   | General Coding           | Writing functions, bug fixes, code reviews    |
| **Claude Haiku 4.5**    | Autocomplete             | Inline completion, quick suggestions          |

## Setup

See **[SETUP.md](SETUP.md)** for complete configuration instructions including:

1. AWS credentials setup
2. Continue.dev configuration for all three models
3. Model selection guide (which model for which task)
4. Testing and troubleshooting

## Quick Continue.dev Config

Add to `~/.continue/config.json`:

```json
{
  "models": [
    {
      "title": "Claude Opus 4.6 (Planning)",
      "provider": "bedrock",
      "model": "anthropic.claude-opus-4-6",
      "region": "ca-central-1",
      "contextLength": 200000
    },
    {
      "title": "Claude Sonnet 4.5 (Coding)",
      "provider": "bedrock",
      "model": "anthropic.claude-sonnet-4-5-v2:0",
      "region": "ca-central-1",
      "contextLength": 200000
    },
    {
      "title": "Claude Haiku 4.5 (Fast)",
      "provider": "bedrock",
      "model": "anthropic.claude-haiku-4-5-20251001:0",
      "region": "ca-central-1",
      "contextLength": 200000
    }
  ]
}
```

Configure AWS credentials in `~/.aws/credentials`:

```ini
[traillens-ai]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
region = ca-central-1
```

## Architecture

```text
┌─────────────────────────────────────────────┐
│         ai.traillenshq.com (CNAME)          │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│   bedrock-runtime.ca-central-1.amazonaws.com │
│              AWS Bedrock                     │
│   ┌─────────────────────────────────┐       │
│   │  Claude Opus 4.6 (Planning)     │       │
│   │  Claude Sonnet 4.5 (Coding)     │       │
│   │  Claude Haiku 4.5 (Completion)  │       │
│   └─────────────────────────────────┘       │
└─────────────────────────────────────────────┘
```

## Key Features

- **Simplified Infrastructure** - Just IAM and DNS, no complex API Gateway
- **Multi-Model Support** - Three Claude models for different use cases
- **Cost-Optimized** - Use Haiku for cheap autocomplete, Opus only when needed
- **Single Developer** - Designed for individual use, not team infrastructure

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development guidance.

## License

Copyright (c) 2025 TrailLensCo. All rights reserved.
