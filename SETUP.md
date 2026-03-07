# TrailLens AI Bedrock Setup Guide

Simplified AWS Bedrock infrastructure for single developer use with Continue.dev.

## What Was Deployed

This infrastructure creates:

1. **IAM User** - Dedicated user for Bedrock API access
2. **IAM Policies** - Permissions for all three Claude models
3. **Access Keys** - AWS credentials for authentication
4. **DNS CNAME** - Custom domain pointing to Bedrock endpoint

## Supported Models

| Model | Model ID | Use Case | Cost | Speed |
|-------|----------|----------|------|-------|
| **Claude Opus 4.6** | `anthropic.claude-opus-4-6` | Planning & Architecture | $$$ | Slow |
| **Claude Sonnet 4.5** | `anthropic.claude-sonnet-4-5-v2:0` | General Coding | $$ | Medium |
| **Claude Haiku 4.5** | `anthropic.claude-haiku-4-5-20251001:0` | Autocomplete | $ | Fast |

### Model Selection Guide

- **Planning/Architecture** → **Opus 4.6**
  - Complex design decisions
  - Multi-file refactoring plans
  - System architecture discussions
  - Most capable but slowest and most expensive

- **General Coding** → **Sonnet 4.5**
  - Writing functions and classes
  - Bug fixes and debugging
  - Code reviews
  - Best balance of quality, speed, and cost

- **Autocomplete/Completion** → **Haiku 4.5**
  - Inline code completion
  - Simple one-liners
  - Quick suggestions
  - Fastest and cheapest

## Step 1: Get Your AWS Credentials

After deploying with Pulumi, retrieve your credentials:

```bash
cd pulumi
pulumi stack output access_key_id
pulumi stack output secret_access_key --show-secrets
```

**Save these securely** - you cannot retrieve the secret key again.

## Step 2: Configure AWS Credentials

Create or edit `~/.aws/credentials`:

```ini
[traillens-ai]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
region = ca-central-1
```

Test the credentials:

```bash
export AWS_PROFILE=traillens-ai
aws bedrock list-foundation-models --region ca-central-1 | grep claude
```

## Step 3: Configure Continue.dev

### Option A: Using Custom Domain (Recommended)

Edit `~/.continue/config.json`:

```json
{
  "models": [
    {
      "title": "Claude Opus 4.6 (Planning)",
      "provider": "bedrock",
      "model": "anthropic.claude-opus-4-6",
      "region": "ca-central-1",
      "apiBase": "https://ai.traillenshq.com",
      "contextLength": 200000,
      "completionOptions": {
        "temperature": 0.0,
        "maxTokens": 8192
      }
    },
    {
      "title": "Claude Sonnet 4.5 (Coding)",
      "provider": "bedrock",
      "model": "anthropic.claude-sonnet-4-5-v2:0",
      "region": "ca-central-1",
      "apiBase": "https://ai.traillenshq.com",
      "contextLength": 200000,
      "completionOptions": {
        "temperature": 0.2,
        "maxTokens": 4096
      }
    },
    {
      "title": "Claude Haiku 4.5 (Fast)",
      "provider": "bedrock",
      "model": "anthropic.claude-haiku-4-5-20251001:0",
      "region": "ca-central-1",
      "apiBase": "https://ai.traillenshq.com",
      "contextLength": 200000,
      "completionOptions": {
        "temperature": 0.3,
        "maxTokens": 2048
      }
    }
  ],
  "tabAutocompleteModel": {
    "title": "Claude Haiku 4.5 (Autocomplete)",
    "provider": "bedrock",
    "model": "anthropic.claude-haiku-4-5-20251001:0",
    "region": "ca-central-1",
    "apiBase": "https://ai.traillenshq.com"
  }
}
```

**For Dev Environment:**
Replace `https://ai.traillenshq.com` with `https://ai.dev.traillenshq.com`

### Option B: Using Direct Bedrock Endpoint

If DNS is not yet propagated, use the direct endpoint:

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

Continue.dev will automatically use `bedrock-runtime.ca-central-1.amazonaws.com`.

## Step 4: Set Default Model in VSCode

In VSCode, open Continue.dev and select your default model:

1. **For Planning/Design**: Select "Claude Opus 4.6 (Planning)"
2. **For Regular Coding**: Select "Claude Sonnet 4.5 (Coding)"
3. **For Quick Tasks**: Select "Claude Haiku 4.5 (Fast)"

You can switch models at any time based on the task complexity.

## Step 5: Test the Setup

### Test with Continue.dev

1. Open any code file in VSCode
2. Highlight some code
3. Open Continue.dev (Cmd+L or Ctrl+L)
4. Type: "Explain this code"
5. Verify the model responds

### Test with AWS CLI

