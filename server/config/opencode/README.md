# OpenCode Configuration for TrailLens AI

This directory contains the OpenCode configuration for using AWS Bedrock models via LiteLLM.

## What is OpenCode?

OpenCode is an AI-powered code editor and development tool that supports both:

- **VSCode Extension**: AI assistance directly in Visual Studio Code
- **TUI (Terminal UI)**: Command-line interface for AI-powered coding

## Installation

### Quick Install (Recommended)

Run the install script from the project root:

```bash
./ai/scripts/install-opencode.sh
```

### Manual Install

1. Copy configuration to OpenCode directory:

```bash
# Create directory
mkdir -p ~/.config/opencode

# Extract API key from .env
LITELLM_KEY=$(grep "^LITELLM_MASTER_KEY=" ../../.env | cut -d '=' -f2-)

# Copy config and substitute API key
sed "s/{env:LITELLM_MASTER_KEY}/${LITELLM_KEY}/g" opencode.json > ~/.config/opencode/opencode.json
```

## Configuration Details

### Models Configured

The configuration includes 8 models from AWS Bedrock via LiteLLM:

1. **Claude Sonnet 4.6** (Default)
   - Best for: General coding tasks, bug fixes, code reviews
   - Context: 200K tokens
   - Output: 8,192 tokens

2. **Claude Haiku 4.5**
   - Best for: Quick questions, fast responses
   - Context: 200K tokens
   - Output: 8,192 tokens

3. **Claude 3.5 Haiku**
   - Best for: Budget-conscious fast tasks
   - Context: 200K tokens
   - Output: 8,192 tokens

4. **Claude Opus 4.6**
   - Best for: Complex architectural decisions, system design
   - Context: 200K tokens
   - Output: 8,192 tokens

5. **Kimi K2.5**
   - Best for: Multimodal tasks with agent swarm capabilities
   - Context: 256K tokens
   - Output: 8,192 tokens

6. **Titan Image Generator V2**
   - Best for: Image generation
   - Context: 4,096 tokens
   - Output: 1,024 tokens

7. **Titan Embed Text V2**
   - Best for: Embeddings and semantic search
   - Context: 8,192 tokens
   - Output: 1,024 tokens

8. **Cohere Rerank V3.5**
   - Best for: Reranking search results
   - Context: 4,096 tokens
   - Output: 1,024 tokens

### Connection Details

- **Config Location**: `~/.config/opencode/opencode.json`
- **LiteLLM Endpoint**: `http://litellm:4000` (internal container)
- **Host Endpoint**: `http://localhost:8001` (from host machine)
- **API Key**: Substituted directly into config during installation
- **Default Model**: Claude Sonnet 4.6
- **Server Port**: 3001
- **mDNS Domain**: `opencode.local`

## Prerequisites

### 1. LiteLLM Server Running

Ensure the LiteLLM server is running:

```bash
cd ai/server
./manage.sh up
./manage.sh status
```

### 2. AWS Credentials

Configure AWS credentials with Bedrock permissions:

```bash
# ~/.aws/credentials
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
region = ca-central-1
```

Or use a named profile:

```bash
export AWS_PROFILE=traillens-ai
```

## Usage

### VSCode Extension

1. Install the OpenCode extension in VSCode
2. The extension will automatically detect `~/.config/opencode/opencode.json`
3. Start coding with AI assistance

### Terminal UI (TUI)

```bash
# Start OpenCode TUI
opencode

# Or open specific file
opencode path/to/file.py

# Or specify custom config
OPENCODE_CONFIG=~/.config/opencode/opencode.json opencode
```

### Switching Models

Models can be switched through the OpenCode interface. The default model is Claude Sonnet 4.6, but you can select any of the 8 configured models.

## Configuration File Structure

The installed `~/.config/opencode/opencode.json` file contains:

```json
{
  "provider": {
    "litellm": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "LiteLLM (AWS Bedrock)",
      "options": {
        "baseURL": "http://litellm:4000",
        "apiKey": "sk-test-1234567890"
      },
      "models": {
        "model-name": {
          "name": "Display Name",
          "limit": {
            "context": 200000,
            "output": 8192
          }
        }
      }
    }
  },
  "model": "claude-sonnet-4-6",
  "server": {
    "port": 3001,
    "hostname": "0.0.0.0",
    "mdns": true,
    "mdnsDomain": "opencode.local"
  }
}
```

**Note**: The `apiKey` value is automatically substituted from `ai/server/.env` during installation.

**Security Note**: Ensure `~/.config/opencode/opencode.json` has appropriate permissions (600 recommended).

## Troubleshooting

### "Connection Refused" Error

**Solution**: Ensure LiteLLM server is running

```bash
cd ai/server
./manage.sh status
./manage.sh urls
```

### "Unauthorized" or "Invalid API Key" Error

**Solution**: Verify LITELLM_MASTER_KEY matches between OpenCode config and server:

```bash
# Check key in OpenCode config
grep "apiKey" ~/.config/opencode/opencode.json

# Check key in server config
grep "LITELLM_MASTER_KEY" ai/server/.env

# If they don't match, re-run the installer
./ai/scripts/install-opencode.sh
```

### Models Not Available

**Solution**: Ensure Bedrock models are enabled in AWS region

```bash
aws bedrock list-foundation-models --region ca-central-1 | grep claude
```

### mDNS Not Resolving

**Solution**: Check if Avahi/Bonjour service is running (macOS/Linux)

```bash
# macOS (built-in)
dns-sd -B _opencode._tcp

# Linux
avahi-browse -r _opencode._tcp
```

## Production Configuration

For production use, update `~/.config/opencode/opencode.json`:

```json
{
  "provider": {
    "litellm": {
      "options": {
        "baseURL": "https://ai.traillenshq.com",
        "apiKey": "your-production-api-key"
      }
    }
  }
}
```

**Security**: Store production API keys securely and never commit them to version control.

## Cost Optimization

- **Default Model**: Sonnet 4.6 provides best balance of cost/performance
- **Fast Queries**: Use Haiku 4.5 or Haiku 3.5 for quick questions
- **Complex Tasks**: Use Opus 4.6 sparingly for architectural decisions
- **Budget Mode**: Set Haiku 3.5 as default for maximum cost savings

## Additional Resources

- [OpenCode Documentation](https://opencode.dev/docs) (if available)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [TrailLens AI Setup Guide](../../README.md)

## Comparison with Continue.dev

| Feature | OpenCode | Continue.dev |
| ------- | -------- | ------------ |
| VSCode Extension | ✓ | ✓ |
| Terminal UI | ✓ | ✗ |
| Config Location | `~/.config/opencode/` | `~/.continue/` |
| API Key Storage | In config file | Environment variable |
| Model Switching | UI-based | Dropdown |
| Context Providers | Built-in | Configurable |
| mDNS Support | ✓ | ✗ |

Both tools can coexist and use the same LiteLLM backend!

## License

Copyright (c) 2025 TrailLensCo. All rights reserved.
