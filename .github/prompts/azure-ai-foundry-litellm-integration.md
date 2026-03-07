# Azure AI Foundry Integration with LiteLLM - Analysis Report

**Date:** February 25, 2026
**Project:** TrailLens AI Infrastructure
**Purpose:** Review existing Pulumi infrastructure and determine Azure AI Foundry integration strategy with LiteLLM

## Executive Summary

This report analyzes the TrailLens AI project infrastructure and provides recommendations for integrating Azure AI Foundry endpoints with the existing LiteLLM proxy configuration. The review covers current AWS Bedrock implementation, Azure AI Foundry capabilities, free tier availability, and technical integration requirements.

**Key Findings:**
- Current infrastructure uses AWS Bedrock with IAM-based authentication for Claude models
- Azure AI Foundry offers Claude models but requires **paid Enterprise or MCA-E subscription** (no free tier for Claude)
- Azure provides $200 free credits for 30 days for new accounts (one-time offer)
- LiteLLM supports Azure AI Foundry with multiple authentication methods
- Integration can be achieved by adding Azure model configurations to existing LiteLLM setup

## Current Infrastructure Review

### 1. AWS Bedrock Implementation

**Pulumi Stack:** [ai/pulumi/\_\_main\_\_.py](../pulumi/__main__.py)

The current infrastructure deploys a simplified Bedrock setup consisting of:

#### Components Deployed

**IAM Resources** ([components/bedrock.py](../pulumi/components/bedrock.py)):
- IAM user: `traillens-ai-bedrock-user`
- Access keys for programmatic access
- Multi-region IAM policies supporting:
  - Claude models (Opus 4.6, Sonnet 4.6, Haiku 4.5) in `ca-central-1`
  - Inference profiles for cross-region routing
  - Titan Embed Text V2 (ca-central-1)
  - Cohere Rerank V3.5 (ca-central-1)
  - Moonshot Kimi K2.5 (us-east-1)
  - Titan Image Generator V2 (us-east-1)

**Budget Monitoring** ([components/budget.py](../pulumi/components/budget.py)):
- AWS Budget: $75/month for Amazon Bedrock
- SNS topic for budget alerts
- Email notifications at 80%, 100% actual spend, and 100% forecasted spend

**Supported Models:**

| Model | Model ID | Use Case | Region |
|-------|----------|----------|--------|
| Claude Opus 4.6 | `anthropic.claude-opus-4-6-v1` | Planning/Architecture | ca-central-1 |
| Claude Sonnet 4.6 | `anthropic.claude-sonnet-4-6` | General Coding | ca-central-1 |
| Claude Haiku 4.5 | `anthropic.claude-haiku-4-5-20251001-v1:0` | Completion/Autocomplete | ca-central-1 |
| Claude Haiku 3.5 | `anthropic.claude-3-5-haiku-20241022-v1:0` | Code Apply (cheapest) | ca-central-1 |
| Titan Embed V2 | `amazon.titan-embed-text-v2:0` | Embeddings | ca-central-1 |
| Cohere Rerank V3.5 | `cohere.rerank-v3-5:0` | Reranking | ca-central-1 |
| Kimi K2.5 | `moonshotai.kimi-k2.5` | Multimodal with Agent Swarm | us-east-1 |
| Titan Image V2 | `amazon.titan-image-generator-v2:0` | Image Generation | us-east-1 |

#### Configuration Management

**Config Loader** ([utils/config.py](../pulumi/utils/config.py)):
- Validates required configuration: `project_name`, `region`, `domain`, `zone_name`, `budget_alert_email`
- Enforces `ca-central-1` region requirement
- Loads tags from Pulumi config

**Stack Configuration:**
- Production stack: `Pulumi.prod.yaml`
- Development stack: Not currently configured (would be `Pulumi.dev.yaml`)

### 2. LiteLLM Proxy Configuration

**Configuration File:** [server/config/litellm-config.yaml](../server/config/litellm-config.yaml)

The LiteLLM proxy is configured for local testing with the following setup:

#### Model List

```yaml
model_list:
  # Text models (ca-central-1 in production)
  - model_name: claude-opus-4-6
    litellm_params:
      model: bedrock/us.anthropic.claude-opus-4-6-v1
      aws_region_name: ca-central-1

  - model_name: claude-sonnet-4-6
    litellm_params:
      model: bedrock/us.anthropic.claude-sonnet-4-6
      aws_region_name: ca-central-1

  - model_name: claude-haiku-4-5
    litellm_params:
      model: bedrock/us.anthropic.claude-haiku-4-5-20251001-v1:0
      aws_region_name: ca-central-1

  - model_name: claude-haiku-3-5
    litellm_params:
      model: bedrock/anthropic.claude-3-5-haiku-20241022-v1:0
      aws_region_name: ca-central-1

  # Image generation (us-east-1)
  - model_name: titan-image-v2
    litellm_params:
      model: bedrock/amazon.titan-image-generator-v2:0
      aws_region_name: us-east-1

  # Embedding model (ca-central-1)
  - model_name: titan-embed-v2
    litellm_params:
      model: bedrock/amazon.titan-embed-text-v2:0
      aws_region_name: ca-central-1

  # Rerank model (ca-central-1)
  - model_name: cohere-rerank-v3-5
    litellm_params:
      model: bedrock/arn:aws:bedrock:ca-central-1::foundation-model/cohere.rerank-v3-5:0
      aws_region_name: ca-central-1
    model_info:
      mode: rerank
      skip_health_check: true

  # Kimi K2.5 (us-east-1 only)
  - model_name: kimi-k2-5
    litellm_params:
      model: bedrock/moonshotai.kimi-k2.5
      aws_region_name: us-east-1
```

#### Features Enabled

**General Settings:**
- Master key for API authentication: `sk-test-1234567890`
- Verbose logging enabled for testing
- CORS origin: `*` (for local development)
- Model persistence in database

**LiteLLM Settings:**
- Telemetry disabled
- Drop unsupported parameters
- Success callback to Langfuse
- Request timeout: 600 seconds
- Redis caching enabled:
  - Host: `redis`
  - Port: `6379`
  - Cached call types: `acompletion`, `atext_completion`, `aembedding`, `atranscription`

### 3. Local Testing Environment

**Docker Compose Setup:** [server/podman-compose.yaml](../server/podman-compose.yaml)

Services orchestrated:
- **LiteLLM Proxy** (port 8000) - OpenAI-compatible API for Bedrock
- **PostgreSQL** (port 5432, internal) - LiteLLM persistence and cost tracking
- **Redis** (port 6379, internal) - Response caching
- **OpenCode Server** (port 4096) - AI code assistant
- **OpenCode Web UI** (port 3001) - Browser interface
- **Nginx** (port 8080) - Reverse proxy

**Management Script:** [server/manage.sh](../server/manage.sh)
- Build, start, stop, restart services
- View logs and status
- Test connectivity
- Clean up resources

## Azure AI Foundry Capabilities

### 1. Claude Models Availability

**Source:** [Microsoft Foundry Claude Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/use-foundry-models-claude?view=foundry-classic)

