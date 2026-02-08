# Continue.dev Configuration for TrailLens AI

This directory contains the Continue.dev VSCode extension configuration for using AWS Bedrock with Claude models.

## Installation

### Quick Install (Recommended)

Run the install script:

```bash
./install.sh
```

### Manual Install

Copy the configuration to your Continue.dev directory:

```bash
# macOS/Linux
cp config.yaml ~/.continue/config.yaml

# Windows
copy config.yaml %USERPROFILE%\.continue\config.yaml
```

## Configuration Details

### Models Configured

1. **Claude Opus 4.6 (Planning)**
   - Best for: Complex architectural decisions, system design, multi-file refactoring
   - Temperature: 0.0 (most deterministic)
   - Max tokens: 8192

2. **Claude Sonnet 4.5 (Coding)**
   - Best for: General coding tasks, bug fixes, code reviews
   - Temperature: 0.2 (balanced)
   - Max tokens: 4096
   - **Recommended default for most tasks**

3. **Claude Haiku 4.5 (Fast)**
   - Best for: Quick questions, simple completions
   - Temperature: 0.3 (slightly creative)
   - Max tokens: 2048

### Tab Autocomplete

Configured to use **Claude Haiku 4.5** for inline code completion:
- Fast response times
- Low cost
- Max tokens: 500 (sufficient for completions)

### Embeddings

Uses **Amazon Titan Embed Text v2** for code context and similarity search.

## AWS Credentials

This configuration requires AWS credentials with Bedrock permissions. Ensure you have configured:

```bash
# ~/.aws/credentials
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
region = ca-central-1
```

Or use a named profile:

```bash
[traillens-ai]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
region = ca-central-1
```

Then set the environment variable:

```bash
export AWS_PROFILE=traillens-ai
```

## Switching Models

To switch models in VSCode:

1. Open Continue.dev sidebar (Cmd+L or Ctrl+L)
2. Click the model name at the top
3. Select from:
   - "Claude Opus 4.6 (Planning)" for complex tasks
   - "Claude Sonnet 4.5 (Coding)" for general coding
   - "Claude Haiku 4.5 (Fast)" for quick questions

## Cost Optimization

The configuration is optimized for cost:

- **Tab autocomplete** uses Haiku (cheapest) instead of Sonnet
- **Max tokens** limited to prevent runaway costs
- **Temperature** settings optimized for code generation

### Estimated Monthly Costs

Assuming 8 hours/day of active development:

| Activity | Model | Daily Tokens | Monthly Cost |
| -------- | ----- | ------------ | ------------ |
| Autocomplete | Haiku | 50k input, 10k output | $2.60 |
| Coding (20 queries) | Sonnet | 400k input, 100k output | $4.20 |
| Planning (5 queries) | Opus | 200k input, 50k output | $6.75 |
| **Total** | | | **~$13.55/month** |

## Customization

### Increase Token Limits

For longer responses, edit `maxTokens` in config.yaml:

```yaml
models:
  - title: Claude Sonnet 4.5 (Coding)
    completionOptions:
      maxTokens: 8192  # Increase as needed
```

### Adjust Temperature

For more creative responses:

```yaml
models:
  - title: Claude Sonnet 4.5 (Coding)
    completionOptions:
      temperature: 0.5  # 0.0 = deterministic, 1.0 = creative
```

### Use Custom Domain

To use the custom domain (`ai.traillenshq.com`) instead of direct Bedrock access, add `apiBase`:

```yaml
models:
  - title: Claude Sonnet 4.5 (Coding)
    provider: bedrock
    model: anthropic.claude-sonnet-4-5-v2:0
    region: ca-central-1
    apiBase: https://ai.traillenshq.com
```

**Note**: The CNAME is primarily for organizational purposes. Continue.dev works with both direct Bedrock endpoint and custom domain.

## Troubleshooting

### "Access Denied" Error

**Solution**: Verify AWS credentials are configured

```bash
aws sts get-caller-identity
```

### "Model Not Found" Error

**Solution**: Ensure Bedrock models are enabled in your AWS region

```bash
aws bedrock list-foundation-models --region ca-central-1 | grep claude
```

### Autocomplete Not Working

**Solution**: Check that `tabAutocompleteModel` is configured and using Haiku

### Slow Responses

**Solution**:
- Use Haiku for quick tasks
- Check AWS region latency
- Reduce `maxTokens` if responses are too long

## Additional Resources

- [Continue.dev Documentation](https://continue.dev/docs)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [TrailLens AI Setup Guide](../SETUP.md)

## License

Copyright (c) 2025 TrailLensCo. All rights reserved.