```bash
aws bedrock-runtime invoke-model \
  --region ca-central-1 \
  --model-id anthropic.claude-sonnet-4-5-v2:0 \
  --body '{"anthropic_version":"bedrock-2023-05-31","messages":[{"role":"user","content":"Say hello"}],"max_tokens":100}' \
  output.json

cat output.json
```

## DNS Configuration

### Production
- **Domain**: `ai.traillenshq.com`
- **CNAME**: → `bedrock-runtime.ca-central-1.amazonaws.com`
- **TTL**: 300 seconds

### Development
- **Domain**: `ai.dev.traillenshq.com`
- **CNAME**: → `bedrock-runtime.ca-central-1.amazonaws.com`
- **TTL**: 300 seconds

### Verify DNS Propagation

```bash
# Check CNAME record
dig ai.traillenshq.com CNAME

# Test HTTPS connection (will fail - Bedrock doesn't accept custom domains directly)
# This is expected - use Continue.dev which handles the host header correctly
curl -v https://ai.traillenshq.com
```

**Note**: The CNAME is for organizational purposes. Continue.dev will handle the proper host headers when making requests.

## Cost Optimization

### Model Cost Comparison (approximate)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Haiku 4.5 | $1 | $5 |
| Sonnet 4.5 | $3 | $15 |
| Opus 4.6 | $15 | $75 |

### Recommendations

1. **Use Haiku for autocomplete** - Saves 66-93% compared to Sonnet/Opus
2. **Use Sonnet for daily coding** - Good quality, reasonable cost
3. **Reserve Opus for complex tasks** - Only when you need maximum capability

### Monitor Your Costs

```bash
# View Bedrock usage
aws ce get-cost-and-usage \
  --time-period Start=2025-02-01,End=2025-02-28 \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --filter file://bedrock-filter.json

# bedrock-filter.json
{
  "Dimensions": {
    "Key": "SERVICE",
    "Values": ["Amazon Bedrock"]
  }
}
```

## Troubleshooting

### "Access Denied" Errors

**Solution**: Verify IAM policies are attached

```bash
aws iam list-user-policies --user-name traillens-ai-dev-bedrock-user
```

### "Model Not Found" Errors

**Solution**: Ensure you're using the correct region and model IDs

```bash
# List available models in your region
aws bedrock list-foundation-models --region ca-central-1 | grep claude
```

### Continue.dev Not Connecting

**Solution**: Check AWS credentials

```bash
# Verify credentials are set
aws sts get-caller-identity --profile traillens-ai

# Check ~/.aws/credentials file exists
cat ~/.aws/credentials
```

### DNS Not Resolving

**Solution**: Wait for propagation or use direct endpoint

```bash
# Check if CNAME exists
dig ai.traillenshq.com CNAME

# If not propagated, use direct endpoint in Continue.dev config
# Remove "apiBase" field and Continue.dev will use default Bedrock endpoint
```

## Security Best Practices

1. **Rotate Access Keys Regularly**
   ```bash
   # Create new key
   aws iam create-access-key --user-name traillens-ai-dev-bedrock-user

   # Delete old key (after updating credentials)
   aws iam delete-access-key --user-name traillens-ai-dev-bedrock-user --access-key-id OLD_KEY_ID
   ```

2. **Never Commit Credentials**
   - Add `~/.aws/credentials` to `.gitignore`
   - Use AWS Secrets Manager for shared credentials

3. **Monitor Usage**
   - Set up CloudWatch alarms for unusual activity
   - Review AWS billing dashboard monthly

## Advanced Configuration

### Environment Variables

Alternatively, set credentials via environment variables:

```bash
export AWS_PROFILE=traillens-ai
export AWS_REGION=ca-central-1
export AWS_ACCESS_KEY_ID=your_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_key
```

### Multiple Environments

Separate profiles for dev and prod:

```ini
# ~/.aws/credentials
[traillens-ai-dev]
aws_access_key_id = DEV_KEY
aws_secret_access_key = DEV_SECRET
region = ca-central-1

[traillens-ai-prod]
aws_access_key_id = PROD_KEY
aws_secret_access_key = PROD_SECRET
region = ca-central-1
```

Switch between them:

```bash
export AWS_PROFILE=traillens-ai-dev    # Development
export AWS_PROFILE=traillens-ai-prod   # Production
```

## Next Steps

1. **Deploy to production** - Repeat setup for prod stack
2. **Set up cost alerts** - CloudWatch alarms for budget
3. **Share with team** - Document credential distribution
4. **Monitor usage** - Track which models are most cost-effective

## Support

- AWS Bedrock Docs: https://docs.aws.amazon.com/bedrock/
- Continue.dev Docs: https://continue.dev/docs
- Claude API Docs: https://docs.anthropic.com/

## License

Copyright (c) 2025 TrailLensCo. All rights reserved.