Azure AI Foundry provides access to Anthropic's Claude models:

#### Available Models

| Model | Capabilities | Best For |
|-------|-------------|----------|
| **Claude Opus 4.6** | Most intelligent, world's best for coding | Enterprise agents, professional work, complex coding |
| **Claude Sonnet 4.5** | Highly capable for real-world agents | Long-horizon tasks, high-volume use cases |
| **Claude Haiku 4.5** | Near-frontier performance | Coding, agents, wide range of use cases |

**Important Limitations:**
- Requires **paid Azure subscription** (Enterprise or MCA-E subscriptions only)
- Billing account must be in a country/region where Anthropic offers models
- **No free tier for Claude models** - paid subscription required

### 2. Free Trial and Credits

**Sources:**
- [Azure AI Foundry Pricing](https://azure.microsoft.com/en-us/pricing/details/ai-foundry/)
- [Azure Free Account](https://azure.microsoft.com/en-us/pricing/purchase-options/azure-account)

#### Free Tier Details

**Platform Access:**
- Azure AI Foundry platform is **free to use and explore**
- Individual features billed at normal rates

**Free Credits for New Customers:**
- **$200 USD credit** valid for **30 days**
- One account per new customer
- Requires credit/debit card (non-prepaid)
- Move to pay-as-you-go within 30 days or after credit exhausted

**Important Notes:**
- Free credits apply to Azure services broadly, not Claude models specifically
- Some services always free, some free for 12 months
- Unused credits cannot be carried over or transferred

**Current Account Status:**
```json
{
  "name": "Azure subscription 1",
  "state": "Enabled",
  "user": "mark@buckaway.ca",
  "tenantId": "f9950eac-62f4-4c79-9597-7536f4f2deb4",
  "subscriptionId": "6f3b8a6c-56a3-4ab7-938b-deab5013d7a8"
}
```

### 3. Endpoint Configuration

**Source:** [Microsoft Foundry Endpoints](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/concepts/endpoints?view=foundry-classic)

Azure AI Foundry provides endpoints in two formats:

#### Foundry Tools Endpoint
```
https://<your-resource-name>.cognitiveservices.azure.com/
```

#### Azure AI Inference Endpoint
```
https://<resource-name>.services.ai.azure.com/models
```

For Claude models specifically:
```
https://<resource-name>.services.ai.azure.com/anthropic
```

**Authentication:**
- API Key authentication (`AZURE_AI_API_KEY`)
- Azure AD authentication (tenant ID, client ID, client secret)

## LiteLLM Azure Integration

**Sources:**
- [LiteLLM Azure OpenAI Documentation](https://docs.litellm.ai/docs/providers/azure/)
- [LiteLLM Azure AI Studio](https://docs.litellm.ai/docs/providers/azure_ai)
- [LiteLLM Azure Anthropic](https://docs.litellm.ai/docs/providers/azure/azure_anthropic)

### 1. Azure OpenAI Configuration

LiteLLM supports Azure OpenAI with the following configuration pattern:

#### Basic Configuration

```yaml
model_list:
  - model_name: azure-gpt-4o
    litellm_params:
      model: azure/gpt-4o
      api_base: https://eastus.api.cognitive.microsoft.com
      api_key: os.environ/AZURE_OPENAI_KEY
      api_version: "2024-10-21"
```

#### Environment Variable Usage

```yaml
model_list:
  - model_name: azure-model-name
    litellm_params:
      model: azure/deployment-name
      api_base: os.environ/AZURE_API_BASE
      api_key: os.environ/AZURE_API_KEY
      api_version: os.environ/AZURE_API_VERSION
```

### 2. Azure Claude Configuration

**Source:** [LiteLLM Azure Anthropic](https://docs.litellm.ai/docs/providers/azure/azure_anthropic)

For Claude models via Azure Foundry, use the following pattern:

```yaml
model_list:
  - model_name: azure-claude-sonnet-4-5
    litellm_params:
      model: azure/claude-sonnet-4-5
      api_base: https://<resource-name>.services.ai.azure.com/anthropic
      api_key: os.environ/AZURE_AI_API_KEY
```

### 3. Authentication Methods

#### API Key Authentication

```bash
export AZURE_AI_API_KEY="your-api-key"
```

#### Azure AD Authentication

```bash
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
```

**Note:** Azure AI Foundry Agents require Azure AD authentication (not API keys).

## Proposed Azure Integration Strategy

### 1. Azure Resource Setup (Prerequisites)

Before configuring LiteLLM, the following Azure resources must be created:

#### Required Azure Resources

1. **Azure AI Hub** - Central workspace for AI resources
2. **Azure AI Project** - Project-specific configuration
3. **Model Deployments** - Deploy Claude models to endpoints
4. **Service Principal** (optional) - For service account authentication

#### Estimated Setup Steps

```bash
# Login to Azure (already completed)
az login

# Create resource group
az group create \
  --name traillens-ai-rg \
  --location canadacentral

# Create AI Hub (requires Azure AI Foundry portal)
# This step must be done via portal: https://ai.azure.com/

# Deploy Claude models (via portal)
# Navigate to Model Catalog → Deploy Claude Opus/Sonnet/Haiku
```

**Important:** Model deployment via Azure AI Foundry is primarily portal-based. CLI support is limited for Foundry Models.

### 2. Retrieve Azure Credentials

Once resources are deployed, retrieve endpoint and credentials:

#### Get Resource Information

```bash
# List AI resources
az resource list \
  --resource-type "Microsoft.MachineLearningServices/workspaces" \
  --query "[].{name:name, location:location, id:id}" \
  --output table

# Get workspace details
az ml workspace show \
  --name <workspace-name> \
  --resource-group traillens-ai-rg

# Get endpoint URL (from deployment)
# This will be available in the Azure AI Foundry portal after deployment
```

#### Create Service Principal (Optional)

```bash
# Create service principal for authentication
az ad sp create-for-rbac \
  --name traillens-ai-sp \
  --role "Cognitive Services User" \
  --scopes /subscriptions/6f3b8a6c-56a3-4ab7-938b-deab5013d7a8

# Output will include:
# - appId (client ID)
# - password (client secret)
# - tenant
```

### 3. LiteLLM Configuration Changes

**File to Modify:** [server/config/litellm-config.yaml](../server/config/litellm-config.yaml)

#### Add Azure Claude Models

Add the following to the `model_list` section:

```yaml
  # Azure AI Foundry - Claude Models
  # NOTE: Replace <resource-name> with actual Azure AI resource name
  # NOTE: Replace api_key with environment variable reference

  - model_name: azure-claude-opus-4-6
    litellm_params:
      model: azure/claude-opus-4-6
      api_base: https://<resource-name>.services.ai.azure.com/anthropic
      api_key: os.environ/AZURE_AI_API_KEY
      api_version: "2024-10-21"  # Use latest supported version
    model_info:
      mode: chat
      supports_function_calling: true

  - model_name: azure-claude-sonnet-4-5
    litellm_params:
      model: azure/claude-sonnet-4-5
      api_base: https://<resource-name>.services.ai.azure.com/anthropic
      api_key: os.environ/AZURE_AI_API_KEY
      api_version: "2024-10-21"
    model_info:
      mode: chat
      supports_function_calling: true

  - model_name: azure-claude-haiku-4-5
    litellm_params:
      model: azure/claude-haiku-4-5
      api_base: https://<resource-name>.services.ai.azure.com/anthropic
      api_key: os.environ/AZURE_AI_API_KEY
      api_version: "2024-10-21"
    model_info:
      mode: chat
      supports_function_calling: true
```

#### Environment Variables

**File to Modify:** [server/.env](../server/.env)

Add Azure credentials:

```bash
# Azure AI Foundry Configuration
AZURE_AI_API_KEY=your-azure-ai-api-key
AZURE_API_BASE=https://<resource-name>.services.ai.azure.com/anthropic
AZURE_API_VERSION=2024-10-21

# Optional: Azure AD Authentication
AZURE_TENANT_ID=f9950eac-62f4-4c79-9597-7536f4f2deb4
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

### 4. Testing Azure Integration

#### Test with LiteLLM Proxy

```bash
# Start services
cd server
./manage.sh start

# Test Azure Claude via LiteLLM API
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-test-1234567890" \
  -d '{
    "model": "azure-claude-sonnet-4-5",
    "messages": [
      {"role": "user", "content": "Say hello from Azure!"}
    ],
    "max_tokens": 100
  }'
```

#### Test Script

Create [server/test-azure-models.sh](../server/test-azure-models.sh):

```bash
#!/bin/bash
# Test Azure AI Foundry models via LiteLLM

LITELLM_URL="http://localhost:8000"
API_KEY="sk-test-1234567890"

echo "Testing Azure Claude Models..."

for model in "azure-claude-opus-4-6" "azure-claude-sonnet-4-5" "azure-claude-haiku-4-5"; do
    echo ""
    echo "Testing $model..."

    curl -s -X POST "$LITELLM_URL/v1/chat/completions" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $API_KEY" \
      -d "{
        \"model\": \"$model\",
        \"messages\": [{\"role\": \"user\", \"content\": \"Say: Testing $model\"}],
        \"max_tokens\": 50
      }" | jq -r '.choices[0].message.content'
done

echo ""
echo "✓ Azure model testing complete"
```

### 5. Cost Comparison

#### AWS Bedrock Pricing (Current)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Claude Haiku 4.5 | $1 | $5 |
| Claude Sonnet 4.5 | $3 | $15 |
| Claude Opus 4.6 | $15 | $75 |

**Current Budget:** $75/month for Amazon Bedrock

#### Azure AI Foundry Pricing

**Source:** [Azure AI Foundry Models Pricing](https://azure.microsoft.com/en-us/pricing/details/ai-foundry-models/aoai/)

Pricing is typically comparable to AWS Bedrock, but exact rates depend on:
- Azure region selected
- Commitment tier (pay-as-you-go vs. reserved capacity)
- Enterprise agreement terms

**Free Trial:**
- $200 credit for 30 days (one-time)
- After credits exhausted or 30 days: pay-as-you-go pricing

#### Hybrid Strategy Cost Optimization

**Recommendation:** Use both providers for redundancy and cost optimization

1. **Primary:** AWS Bedrock (already deployed, budgeted)
2. **Secondary:** Azure AI Foundry (free $200 credit for testing)
3. **Fallback:** Switch to Azure if AWS Bedrock has regional outages
4. **Testing:** Use Azure credits to test new Claude model versions

**LiteLLM Routing:** Configure model fallbacks

```yaml
model_list:
  - model_name: claude-sonnet-4-5
    litellm_params:
      model: bedrock/anthropic.claude-sonnet-4-6
      aws_region_name: ca-central-1
    model_info:
      fallback_models: ["azure-claude-sonnet-4-5"]

  - model_name: azure-claude-sonnet-4-5
    litellm_params:
      model: azure/claude-sonnet-4-5
      api_base: https://<resource>.services.ai.azure.com/anthropic
      api_key: os.environ/AZURE_AI_API_KEY
```

## Pulumi Azure Infrastructure Deployment

This section provides comprehensive guidance on deploying Azure AI Services infrastructure using Pulumi to complement the existing AWS Bedrock setup.

### 🚨 CRITICAL FINDING: Claude Models NOT Available in Canadian Regions

**Sources:**
- [Deploy and use Claude models in Microsoft Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/use-foundry-models-claude?view=foundry-classic)
- [Feature availability across cloud regions](https://learn.microsoft.com/en-us/azure/ai-foundry/reference/region-support?view=foundry-classic)
- [Region availability for models in serverless APIs](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/deploy-models-serverless-availability?view=foundry-classic)

**CURRENT REGIONAL AVAILABILITY (February 2026):**

Claude models in Azure AI Foundry are **ONLY** available in:
- **East US 2** (Virginia, United States)
- **Sweden Central** (Stockholm, Sweden)

**NOT AVAILABLE IN:**
- ❌ Canada Central (Montreal, Quebec)
- ❌ Canada East (Toronto, Ontario)

### 🇨🇦 Canadian Data Sovereignty Conflict

**The Problem:**

There is a **fundamental conflict** between the requirement for Canadian data residency and Claude model availability:

1. **TrailLens Requirement:** All resources must be in Canadian regions for data sovereignty
2. **Azure Reality:** Claude models are only available in East US 2 and Sweden Central
3. **Conflict:** Cannot have both Claude models AND Canadian data residency with Azure

**Why This Matters:**

- **Data Sovereignty:** Data processed by Claude in East US 2 leaves Canada
- **Compliance Risk:** May violate Canadian data residency requirements
- **Latency:** Higher latency from Canada to US East vs. Canada Central
- **AWS Advantage:** AWS Bedrock supports Claude in `ca-central-1` (Canadian region)

### 📅 Future Availability - Microsoft Canada Investment

**Sources:**
- [Microsoft Deepens Commitment to Canada with $19B AI Investment](https://blogs.microsoft.com/on-the-issues/2025/12/09/microsoft-deepens-its-commitment-to-canada-with-landmark-19b-ai-investment/)
- [Microsoft to Spend $7.5B on Canadian AI Expansion](https://www.uctoday.com/unified-communications/microsoft-to-spend-7-5b-on-canadian-ai-expansion-bringing-total-investment-to-19b/)

**Canadian AI Expansion Timeline:**

Microsoft announced a **$19 billion investment** in Canada's AI infrastructure:

- **New datacenter capacity** in Canada Central and Canada East
- **Coming online:** Second half of 2026
- **Sovereign AI Landing Zone (SAIL)** in Canada
- **In-country data processing** for AI workloads
- **Cohere integration** (Command A, Embed 4 models)

**What This Means:**

- Claude models **may** become available in Canadian regions by Q4 2026
- Current limitation is **temporary** but affects immediate deployment
- No official confirmation yet on Claude specifically

### 🎯 Updated Recommendation: Region Strategy

Given the current regional limitations, here are the options:

#### Option 1: AWS Bedrock Only

**Advantages:**
- ✅ Claude models available in `ca-central-1` (Canadian region)
- ✅ Full data sovereignty compliance
- ✅ Already deployed and working
- ✅ Lowest latency from Canada
- ✅ Within budget ($75/month)

**Disadvantages:**
- ❌ No multi-cloud redundancy
- ❌ Single provider dependency

**Verdict:** **Maintain as primary provider**

#### Option 2: Hybrid AWS + Azure East US 2 (SELECTED APPROACH)

**Advantages:**
- ✅ Claude models available immediately for testing
- ✅ Multi-cloud redundancy
- ✅ Can use $200 free credits
- ✅ Faster time to market for Azure integration testing
- ✅ Positions team for future Canadian region migration

**Disadvantages:**
- ⚠️ **Data processed in East US 2 leaves Canada**
- ⚠️ Higher latency vs. Canadian region (~20-40ms additional)
- ⚠️ May require data sovereignty waiver documentation
- ⚠️ Temporary solution until Canadian regions available

**Data Sovereignty Mitigation:**
- Use for non-production/testing workloads initially
- Document data flow and regional processing
- Prepare migration plan to Canadian regions (Q4 2026)
- Maintain AWS Bedrock (ca-central-1) as primary for production

**Verdict:** **SELECTED - Proceed with East US 2 deployment while planning Canadian region migration**

#### Option 3: Wait for Canadian Region Support

**Strategy:**
- Keep AWS Bedrock as primary provider (ca-central-1)
- Monitor Azure for Canadian region rollout (H2 2026)
- Revisit Azure integration when Claude available in Canada Central/East
- Use free trial credits to test in East US 2 (non-production only)

**Timeline:**
- **Now - Q3 2026:** AWS Bedrock only
- **Q4 2026:** Re-evaluate Azure when Canadian regions available
- **2027:** Potential multi-cloud deployment with both providers in Canada

**Verdict:** **DEFERRED - Will migrate to Canadian regions when available**

### 📍 Region Configuration Update

**DEPLOYMENT STRATEGY:**

Based on the selected Option 2 approach:

1. **Deploy to East US 2** for immediate Azure integration
2. **Maintain AWS Bedrock (ca-central-1)** as primary production provider
3. **Document data sovereignty implications** for compliance review
4. **Plan migration to canadacentral** when Claude models become available (Q4 2026)

**Pulumi Configuration Approach:**

1. **Allow East US 2** as valid Azure region for current deployment
2. **Warn about data sovereignty** implications during deployment
3. **Log reminder** to migrate to Canadian region when available
4. **Track migration deadline** (Q4 2026 target)

### 1. Azure Provider Setup

#### Install Azure Provider

```bash
cd pulumi
source ../scripts/setup-env.sh
pip install pulumi-azure-native pulumi-azuread
```

#### Update Requirements

**File:** [ai/pulumi/requirements.txt](../pulumi/requirements.txt)

Add:
```
pulumi>=3.0.0,<4.0.0
pulumi-aws>=6.0.0,<7.0.0
pulumi-azure-native>=2.0.0,<3.0.0
pulumi-azuread>=6.0.0,<7.0.0
```

### 2. Create Azure Components Module

**Source:** [Pulumi Azure Native Cognitive Services](https://www.pulumi.com/registry/packages/azure-native/api-docs/cognitiveservices/)

Create new file: [ai/pulumi/components/azure_ai.py](../pulumi/components/azure_ai.py)

```python
# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

"""
Azure AI Services component for TrailLens AI infrastructure.

This component deploys:
- Resource Group for Azure AI resources
- Cognitive Services Account (AI Services multi-service)
- Service Principal for API authentication
- Model deployments for Claude models (when available via API)
- Budget alerts for cost monitoring

Note: Claude model deployments currently require Azure AI Foundry portal.
      This component creates the foundation infrastructure.
"""

import json

import pulumi
import pulumi_azure_native as azure
import pulumi_azuread as azuread


def create_azure_ai_stack(project_name: str, region: str, tags: dict):
    """
    Create Azure AI Services stack for Claude model access.

    Args:
        project_name: The project name.
        region: Azure region (canadacentral recommended).
        tags: Resource tags.

    Returns:
        dict: Dictionary containing Azure resources and credentials.
    """
    stack_name = f"{project_name}-ai-azure"

    pulumi.log.info(f"Creating Azure AI stack: {stack_name}")

    # ==========================================================================
    # Resource Group
    # ==========================================================================

    resource_group = azure.resources.ResourceGroup(
        f"{stack_name}-rg",
        resource_group_name=f"{stack_name}-rg",
        location=region,
        tags={**tags, "Name": f"{stack_name}-rg"},
    )

    pulumi.log.info(f"✓ Resource Group created: {resource_group.name}")

    # ==========================================================================
    # Cognitive Services Account (AI Services)
    # ==========================================================================

    # AI Services is a multi-service account that provides access to:
    # - Azure OpenAI Service
    # - Azure AI Foundry Models (Claude, etc.)
    # - Text Analytics, Translation, etc.
    cognitive_account = azure.cognitiveservices.Account(
        f"{stack_name}-cognitive",
        account_name=f"{project_name}-ai-cognitive",
        resource_group_name=resource_group.name,
        location=resource_group.location,
        kind="AIServices",  # Multi-service account type
        sku=azure.cognitiveservices.SkuArgs(
            name="S0",  # Standard tier (required for Claude models)
        ),
        properties=azure.cognitiveservices.AccountPropertiesArgs(
            custom_sub_domain_name=f"{project_name}-ai",
            public_network_access="Enabled",  # Required for API access
            # Network ACLs can be configured here for production
            network_acls=azure.cognitiveservices.NetworkRuleSetArgs(
                default_action="Allow",  # Change to "Deny" for production
            ),
        ),
        tags={**tags, "Name": f"{stack_name}-cognitive"},
    )

    pulumi.log.info(f"✓ Cognitive Services Account created: {cognitive_account.name}")

    # ==========================================================================
    # Service Principal for API Authentication (Optional)
    # ==========================================================================

    # Create a service principal for programmatic access
    # This is similar to AWS IAM user
    app = azuread.Application(
        f"{stack_name}-app",
        display_name=f"{stack_name}-app",
    )

    service_principal = azuread.ServicePrincipal(
        f"{stack_name}-sp",
        client_id=app.client_id,
    )

    # Create a client secret (similar to AWS access key)
    client_secret = azuread.ApplicationPassword(
        f"{stack_name}-secret",
        application_id=app.id,
        display_name="AI Services Access",
    )

    # Assign "Cognitive Services User" role to service principal
    role_assignment = azure.authorization.RoleAssignment(
        f"{stack_name}-role",
        principal_id=service_principal.object_id,
        principal_type="ServicePrincipal",
        role_definition_id=f"/subscriptions/{azure.authorization.get_client_config().subscription_id}/providers/Microsoft.Authorization/roleDefinitions/a97b65f3-24c7-4388-baec-2e87135dc908",  # Cognitive Services User role
        scope=cognitive_account.id,
    )

    pulumi.log.info("✓ Service Principal and role assignment created")

    # ==========================================================================
    # Budget for Azure AI Services
    # ==========================================================================

    # Note: Azure Consumption Budget requires subscription-level permissions
    # This may need to be created manually via portal
    # Keeping this section as reference

    pulumi.log.info("⚠ Budget must be created manually via Azure Portal")
    pulumi.log.info("  Navigate to: Cost Management + Billing → Budgets")
    pulumi.log.info("  Set budget for Cognitive Services at $75/month")

    # ==========================================================================
    # Outputs
    # ==========================================================================

    return {
        "resource_group": resource_group,
        "resource_group_name": resource_group.name,
        "cognitive_account": cognitive_account,
        "cognitive_account_name": cognitive_account.name,
        "cognitive_account_endpoint": cognitive_account.properties.endpoint,
        "cognitive_account_key": cognitive_account.list_keys().apply(
            lambda keys: keys.key1
        ),
        "service_principal_id": service_principal.object_id,
        "service_principal_client_id": app.client_id,
        "service_principal_secret": client_secret.value,
        "azure_region": region,
        "foundry_endpoint": cognitive_account.properties.endpoint.apply(
            lambda endpoint: f"{endpoint}anthropic"
        ),
    }


def create_azure_budget(
    project_name: str,
    resource_group_name: pulumi.Output[str],
    email: str,
    tags: dict,
):
    """
    Create Azure Budget for cost monitoring.

    Note: This requires Consumption API which may have permission restrictions.
    Consider creating budgets manually via Azure Portal for initial setup.

    Args:
        project_name: The project name.
        resource_group_name: Resource group name.
        email: Email address for budget alerts.
        tags: Resource tags.

    Returns:
        dict: Dictionary containing budget resources (or None if not supported).
    """
    pulumi.log.warn(
        "Azure Budget API has limitations. "
        "Manual budget creation via portal recommended."
    )

    # Budget creation via Pulumi is complex and requires specific permissions
    # Recommend manual setup via Azure Portal:
    # 1. Navigate to Cost Management + Billing
    # 2. Create Budget
    # 3. Set amount: $75/month
    # 4. Set alerts: 80%, 100% actual spend

    return {
        "budget_id": None,
        "budget_setup_required": True,
        "budget_setup_instructions": "Create budget manually via Azure Portal → Cost Management + Billing → Budgets",
    }
```

### 3. Update Main Pulumi Program

**File:** [ai/pulumi/\_\_main\_\_.py](../pulumi/__main__.py)

Update to support Azure deployment:

```python
# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

"""
TrailLens AI Infrastructure with Pulumi

Multi-cloud infrastructure supporting both AWS Bedrock and Azure AI Services.

Supported Models (AWS Bedrock):
    - Claude Opus 4.6 (Planning/Architecture)
    - Claude Sonnet 4.5 (Coding)
    - Claude Haiku 4.5 (Completion/Autocomplete)
    - Claude Haiku 3.5 (Code Apply/Edits - Cheapest)

Supported Models (Azure AI Foundry):
    - Claude Opus 4.6 (Planning/Architecture)
    - Claude Sonnet 4.5 (Coding)
    - Claude Haiku 4.5 (Completion/Autocomplete)
"""

import pulumi

from components.azure_ai import create_azure_ai_stack, create_azure_budget
from components.bedrock import create_bedrock_iam_stack
from components.budget import create_budget_stack
from utils.config import load_config, validate_config


def main():
    """
    Main deployment function for multi-cloud AI infrastructure.
    """
    # Load configuration from Pulumi config
    config = load_config()

    # Validate configuration
    try:
        validate_config(config)
    except Exception as e:
        pulumi.log.error(f"Configuration validation failed: {e}")
        raise

    # Print configuration summary
    pulumi.log.info("=" * 70)
    pulumi.log.info(
        f"TrailLens AI Infrastructure Deployment - Stack: {pulumi.get_stack()}"
    )
    pulumi.log.info(f"AWS Region: {config['region']}")
    pulumi.log.info(f"Azure Region: {config.get('azure_region', 'not configured')}")
    pulumi.log.info(f"Domain: {config['domain']}")
    pulumi.log.info(f"Zone: {config['zone_name']}")
    pulumi.log.info("=" * 70)

    # ==========================================================================
    # AWS Bedrock IAM Setup
    # ==========================================================================

    pulumi.log.info("Creating AWS Bedrock IAM resources...")

    bedrock = create_bedrock_iam_stack(
        project_name=config["project_name"],
        region=config["region"],
        tags=config.get("tags", {}),
    )

    # ==========================================================================
    # AWS Budget Setup
    # ==========================================================================

    pulumi.log.info("Creating AWS Budget for cost monitoring...")

    aws_budget = create_budget_stack(
        project_name=config["project_name"],
        email=config["budget_alert_email"],
        tags=config.get("tags", {}),
    )

    # ==========================================================================
    # Azure AI Services Setup (Optional)
    # ==========================================================================

    azure_stack = None
    azure_budget = None

    if config.get("azure_enabled", False):
        pulumi.log.info("Creating Azure AI Services resources...")

        azure_stack = create_azure_ai_stack(
            project_name=config["project_name"],
            region=config.get("azure_region", "canadacentral"),
            tags=config.get("tags", {}),
        )

        pulumi.log.info("Setting up Azure budget monitoring...")

        azure_budget = create_azure_budget(
            project_name=config["project_name"],
            resource_group_name=azure_stack["resource_group_name"],
            email=config["budget_alert_email"],
            tags=config.get("tags", {}),
        )

        pulumi.log.info("✓ Azure AI infrastructure deployment complete!")
    else:
        pulumi.log.info("⊘ Azure deployment disabled in config")

    # ==========================================================================
    # Exports
    # ==========================================================================

    # AWS Bedrock Exports
    pulumi.export("aws_iam_user_name", bedrock["iam_user_name"])
    pulumi.export("aws_iam_user_arn", bedrock["iam_user_arn"])
    pulumi.export("aws_access_key_id", bedrock["access_key_id"])
    pulumi.export("aws_secret_access_key", bedrock["secret_access_key"])
    pulumi.export("aws_region", config["region"])
    pulumi.export("aws_budget_topic_arn", aws_budget["budget_topic_arn"])
    pulumi.export("aws_budget_id", aws_budget["budget_id"])

    # Azure Exports (if enabled)
    if azure_stack:
        pulumi.export("azure_resource_group", azure_stack["resource_group_name"])
        pulumi.export(
            "azure_cognitive_account_name", azure_stack["cognitive_account_name"]
        )
        pulumi.export("azure_endpoint", azure_stack["cognitive_account_endpoint"])
        pulumi.export("azure_foundry_endpoint", azure_stack["foundry_endpoint"])
        pulumi.export("azure_api_key", azure_stack["cognitive_account_key"])
        pulumi.export(
            "azure_service_principal_id", azure_stack["service_principal_client_id"]
        )
        pulumi.export(
            "azure_service_principal_secret", azure_stack["service_principal_secret"]
        )
        pulumi.export("azure_region", azure_stack["azure_region"])

        if azure_budget and azure_budget.get("budget_setup_required"):
            pulumi.export(
                "azure_budget_setup", azure_budget["budget_setup_instructions"]
            )

    # Model Export
    pulumi.export(
        "models",
        {
            "aws": {
                "opus": "anthropic.claude-opus-4-6-v1",
                "sonnet": "anthropic.claude-sonnet-4-6",
                "haiku": "anthropic.claude-haiku-4-5-20251001-v1:0",
                "haiku_3_5": "anthropic.claude-3-5-haiku-20241022-v1:0",
                "titan_embed": "amazon.titan-embed-text-v2:0",
                "titan_image": "amazon.titan-image-generator-v2:0",
                "cohere_rerank": "cohere.rerank-v3-5:0",
                "kimi_k2_5": "moonshotai.kimi-k2.5",
            },
            "azure": {
                "opus": "claude-opus-4-6",
                "sonnet": "claude-sonnet-4-5",
                "haiku": "claude-haiku-4-5",
            }
            if azure_stack
            else {},
        },
    )

    pulumi.log.info("✓ TrailLens AI infrastructure deployment complete!")
    pulumi.log.info("")
    pulumi.log.info("Next steps:")
    pulumi.log.info("  1. Save access credentials from outputs")
    pulumi.log.info("  2. Configure AWS credentials: ~/.aws/credentials")

    if azure_stack:
        pulumi.log.info("  3. Configure Azure credentials for LiteLLM")
        pulumi.log.info("  4. Deploy Claude models via Azure AI Foundry portal")
        pulumi.log.info("  5. Update LiteLLM config with Azure endpoints")
    else:
        pulumi.log.info("  3. Enable Azure in config if needed")

    pulumi.log.info("  See SETUP.md for detailed instructions")


if __name__ == "__main__":
    main()
```

### 4. Update Configuration Utilities

**File:** [ai/pulumi/utils/config.py](../pulumi/utils/config.py)

Add Azure configuration support:

```python
# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

"""
Configuration utilities for TrailLens AI infrastructure.

Supports both AWS Bedrock and Azure AI Services configurations.
"""

import pulumi


def load_config():
    """
    Load configuration from Pulumi config.

    Returns:
        dict: Configuration dictionary with all required settings.
    """
    config = pulumi.Config()

    # AWS Configuration
    project_name = config.require("project_name")
    region = config.require("region")
    domain = config.require("domain")
    zone_name = config.require("zone_name")
    budget_alert_email = config.require("budget_alert_email")

    # Azure Configuration (optional)
    azure_enabled = config.get_bool("azure_enabled") or False
    azure_region = config.get("azure_region") or "canadacentral"
    azure_resource_name = config.get("azure_resource_name") or f"{project_name}-ai"

    # Build configuration dictionary
    config_dict = {
        # AWS Configuration
        "project_name": project_name,
        "region": region,
        "domain": domain,
        "zone_name": zone_name,
        "budget_alert_email": budget_alert_email,
        # Azure Configuration
        "azure_enabled": azure_enabled,
        "azure_region": azure_region,
        "azure_resource_name": azure_resource_name,
        # Tags
        "tags": {
            "Project": config.get("tag_project") or "TrailLens",
            "Environment": config.get("tag_environment") or "prod",
            "ManagedBy": config.get("tag_managed_by") or "Pulumi",
            "Repository": config.get("tag_repository") or "traillens-ai",
        },
    }

    # Add any custom tags from config
    custom_tags = config.get_object("tags") or {}
    config_dict["tags"].update(custom_tags)

    return config_dict


def validate_config(config):
    """
    Validate configuration to ensure all required values are present.

    Args:
        config: Configuration dictionary.

    Raises:
        Exception: If configuration is invalid.
    """
    # Required AWS configuration
    required_keys = [
        "project_name",
        "region",
        "domain",
        "zone_name",
        "budget_alert_email",
    ]

    for key in required_keys:
        if key not in config or not config[key]:
            raise Exception(f"Missing required configuration: {key}")

    # Validate AWS region
    if config["region"] != "ca-central-1":
        raise Exception(
            f"Invalid AWS region: {config['region']}. "
            "All TrailLens infrastructure must be deployed to ca-central-1"
        )

    # Validate Azure configuration if enabled
    if config.get("azure_enabled", False):
        if not config.get("azure_region"):
            raise Exception("azure_region required when azure_enabled is true")

        # CRITICAL: Warn about non-Canadian regions
        # Allow East US 2 for current deployment (Option 2 strategy)
        # Plan migration to canadacentral when Claude models available (Q4 2026)
        allowed_regions = ["canadacentral", "eastus2"]

        if config["azure_region"] not in allowed_regions:
            raise Exception(
                f"Invalid Azure region: {config['azure_region']}. "
                f"Allowed regions: {', '.join(allowed_regions)}. "
                "Use 'eastus2' for current deployment (Claude models available), "
                "or 'canadacentral' when models become available (target: Q4 2026)."
            )

        # Warning for non-Canadian regions
        if config["azure_region"] != "canadacentral":
            pulumi.log.warn(
                f"⚠️  DATA SOVEREIGNTY WARNING: Deploying to {config['azure_region']}. "
                "Data processed by Claude will be stored/processed outside Canada. "
                "This is a temporary deployment strategy. "
                "Migration to canadacentral planned for Q4 2026 when Claude models available. "
                "Ensure compliance team is aware of cross-border data flow."
            )

    pulumi.log.info("✓ Configuration validation passed")
```

### 5. Update Stack Configuration

**File:** [ai/pulumi/Pulumi.prod.yaml](../pulumi/Pulumi.prod.yaml)

Add Azure configuration:

```yaml
config:
  # AWS Configuration (Primary - Production)
  traillens-ai:project_name: traillens
  traillens-ai:region: ca-central-1
  traillens-ai:domain: traillenshq.com
  traillens-ai:zone_name: traillenshq.com
  traillens-ai:budget_alert_email: mark.buckaway@mac.com

  # Azure Configuration (Secondary - Testing/Redundancy)
  # CURRENT: Using East US 2 (Claude models available)
  # FUTURE: Migrate to canadacentral when Claude available (Q4 2026)
  traillens-ai:azure_enabled: true
  traillens-ai:azure_region: eastus2  # Change to canadacentral in Q4 2026
  traillens-ai:azure_resource_name: traillens-ai

  # Tags
  traillens-ai:tag_project: TrailLens
  traillens-ai:tag_environment: prod
  traillens-ai:tag_managed_by: Pulumi
  traillens-ai:tag_repository: traillens-ai
```

### 6. Deployment Instructions

#### Prerequisites

1. **Azure CLI** installed and logged in
2. **Pulumi** installed and configured
3. **Azure subscription** with appropriate permissions

#### Step-by-Step Deployment

```bash
# 1. Navigate to Pulumi directory
cd ai/pulumi

# 2. Activate virtual environment
source ../scripts/setup-env.sh

# 3. Install Azure provider
pip install -r requirements.txt

# 4. Configure Pulumi stack
pulumi stack select prod

# 5. Enable Azure in configuration
pulumi config set azure_enabled true

# 6. Set Azure region (East US 2 for current deployment)
# Note: Use eastus2 now, migrate to canadacentral in Q4 2026
pulumi config set azure_region eastus2

# 7. Preview changes
pulumi preview

# 8. Deploy infrastructure
pulumi up

# 9. Retrieve outputs
pulumi stack output azure_endpoint
pulumi stack output azure_api_key --show-secrets
pulumi stack output azure_service_principal_id
pulumi stack output azure_service_principal_secret --show-secrets
```

#### Post-Deployment Steps

After Pulumi deployment completes:

1. **Navigate to Azure AI Foundry Portal:**

   ```text
   https://ai.azure.com/
   ```

2. **Create AI Hub:**

   - Use the deployed Cognitive Services account
   - **Location: East US 2** (current deployment region - Claude models available)
   - Name: `traillens-ai-hub`
   - Note: Will migrate to Canada Central when Claude available (Q4 2026)

3. **Deploy Claude Models:**

   - Navigate to Model Catalog
   - Search for "Claude"
   - **Ensure deployment region is East US 2**
   - Deploy:
     - Claude Opus 4.6
     - Claude Sonnet 4.5
     - Claude Haiku 4.5
   - Document deployment for future Canadian region migration

4. **Note Endpoint URLs:**

   - Foundry endpoint will be: `https://traillens-ai-cognitive.services.ai.azure.com/anthropic`
   - Use in LiteLLM configuration

### 7. Verify Deployment

```bash
# Check resource group
az group show --name traillens-ai-azure-rg

# Check Cognitive Services account
az cognitiveservices account show \
  --name traillens-ai-cognitive \
  --resource-group traillens-ai-azure-rg

# List keys
az cognitiveservices account keys list \
  --name traillens-ai-cognitive \
  --resource-group traillens-ai-azure-rg

# Test endpoint
export AZURE_AI_KEY=$(az cognitiveservices account keys list \
  --name traillens-ai-cognitive \
  --resource-group traillens-ai-azure-rg \
  --query key1 -o tsv)

curl -X POST "https://traillens-ai-cognitive.cognitiveservices.azure.com/openai/deployments/YOUR_DEPLOYMENT/chat/completions?api-version=2024-02-15-preview" \
  -H "Content-Type: application/json" \
  -H "api-key: $AZURE_AI_KEY" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
```

### 8. Important Limitations

**Pulumi Support for Azure AI Foundry:**
- ✅ Can create Cognitive Services Account
- ✅ Can create Service Principal and role assignments
- ✅ Can configure network rules and policies
- ❌ Cannot deploy Claude models from catalog (portal required)
- ❌ Cannot create AI Hub via Pulumi (portal required)
- ❌ Cannot configure RAI (Responsible AI) policies fully
- ❌ Limited budget API support

**Recommended Approach:**
1. Use Pulumi for base infrastructure (Account, Service Principal, Resource Group)
2. Use Azure Portal for model deployments and AI Hub configuration
3. Store outputs in Pulumi stack for reference

### 9. Cleanup

To destroy Azure resources:

```bash
# Disable Azure in config first
pulumi config set azure_enabled false

# Preview changes
pulumi preview

# Destroy Azure resources
pulumi destroy

# Or destroy specific resources
az group delete --name traillens-ai-azure-rg --yes
```

### 3. Hybrid Multi-Cloud Strategy

**Recommended Approach:** Keep AWS Bedrock as primary, add Azure manually

#### Pulumi Changes

**Minimal Impact:** No Pulumi changes required initially

1. Deploy Azure resources manually via portal
2. Store Azure credentials in environment variables
3. Update LiteLLM configuration to include Azure models
4. Test integration locally
5. Consider Pulumi integration later if needed

#### Configuration Management

**File:** [ai/pulumi/utils/config.py](../pulumi/utils/config.py)

Add optional Azure configuration:

```python
def load_config():
    config = pulumi.Config()

    config_dict = {
        # ... existing AWS config ...

        # Optional Azure configuration
        "azure_enabled": config.get_bool("azure_enabled") or False,
        "azure_resource_name": config.get("azure_resource_name"),
        "azure_region": config.get("azure_region") or "canadacentral",
    }

    return config_dict
```

**Stack Config:** [ai/pulumi/Pulumi.prod.yaml](../pulumi/Pulumi.prod.yaml)

Add:
```yaml
config:
  # ... existing config ...
  traillens-ai:azure_enabled: false  # Enable when Azure is ready
  traillens-ai:azure_resource_name: "traillens-ai"
  traillens-ai:azure_region: "canadacentral"
```

## Implementation Roadmap

### Phase 1: Azure Account Setup (Manual)

**Estimated Time:** 1-2 hours
**Status:** Ready to start (Azure account logged in)

1. ✅ Login to Azure Portal: https://portal.azure.com
2. ⬜ Navigate to Azure AI Foundry: https://ai.azure.com/
3. ⬜ Create AI Hub in Canada Central region
4. ⬜ Create AI Project under the Hub
5. ⬜ Deploy Claude Opus 4.6 from Model Catalog
6. ⬜ Deploy Claude Sonnet 4.5 from Model Catalog
7. ⬜ Deploy Claude Haiku 4.5 from Model Catalog
8. ⬜ Note endpoint URLs and API keys

**Free Trial Usage:**
- Estimated cost for testing: $20-50 of $200 credit
- Remaining credit can be used for 30 days

### Phase 2: LiteLLM Integration (Configuration)

**Estimated Time:** 30 minutes
**Status:** Pending Phase 1 completion

1. ⬜ Update [server/config/litellm-config.yaml](../server/config/litellm-config.yaml)
2. ⬜ Add Azure model configurations
3. ⬜ Update [server/.env](../server/.env) with Azure credentials
4. ⬜ Create [server/test-azure-models.sh](../server/test-azure-models.sh)
5. ⬜ Test Azure models locally via LiteLLM

**Validation Criteria:**
- All three Azure Claude models respond via LiteLLM
- Response times comparable to AWS Bedrock
- No authentication errors

### Phase 3: Testing and Validation

**Estimated Time:** 1 hour
**Status:** Pending Phase 2 completion

1. ⬜ Start local services: `./manage.sh start`
2. ⬜ Run test script: `./test-azure-models.sh`
3. ⬜ Compare responses between AWS and Azure models
4. ⬜ Test fallback configuration
5. ⬜ Monitor Azure credit usage

**Success Metrics:**
- Azure models accessible via LiteLLM
- Response quality matches AWS Bedrock
- Latency acceptable (<3 seconds for simple requests)

### Phase 4: Documentation and Handoff

**Estimated Time:** 30 minutes
**Status:** Pending Phase 3 completion

1. ⬜ Document Azure setup steps in [SETUP.md](../SETUP.md)
2. ⬜ Update [README.md](../README.md) with Azure support
3. ⬜ Create troubleshooting guide for Azure errors
4. ⬜ Update Continue.dev configuration examples

### Phase 5: Optional - Pulumi Integration

**Estimated Time:** 2-3 hours
**Status:** Optional, can be deferred

1. ⬜ Add pulumi-azure-native to requirements
2. ⬜ Create Azure component in [pulumi/components/](../pulumi/components/)
3. ⬜ Add Azure stack configuration
4. ⬜ Test Pulumi deployment (limited scope)

**Note:** Manual portal setup is recommended initially due to Pulumi limitations with AI Foundry.

## Recommendations

### 1. Immediate Actions

**Priority: High**

1. **Deploy Azure East US 2:**

   - Use $200 credit to deploy Claude models in East US 2
   - Document data sovereignty implications for compliance review
   - Validate pricing and performance vs. AWS Bedrock
   - Set up monitoring for regional latency
   - Plan migration to canadacentral (Q4 2026 target)

2. **Configure LiteLLM Hybrid:**

   - Add Azure models to existing LiteLLM config
   - Implement fallback routing
   - Test failover scenarios

3. **Document Azure Setup:**

   - Create step-by-step Azure deployment guide
   - Include screenshots for portal configuration
   - Document API key retrieval process

### 2. Long-Term Strategy

**Priority: Medium**

1. **Multi-Cloud Redundancy:**

   - Keep AWS Bedrock as primary production provider (ca-central-1)
   - Use Azure as secondary/testing provider (eastus2 currently)
   - Implement intelligent routing based on cost/latency
   - **Q4 2026 Migration:** Move Azure to canadacentral when Claude available
   - Document data flow for compliance (temporary cross-border processing)

2. **Cost Optimization:**

   - Monitor both providers' pricing changes
   - Use cheaper provider for high-volume requests
   - Reserve expensive models (Opus) for complex tasks

3. **Pulumi Integration:**

   - Defer until Azure AI Foundry has better IaC support
   - Focus on manual setup initially
   - Revisit Pulumi integration in Q2 2026

### 3. Risk Mitigation

**Priority: High**

1. **Free Trial Expiration:**
   - $200 credit expires in 30 days
   - Plan transition to paid tier or discontinue Azure
   - Set up budget alerts before trial ends

2. **Subscription Requirements:**
   - Current subscription: "Azure subscription 1" (Standard)
   - Verify Enterprise/MCA-E requirement before heavy investment
   - Check with Microsoft support if unclear

3. **Regional Availability and Migration:**

   - **CURRENT DEPLOYMENT:** East US 2 (Claude models available now)
   - **DATA SOVEREIGNTY:** Document cross-border data flow for compliance team
   - **MIGRATION PLAN:** Prepare to migrate to Canada Central in Q4 2026
   - **MONITORING:** Track Microsoft announcements for Canadian region Claude availability
   - **FALLBACK:** Maintain AWS Bedrock (ca-central-1) as compliant primary provider

### 4. Open Questions

The following questions should be addressed before production deployment:

1. **Subscription Type:**
   - Is current "Azure subscription 1" eligible for Claude models?
   - If not, what upgrade path is required?

2. **Model Availability:**
   - Are all Claude models (Opus 4.6, Sonnet 4.5, Haiku 4.5) available in Canada Central?
   - If not, which region should be used?

3. **Pricing Clarity:**
   - What are exact per-token rates for Claude models in Azure?
   - How do they compare to AWS Bedrock in practice?

4. **Support Requirements:**
   - Does Azure provide equivalent support to AWS?
   - What SLAs are available for Claude models?

## References and Sources

### Azure Documentation

- [Deploy and use Claude models in Microsoft Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/use-foundry-models-claude?view=foundry-classic)
- [Microsoft Foundry Endpoints](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/concepts/endpoints?view=foundry-classic)
- [Azure AI Foundry Pricing](https://azure.microsoft.com/en-us/pricing/details/ai-foundry/)
- [Azure Free Account](https://azure.microsoft.com/en-us/pricing/purchase-options/azure-account)
- [Claude Code on Microsoft Foundry](https://code.claude.com/docs/en/microsoft-foundry)
- [Claude in Microsoft Foundry](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry)

### LiteLLM Documentation

- [LiteLLM Azure OpenAI](https://docs.litellm.ai/docs/providers/azure/)
- [LiteLLM Azure AI Studio](https://docs.litellm.ai/docs/providers/azure_ai)
- [LiteLLM Azure Anthropic (Claude via Azure Foundry)](https://docs.litellm.ai/docs/providers/azure/azure_anthropic)
- [LiteLLM Azure AI Foundry Agents](https://docs.litellm.ai/docs/providers/azure_ai_agents)
- [LiteLLM Proxy Configs](https://docs.litellm.ai/docs/proxy/configs)

### Azure Blog Posts

- [Introducing Anthropic's Claude models in Microsoft Foundry](https://azure.microsoft.com/en-us/blog/introducing-anthropics-claude-models-in-microsoft-foundry-bringing-frontier-intelligence-to-azure/)
- [Claude Opus 4.6 now available in Microsoft Foundry](https://azure.microsoft.com/en-us/blog/claude-opus-4-6-anthropics-powerful-model-for-coding-agents-and-enterprise-workflows-is-now-available-in-microsoft-foundry-on-azure/)

### Community Resources

- [Step-by-step: Integrate Ollama Web UI with Azure OpenAI using LiteLLM Proxy](https://techcommunity.microsoft.com/blog/educatordeveloperblog/step-by-step-integrate-ollama-web-ui-to-use-azure-open-ai-api-with-litellm-proxy/4386612)
- [How to Use OpenClaw with Azure OpenAI Using LiteLLM Proxy](https://gdsks.medium.com/how-to-use-openclaw-with-azure-openai-using-litellm-proxy-7b7d05cddf13)

## Conclusion

The TrailLens AI infrastructure is well-architected for AWS Bedrock and can be extended to support Azure AI Foundry with minimal changes to the LiteLLM configuration. While Azure does not offer a free tier for Claude models, the $200 credit for new accounts provides sufficient runway for testing and validation.

**Key Takeaways:**

1. **Current Setup:** Solid AWS Bedrock implementation with Pulumi IaC
2. **Azure Integration:** Straightforward via LiteLLM configuration updates
3. **Free Trial:** $200 credit available but expires in 30 days
4. **Hybrid Strategy:** Recommended approach for redundancy and cost optimization
5. **Manual Setup:** Azure AI Foundry portal configuration required initially

**Next Steps:**

1. Deploy Azure resources via portal (Phase 1)
2. Configure LiteLLM with Azure models (Phase 2)
3. Test and validate integration (Phase 3)
4. Document setup process (Phase 4)
5. Monitor credit usage and plan long-term strategy

**Estimated Total Time:** 3-5 hours for complete integration and testing

---

**Report Prepared By:** Claude Sonnet 4.5
**Date:** February 25, 2026
**Project:** TrailLens AI Infrastructure
**Repository:** ai/
