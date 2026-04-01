# AI Infrastructure Migration to Canada - Unstructured Prompt

## Unstructured Prompt

We need to migrate TrailLens AI processing infrastructure to Canada to process data locally and reduce dependence on external tools like Claude Code.

Currently, we have Pulumi infrastructure in the `ai/` directory that sets up AWS Bedrock IAM access and creates a CNAME record (ai.traillenshq.com) pointing to the Bedrock endpoint.

**What we need to change:**

1. **Update Bedrock Model Support:**
   - Update Bedrock IAM policies to support the latest Claude models:
     - Claude Opus 4.6 (currently configured for 4.6, just verify ARN)
     - Claude Sonnet 4.6 (currently using 4.5, needs update to 4.6)
   - Keep existing Haiku 4.5 support
   - Ensure ARNs are correct for ca-central-1 region
   - **Add image generation support:**
     - Amazon Titan Image Generator V2 in us-east-1
     - IAM permissions for both ca-central-1 and us-east-1 regions

2. **Remove DNS from Bedrock Stack:**
   - Remove the ai.traillenshq.com CNAME record from the bedrock DNS component
   - We're repurposing that domain for our own EC2 instance
   - The DNS component (`ai/pulumi/components/dns.py`) should be removed or disabled

3. **Create New EC2-Based AI Infrastructure:**
   - Set up an EC2 instance in ca-central-1 (Montreal) for data sovereignty
   - Instance specs: ARM processor, 8GB RAM, 2 vCPU, 40GB disk
   - Use existing infra VPC for integration with current infrastructure
   - Assign one Elastic IP to the instance
   - Point ai.traillenshq.com to the Elastic IP

4. **Install and Configure Services on EC2:**
   - **LiteLLM**: Proxy server for managing LLM API calls (OpenAI-compatible API)
   - **OpenCode Server**: Headless HTTP service (runs on port 4096, served at root `/`)
   - **OpenCode Web UI**: Official browser-based interface (runs on port 3001, served at `/ui`)
   - **OpenCode-Web (bjesus)**: Community web UI (disabled by default, can enable at `/chat` later for testing)

5. **Service Architecture:**
   - Use Podman Compose for container orchestration (rootless, secure)
   - Use Nginx as reverse proxy with Let's Encrypt for SSL certificates
   - Path-based routing on ai.traillenshq.com:
     - `/` → **OpenCode Server** (port 4096) - root URL
     - `/ui` → **OpenCode Web UI** (port 3001)
     - `/litellm` → **LiteLLM** service
   - **Disabled by default** (enable later after testing):
     - `/chat` → bjesus/opencode-web static UI

6. **Automated Instance Scheduling (Cost Optimization):**
   - EventBridge Scheduler to automatically start EC2 instance at 7:00 AM Eastern Time
   - EventBridge Scheduler to automatically stop EC2 instance at 12:00 AM (midnight) Eastern Time
   - Instance runs 17 hours/day (7 AM - 12 AM) instead of 24/7
   - Reduces EC2 costs by ~29% (only charged for running hours)
   - Timezone: America/Toronto (Eastern Time with DST support)

7. **Cost Monitoring (AWS Budgets):**
   - AWS Budget alert for Bedrock usage across all models
   - Threshold: $75/month for all Bedrock API calls
   - Email notifications when 80% and 100% of budget is reached
   - Covers both ca-central-1 (text) and us-east-1 (images) usage
   - SNS topic for alert delivery

## Quick Capture

**What I'm trying to achieve:**
- Process Canadian user data within Canadian borders (ca-central-1)
- Reduce external dependencies on third-party AI tools
- Self-host AI infrastructure with LiteLLM and OpenCode
- Use latest Claude models (Opus 4.6, Sonnet 4.6) in ca-central-1
- Add image generation with Amazon Titan Image Generator V2 in us-east-1
- Optimize costs by running EC2 instance only during business hours (7 AM - 12 AM ET)

**Files/components probably involved:**
- `ai/pulumi/__main__.py` - Main Pulumi orchestration
- `ai/pulumi/components/bedrock.py` - Bedrock IAM policies (update model versions)
- `ai/pulumi/components/dns.py` - Remove or disable DNS CNAME
- `ai/pulumi/components/ec2.py` - New component for EC2 instance
- `ai/pulumi/components/networking.py` - New component for Elastic IP and security groups
- `ai/pulumi/components/scheduler.py` - New component for EventBridge schedules (start/stop)
- `ai/pulumi/components/budget.py` - New component for AWS Budget alerts ($75/month threshold)
- `ai/pulumi/Pulumi.yaml` - Project configuration
- Infra VPC StackReference for VPC/subnet integration

**Technology/tools I think we'll need:**
- **Pulumi Python SDK** for infrastructure as code
- **EC2 Instance Type**: t4g.large (ARM Graviton2, 2 vCPU, 8GB RAM) - matches memory requirements
- **Linux Distribution**: Amazon Linux 2023 (AL2023) ARM edition - optimized for AWS, great ARM support, latest security updates
- **EventBridge Scheduler** - Automated start/stop schedules with timezone support
- **IAM Role for EventBridge** - Permissions to start/stop EC2 instances
- **AWS Budgets** - Cost monitoring and alerts for Bedrock usage
- **SNS Topic** - Email notifications for budget alerts
- **Node.js** - Required for OpenCode CLI
- **Podman & Podman Compose** - rootless container runtime
- **Nginx** - reverse proxy and SSL termination
- **Certbot** - Let's Encrypt SSL certificate management
- **LiteLLM** - LLM proxy server (Python-based, Docker image available, supports multi-region Bedrock)
- **OpenCode CLI** - Command-line interface for OpenCode server and web UI
- **OpenCode Server** - Headless API service (runs on port 4096, for API access)
- **OpenCode Web UI** - Official browser-based interface (runs on port 3001, via `opencode web`)
- **OpenCode-Web (bjesus)** - Community SolidJS chat interface (static build, served via Nginx)
- **Elastic IP** - Static public IP for ai.traillenshq.com
- **Route53** - DNS A record for ai.traillenshq.com → Elastic IP
- **Security Groups** - Firewall rules (ports 80, 443, 22)
- **EBS Volume** - 40GB gp3 volume for instance storage

**Things I'm concerned about:**
- Security: Services exposed to internet must be properly secured
- SSL certificate renewal automation (certbot needs proper cron job)
- Bedrock model ARN changes - need to verify exact ARNs for Claude Opus 4.6 and Sonnet 4.6
- Multi-region Bedrock access - IAM permissions for both ca-central-1 (text) and us-east-1 (images)
- Image generation data leaves Canada (goes to us-east-1) - acceptable trade-off
- OpenCode server authentication - requires OPENCODE_SERVER_PASSWORD env var
- **Memory constraints**: 8GB may be tight given OpenCode's documented memory leak (issue #5363 shows 70GB spikes)
- Podman rootless permissions - SELinux and user namespaces on AL2023
- Cost management - t4g.large + Elastic IP + 40GB EBS in ca-central-1
- Bedrock usage monitoring - need alerts when exceeding $75/month across all models
- Backup strategy for EC2 instance configuration and data
- VPC integration - ensuring proper subnet selection and security group rules
- EventBridge scheduling with Daylight Saving Time - America/Toronto handles DST automatically
- Services starting correctly after automated instance start - need startup scripts
- Elastic IP association during stop/start cycle - should persist automatically

**Things I'm not sure about yet:**
- Should we use a separate EBS volume or instance store for the 40GB disk?
  - Recommendation: EBS gp3 volume (persistent, can be backed up, can be resized)
- What's the default landing page at ai.traillenshq.com/?
  - Recommendation: Simple static page with links to /litellm/docs and /opencode/docs
- Do we need CloudWatch monitoring for the EC2 instance?
  - Recommendation: Yes, **critical** for memory monitoring given 8GB constraint and OpenCode memory leak risk
- LiteLLM configuration - which models should it proxy?
  - Recommendation: Configure for:
    - Bedrock ca-central-1: Claude Opus 4.6, Sonnet 4.6, Haiku 4.5 (text models)
    - Bedrock us-east-1: Amazon Titan Image Generator V2 (image generation)
- OpenCode server configuration - which IDE plugins will connect?
  - Recommendation: Configure for VS Code, Continue.dev plugins
- Will 8GB RAM be sufficient given OpenCode's known memory leak?
  - Concern: OpenCode issue #5363 shows memory growing to 70GB
  - Mitigation: Container memory limits, scheduled restarts, aggressive monitoring
  - Recommendation: Cloudflare Tunnel (free, no auth token needed, persistent)
  - Alternative: ngrok (requires free account and auth token)
  - Fallback: Localtunnel (no auth, but less reliable)
- Should OpenCode Mobile tunnel be path-based or port-based?
  - Recommendation: Keep OpenCode on port 4096 for tunnel, use Nginx for web access

**Related resources:**
- OpenCode Server Documentation: https://opencode.ai/docs/server/
- OpenCode Web Documentation: https://opencode.ai/docs/web/
- OpenCode Mobile GitHub: https://github.com/doza62/opencode-mobile
- OpenCode-Web (bjesus) GitHub: https://github.com/bjesus/opencode-web
- OpenCode Plugins Documentation: https://opencode.ai/docs/plugins/
- LiteLLM Documentation: https://docs.litellm.ai/
- AWS Bedrock Model IDs: https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html
- GitHub Actions Self-Hosted Runner: https://docs.github.com/en/actions/hosting-your-own-runners
- Amazon Linux 2023: https://aws.amazon.com/linux/amazon-linux-2023/
- AWS Graviton (ARM): https://aws.amazon.com/ec2/graviton/
- EventBridge Scheduler: https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html
- EventBridge Scheduler Timezones: https://docs.aws.amazon.com/scheduler/latest/UserGuide/schedule-types.html
- Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
- Expo Push Notifications: https://docs.expo.dev/push-notifications/overview/

## Notes & Context

### Current Infrastructure State

The `ai/` directory currently has a Pulumi stack that:
1. Creates an IAM user with Bedrock access policies
2. Generates access keys for programmatic Bedrock access
3. Creates a Route53 CNAME record (ai.traillenshq.com → bedrock-runtime.REGION.amazonaws.com)

This was designed for developers to use Continue.dev or Claude Code with direct Bedrock access.

### Why We're Migrating

1. **Data Sovereignty**: Canadian data must be processed in Canada (ca-central-1)
2. **Cost Control**: Self-hosted LiteLLM can manage and monitor API costs
3. **Flexibility**: LiteLLM supports multiple LLM providers (Bedrock, OpenAI, Anthropic, etc.)
4. **Self-Sufficiency**: Reduce dependency on external tools like Claude Code
5. **CI/CD Integration**: Self-hosted GitHub runner for automation in Canadian infrastructure

### Architecture Decisions

**EC2 Instance Recommendation:**
- **Instance Type**: t4g.medium
  - 2 vCPU (ARM Graviton2 processor)
  - 4 GB RAM (meets requirement exactly)
  - EBS-optimized
  - Cost-effective (~$30/month in ca-central-1)
  - ARM architecture (requirement: "Amazon ARM processor")

**Linux Distribution Recommendation:**
- **Amazon Linux 2023 (AL2023) ARM Edition**
  - Optimized for AWS and ARM Graviton processors
  - Long-term support with quarterly updates
  - systemd for service management
  - dnf package manager (modern, fast)
  - Built-in AWS tools and optimizations
  - Strong security defaults with SELinux
  - Better than Ubuntu for AWS-specific workloads

**Alternative Considered:**
- Ubuntu 24.04 LTS ARM: More familiar to some developers, but less optimized for AWS
- RHEL 9 ARM: Enterprise-grade but overkill for single instance

**Storage:**
- 40GB EBS gp3 volume (general purpose SSD)
- Allows snapshots for backup
- Can be resized if needed
- Persistent across instance stop/start

**Networking:**
- Use existing VPC from infra submodule (via StackReference)
- Elastic IP for static public addressing
- Security group: Allow 22 (SSH), 80 (HTTP), 443 (HTTPS)
- Route53 A record: ai.traillenshq.com → Elastic IP

**Service Ports (Internal):**
- LiteLLM: 8000 (default)
- OpenCode Server (API): 4096 (headless API endpoint)
- OpenCode Web UI: 3001 (browser interface)
- Nginx: 80, 443 (public-facing)

**Nginx Path Routing:**
```
ai.traillenshq.com/          → Static landing page with service links
ai.traillenshq.com/litellm/  → Proxy to LiteLLM:8000 (LLM proxy API)
ai.traillenshq.com/opencode/ → Proxy to OpenCode Server:4096 (API endpoint)
ai.traillenshq.com/web/      → Proxy to OpenCode Web UI:3001 (official interface)
ai.traillenshq.com/chat/     → Static files: OpenCode-Web (SolidJS chat UI)
```

**Automated Scheduling:**
- **Start Schedule**: EventBridge Scheduler rule at 7:00 AM America/Toronto
  - Cron expression: `cron(0 7 * * ? *)`
  - Action: EC2 StartInstances API call
  - Timezone: America/Toronto (handles DST automatically)

- **Stop Schedule**: EventBridge Scheduler rule at 12:00 AM (midnight) America/Toronto
  - Cron expression: `cron(0 0 * * ? *)`
  - Action: EC2 StopInstances API call
  - Timezone: America/Toronto (handles DST automatically)

- **IAM Role**: EventBridge needs permission to call EC2 StartInstances/StopInstances
  - Policy: Allow ec2:StartInstances and ec2:StopInstances for the specific instance
  - Trust policy: Allow scheduler.amazonaws.com to assume role

**OpenCode Mobile Configuration:**

Mobile app support requires:

1. **Server-Side Installation:**
   - OpenCode CLI installed on EC2 instance
   - Node.js runtime (for npx command)
   - opencode-mobile plugin: `npx opencode-mobile install`

2. **Tunnel Provider Setup (Choose One):**
   - **Cloudflare Tunnel** (Recommended):
     - Free, no authentication required
     - Persistent and reliable
     - Install: `npm install -g cloudflared`
     - Auto-selected by opencode-mobile
   - **ngrok**:
     - Free tier available
     - Requires account and auth token
     - Install: Download from ngrok.com
     - Configure: `ngrok config add-authtoken YOUR_TOKEN`
   - **Localtunnel**:
     - Completely free, no auth
     - Less reliable, URLs change frequently
     - Install: `npm install -g localtunnel`

3. **Mobile App Features:**
   - **Push Notifications**: Via Expo push notification service
   - **Remote Access**: Continue OpenCode sessions from mobile
   - **QR Code Connection**: Scan QR to connect mobile app to server
   - **Session Sync**: Sync sessions between desktop and mobile

4. **Installation Command:**
   ```bash
   # Install opencode-mobile plugin
   npx opencode-mobile install

   # This will:
   # - Update ~/.config/opencode/opencode.json with mobile config
   # - Create /mobile command in OpenCode CLI
   # - Configure tunnel provider (auto-selects: Cloudflare > ngrok > Localtunnel)
   # - Set up push notification tokens
   ```

5. **Environment Variables:**
   - `TUNNEL_PROVIDER`: Force specific tunnel provider (cloudflare|ngrok|localtunnel)
   - `OPENCODE_MOBILE_DEBUG`: Enable debug logging
   - `OPENCODE_PORT`: OpenCode server port (default: 4096)

6. **Usage:**
   ```bash
   # Start OpenCode server with mobile support
   opencode serve --port 4096

   # Generate QR code for mobile connection
   # (Run this from within OpenCode CLI)
   /mobile

   # Scan QR with OpenCode Mobile app (iOS/Android)
   ```

7. **Systemd Service Considerations:**
   - OpenCode server should run as systemd service
   - Tunnel should auto-start with OpenCode server
   - Service needs environment variables for tunnel provider
   - Must persist tunnel URL across restarts (if possible)

8. **Security:**
   - Tunnel provides HTTPS encryption automatically
   - Mobile app uses Expo push tokens for authentication
   - No additional firewall ports needed (tunnel handles routing)
   - Consider OPENCODE_SERVER_PASSWORD for additional security

**OpenCode Web UI Configuration:**

The built-in web interface provides browser-based access to OpenCode:

1. **Running the Web UI:**
   ```bash
   # Start web UI on specific port
   opencode web --port 3001 --hostname 0.0.0.0
   ```

2. **Configuration Options:**
   - `--port 3001`: Fixed port for consistent Nginx proxying
   - `--hostname 0.0.0.0`: Allow network access (default is 127.0.0.1)
   - `--cors`: Enable CORS for specific domains if needed
   - `OPENCODE_SERVER_PASSWORD`: Required for secure network access

3. **Systemd Service:**
   ```bash
   # Create systemd service for OpenCode Web UI
   sudo systemctl enable opencode-web.service
   sudo systemctl start opencode-web.service
   ```

4. **Session Sharing:**
   - Web UI and terminal CLI share the same sessions
   - Can use `opencode attach` from terminal to access web sessions
   - State synchronized across all interfaces (web, terminal, mobile)

5. **Security:**
   - Set `OPENCODE_SERVER_PASSWORD` environment variable
   - Access via Nginx reverse proxy with HTTPS
   - Same authentication for API and Web UI

**OpenCode-Web (bjesus) - Community Chat Interface:**

Modern SolidJS-based chat interface for OpenCode with enhanced features:

1. **What It Is:**
   - Community-built web UI by bjesus (MIT licensed)
   - Modern chat interface with real-time streaming
   - Built with SolidJS, Tailwind CSS, DaisyUI themes
   - Token/cost tracking, virtual scrolling, mobile-responsive

2. **Deployment Approach:**
   - Use **Frontend Mode** (static production build)
   - Build once: `npm run build`
   - Serve static files via Nginx at `/chat/`
   - Connects to OpenCode Server API at port 4096

3. **Installation Steps:**
   ```bash
   # Clone repository
   git clone https://github.com/bjesus/opencode-web.git /opt/opencode-web
   cd /opt/opencode-web

   # Install dependencies and build
   npm install
   npm run build

   # Build output goes to dist/ directory
   # Nginx will serve this at ai.traillenshq.com/chat/
   ```

4. **Nginx Configuration:**
   - Serve static files from `/opt/opencode-web/dist/`
   - Path: `/chat/`
   - Configure API endpoint to point to `https://ai.traillenshq.com/opencode/`

5. **Features:**
   - Real-time SSE streaming for live responses
   - Virtual scrolling for performance with large histories
   - 32 DaisyUI themes for customization
   - Token and cost tracking
   - Session management
   - Mobile-responsive design

6. **Advantages Over Official Web UI:**
   - More modern, polished chat interface
   - Better performance with virtual scrolling
   - Theme customization (32 themes)
   - Enhanced token/cost tracking
   - Active community development

**LiteLLM Architecture (CRITICAL):**

**IMPORTANT**: All OpenCode components must connect ONLY to LiteLLM, never directly to Bedrock.

```
┌──────────────────────────────────────────────────────────────────┐
│                         EC2 Instance                             │
│                        (ca-central-1)                            │
│                                                                   │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────┐          │
│  │ OpenCode CLI │   │ OpenCode Web │   │ OpenCode   │          │
│  │  (Terminal)  │   │      UI      │   │   Mobile   │          │
│  └──────┬───────┘   └──────┬───────┘   └─────┬──────┘          │
│         │                  │                   │                  │
│         └──────────────────┼───────────────────┘                  │
│                            │                                      │
│                     ┌──────▼────────┐                            │
│                     │   LiteLLM     │ ◄── ALL requests go here  │
│                     │   (Port 8000) │                            │
│                     └──────┬────────┘                            │
│                            │                                      │
│              ┌─────────────┴──────────────┐                      │
└──────────────┼────────────────────────────┼──────────────────────┘
               │                            │
        ┌──────▼──────────┐        ┌───────▼────────────┐
        │ AWS Bedrock     │        │  AWS Bedrock       │
        │ ca-central-1    │        │  us-east-1         │
        │                 │        │                    │
        │ Text Models:    │        │ Image Models:      │
        │ - Opus 4.6      │        │ - Titan Image V2   │
        │ - Sonnet 4.6    │        │                    │
        │ - Haiku 4.5     │        │                    │
        └─────────────────┘        └────────────────────┘
         (Canadian data)            (Image gen only)
```

**Configuration Requirements:**

1. **LiteLLM Configuration:**
   - Configure with Bedrock credentials (IAM user from existing ai/ stack)
   - Set up model mappings:
     - **Text models** (ca-central-1): Opus 4.6, Sonnet 4.6, Haiku 4.5
     - **Image models** (us-east-1): Amazon Titan Image Generator V2
   - Multi-region Bedrock support
   - Expose OpenAI-compatible API on port 8000
   - Enable logging and cost tracking

2. **OpenCode Configuration:**
   - Configure OpenCode to use LiteLLM as LLM provider
   - API endpoint: `http://localhost:8000` (or `http://litellm:8000` in containers)
   - Use OpenAI-compatible format (LiteLLM provides OpenAI API compatibility)
   - No direct Bedrock credentials in OpenCode configuration

3. **Benefits:**
   - **Centralized access control**: Single point for Bedrock credentials
   - **Multi-region support**: Automatic routing to ca-central-1 for text, us-east-1 for images
   - **Cost tracking**: LiteLLM logs all requests and costs (including cross-region)
   - **Provider flexibility**: Can add OpenAI, Anthropic, etc. without changing OpenCode config
   - **Security**: Bedrock credentials only in one place (LiteLLM)
   - **Monitoring**: Single point for request logging and metrics

4. **LiteLLM Model Configuration** (example):
   ```yaml
   # config.yaml for LiteLLM
   model_list:
     # Text models in ca-central-1
     - model_name: claude-opus-4-6
       litellm_params:
         model: bedrock/anthropic.claude-opus-4-6
         aws_region_name: ca-central-1

     - model_name: claude-sonnet-4-6
       litellm_params:
         model: bedrock/anthropic.claude-sonnet-4-6
         aws_region_name: ca-central-1

     - model_name: claude-haiku-4-5
       litellm_params:
         model: bedrock/anthropic.claude-haiku-4-5-20251001:0
         aws_region_name: ca-central-1

     # Image generation in us-east-1
     - model_name: titan-image-v2
       litellm_params:
         model: bedrock/amazon.titan-image-generator-v2:0
         aws_region_name: us-east-1

   general_settings:
     master_key: ${LITELLM_MASTER_KEY}  # Set via environment variable
     database_url: sqlite:///litellm.db   # For cost tracking
   ```

5. **OpenCode Configuration File** (`~/.config/opencode/opencode.json`):
   ```json
   {
     "providers": {
       "bedrock": {
         "type": "openai",
         "apiEndpoint": "http://localhost:8000/v1",
         "models": [
           {
             "id": "claude-opus-4-6",
             "name": "Claude Opus 4.6"
           },
           {
             "id": "claude-sonnet-4-6",
             "name": "Claude Sonnet 4.6"
           },
           {
             "id": "titan-image-v2",
             "name": "Titan Image Generator V2"
           }
         ]
       }
     },
     "defaultProvider": "bedrock"
   }
   ```

### Deployment Strategy

**Phase 1: Update Bedrock IAM**
- Update bedrock.py to use Claude Sonnet 4.6 ARN
- Verify Claude Opus 4.6 ARN is correct
- Add IAM permissions for Amazon Titan Image Generator V2 in us-east-1
- Update IAM policy to allow Bedrock access in BOTH ca-central-1 AND us-east-1
- Model ARNs to include:
  - `arn:aws:bedrock:ca-central-1::foundation-model/anthropic.claude-opus-4-6`
  - `arn:aws:bedrock:ca-central-1::foundation-model/anthropic.claude-sonnet-4-6*`
  - `arn:aws:bedrock:ca-central-1::foundation-model/anthropic.claude-haiku-4-5*`
  - `arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-image-generator-v2:0`

**Phase 2: Remove DNS CNAME**
- Comment out or remove dns.py component
- Remove DNS exports from __main__.py
- Deploy to remove the CNAME record

**Phase 3: Create EC2 Infrastructure & Cost Monitoring**
- Create new Pulumi components:
  - `ec2.py`: Instance, EBS volume, user data script
  - `networking.py`: Elastic IP, Security Group, Route53 A record
  - `scheduler.py`: EventBridge schedules (start at 7 AM, stop at midnight ET)
  - `budget.py`: AWS Budget for Bedrock cost monitoring ($75/month threshold)
- Reference existing VPC via StackReference to infra stack
- Deploy EC2 instance with automated scheduling
- Deploy AWS Budget with SNS email notifications

**Phase 4: Configure EC2 Instance**
- User data script or manual setup:
  - Install Node.js (required for OpenCode CLI and npx)
  - Install Podman, Podman Compose, Nginx, Certbot
  - Install OpenCode CLI: `npm install -g @opencode/cli` or via curl
  - Install tunnel provider (Cloudflare Tunnel recommended)
  - Install opencode-mobile plugin: `npx opencode-mobile install`
  - Build OpenCode-Web (bjesus):
    - Clone repo: `git clone https://github.com/bjesus/opencode-web.git /opt/opencode-web`
    - Build: `cd /opt/opencode-web && npm install && npm run build`
  - Configure LiteLLM:
    - Create config.yaml with multi-region Bedrock support
    - Set up text models (ca-central-1) and image models (us-east-1)
    - Configure AWS credentials from Bedrock IAM user
    - Enable SQLite database for cost tracking
  - Clone podman-compose.yml configuration
  - Set up systemd services (OpenCode server, OpenCode web, LiteLLM, Nginx, GitHub runner)
  - Configure Nginx with SSL (Let's Encrypt)
  - Configure Nginx to serve opencode-web static files from `/opt/opencode-web/dist/`
  - Configure OpenCode server environment variables
  - Install and configure GitHub Actions runner

**Phase 5: Testing & Validation**
- Test HTTPS access to ai.traillenshq.com
- Validate LiteLLM API endpoints
- Validate OpenCode server API endpoints (via web and tunnel)
- Test OpenCode Web UIs:
  - Official Web UI: ai.traillenshq.com/web/
  - Community Chat UI: ai.traillenshq.com/chat/
  - Verify both connect to OpenCode Server correctly
  - Test real-time streaming in chat UI
  - Verify session sharing between all interfaces
- Test OpenCode mobile app connection:
  - Run `/mobile` command in OpenCode CLI
  - Scan QR code with mobile app
  - Verify push notifications work
  - Test session sync between desktop and mobile
- Verify all OpenCode interfaces connect ONLY to LiteLLM (not direct Bedrock)
- Test image generation with Amazon Titan Image Generator V2:
  - Send text-to-image request via LiteLLM
  - Verify request routes to us-east-1
  - Confirm image is generated and returned
  - Check LiteLLM cost tracking logs
- Test AWS Budget alerts:
  - Confirm SNS topic subscription email received
  - Verify budget is tracking Bedrock costs
  - Check AWS Budgets console for current spending
- Test GitHub Actions runner with a test workflow
- Verify SSL certificate auto-renewal
- Test EventBridge schedules (manually trigger or wait for scheduled time)
- Verify services restart correctly after automated start
- Confirm Elastic IP remains associated through stop/start cycle
- Verify tunnel reconnects after instance restart

### Security Considerations

1. **SSH Access Control (CRITICAL):**

   **Pulumi Config-Based IP Restrictions:**
   - Store trusted IP addresses in Pulumi stack config (not hardcoded)
   - Support multiple IP addresses/CIDR blocks
   - Configuration approach:
     ```bash
     # Set trusted IPs in Pulumi config
     pulumi config set trustedSshIps "YOUR_IP/32,OFFICE_IP/32,VPN_CIDR/24"
     ```
   - Security Group implementation in `networking.py`:
     ```python
     config = pulumi.Config()
     trusted_ips = config.require("trustedSshIps").split(",")

     security_group = aws.ec2.SecurityGroup(
         "ai-sg",
         ingress=[
             {
                 "protocol": "tcp",
                 "from_port": 22,
                 "to_port": 22,
                 "cidr_blocks": trusted_ips,
                 "description": "SSH from trusted IPs only"
             },
             # ... HTTP/HTTPS rules
         ]
     )
     ```

   **SSH Key Authentication Only:**
   - **REQUIRED**: EC2 instance must be launched with SSH key pair
   - Key pair must be created in AWS before Pulumi deployment
   - User data script MUST disable password authentication:
     ```bash
     #!/bin/bash
     # Harden SSH configuration
     sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
     sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
     sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
     echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config
     systemctl restart sshd
     ```
   - Key pair name passed via Pulumi config:
     ```bash
     pulumi config set sshKeyName "your-ec2-keypair-name"
     ```
   - EC2 instance configuration:
     ```python
     config = pulumi.Config()
     key_name = config.require("sshKeyName")

     instance = aws.ec2.Instance(
         "ai-instance",
         key_name=key_name,  # Required for SSH access
         user_data=user_data_script,  # Includes SSH hardening
         # ... other config
     )
     ```

   **Additional SSH Hardening:**
   - Disable root login (enforced in user data script)
   - Only allow public key authentication
   - Consider fail2ban for brute force protection
   - Audit SSH access via CloudWatch Logs

   **Dynamic IP Management:**
   - For users with dynamic home IPs:
     ```bash
     # Update config when IP changes
     pulumi config set trustedSshIps "NEW_IP/32,OFFICE_IP/32"
     pulumi up  # Updates Security Group
     ```
   - Alternative: Use VPN with static IP range

   **Bell Canada / Virgin Plus IP Ranges (Guelph, Ontario):**

   **Note:** Bell announced discontinuation of Virgin Plus Internet/TV in Ontario as of January 2026. Residential service is now under Bell Canada branding.

   **Common Bell Canada Residential IP Ranges:**

   Primary residential blocks (likely to be assigned in Guelph area):
   - `70.24.0.0/16` through `70.31.0.0/16` (8 contiguous /16 blocks)
   - `142.112.0.0/16` through `142.189.0.0/16` (large range)
   - `184.144.0.0/16` through `184.151.0.0/16` (8 contiguous /16 blocks)
   - `174.88.0.0/16` through `174.95.0.0/16`
   - `76.64.0.0/16` through `76.71.0.0/16`
   - `50.100.0.0/16`, `50.101.0.0/16`
   - `64.228.0.0/16`, `64.229.0.0/16`, `64.231.0.0/16`
   - `65.92.0.0/16` through `65.95.0.0/16`
   - `67.68.0.0/16` through `67.71.0.0/16`
   - `69.156.0.0/16` through `69.159.0.0/16`
   - `74.12.0.0/16` through `74.15.0.0/16`

   **Security Recommendation:**
   - **DO NOT whitelist entire /16 blocks** - these contain 65,536 addresses each
   - **Best practice**: Use your specific /32 IP address only
   - **Acceptable alternative**: Use smaller subnet from your ISP (e.g., /24 or /28)
   - **Query your current IP**: `curl ifconfig.me` to find your exact address

   **Example Configuration for Bell Canada home user:**
   ```bash
   # Get your current IP
   MY_IP=$(curl -s ifconfig.me)

   # Set only your specific IP
   pulumi config set trustedSshIps "${MY_IP}/32"

   # Or if you need multiple locations
   pulumi config set trustedSshIps "70.30.123.45/32,142.150.67.89/32"
   ```

   **References:**
   - [AS577 Bell Canada on IPinfo.io](https://ipinfo.io/AS577)
   - [AS7122 Bell Canada on IPinfo.io](https://ipinfo.io/AS7122)
   - [Bell Canada Network Ranges on Netify](https://www.netify.ai/resources/telco/bell-canada)
   - [Bell Virgin Plus discontinuation announcement](https://www.iphoneincanada.ca/2025/10/15/bell-to-kill-off-virgin-internet-and-tv-in-ontario-axe-tv-boxes/)

2. **Firewall (Security Group):**
   - Minimize open ports (only 22, 80, 443)
   - SSH restricted to trusted IPs via Pulumi config
   - HTTP/HTTPS open for public access (services behind Nginx)
   - All outbound traffic allowed (for updates, Bedrock API calls)

3. **Authentication:**
   - OpenCode server: OPENCODE_SERVER_PASSWORD environment variable
   - LiteLLM: API key authentication
   - GitHub runner: Token-based authentication
   - SSH: Key-based only (passwords disabled)

3. **SSL/TLS:**
   - Let's Encrypt certificates via Certbot
   - Auto-renewal with systemd timer
   - Force HTTPS redirect in Nginx

4. **Container Security:**
   - Podman rootless mode (no root daemon)
   - SELinux enabled on AL2023
   - Regular container image updates

5. **Secrets Management:**
   - Use AWS Secrets Manager for sensitive credentials
   - Inject secrets as environment variables in Podman Compose
   - Never commit credentials to version control

### Cost Estimate (ca-central-1)

**WITHOUT Automated Scheduling (24/7):**
- t4g.medium instance: ~$30/month (on-demand, 24/7)
- Elastic IP: $0/month (while associated)
- 40GB EBS gp3: ~$3.20/month
- Data transfer: Variable (first 100GB/month free)
- **Total: ~$33-40/month**

**WITH Automated Scheduling (17 hours/day: 7 AM - 12 AM ET):**
- t4g.medium instance: ~$21/month (on-demand, 17 hrs/day = 71% of 24/7 cost)
- Elastic IP: $0/month (while associated)
- 40GB EBS gp3: ~$3.20/month (charged regardless of instance state)
- EventBridge Scheduler: $0/month (first 14 million invocations free, we use 2/day)
- Data transfer: Variable (first 100GB/month free)
- **Total: ~$24-27/month (29% savings)**

Plus Bedrock API usage (pay-per-use).

**Cost Savings:**
- Running 17 hours/day instead of 24/7 saves ~$9/month on EC2 costs
- Estimated annual savings: ~$108/year
- EBS storage is still charged during stopped state (no savings there)

### Bedrock Model ARNs (Needs Verification)

**Text Models (ca-central-1):**
- Opus 4.6: `anthropic.claude-opus-4-6`
- Sonnet 4.5: `anthropic.claude-sonnet-4-5-v2:0` (NEEDS UPDATE to 4.6)
  - Possible 4.6 ARN: `anthropic.claude-sonnet-4-6` or `anthropic.claude-sonnet-4-6-v1:0`
- Haiku 4.5: `anthropic.claude-haiku-4-5-20251001:0`

**Image Models (us-east-1):**
- Titan Image Generator V2: `amazon.titan-image-generator-v2:0`

**Multi-Region IAM Policy:**
The IAM policy in bedrock.py needs to allow Bedrock access in BOTH regions:
```python
"Resource": [
    # Text models in ca-central-1
    "arn:aws:bedrock:ca-central-1::foundation-model/anthropic.claude*",
    # Image models in us-east-1
    "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-image-generator-v2:0",
]
```

Check AWS Bedrock console or documentation for exact ARNs.

### AWS Budget Configuration (Cost Monitoring)

**Budget Alert for Bedrock Usage:**

AWS Budgets will monitor ALL Bedrock usage and send email alerts when spending exceeds thresholds.

**Configuration:**
```python
# ai/pulumi/components/budget.py
import pulumi_aws as aws

def create_bedrock_budget(project_name, alert_email, budget_amount=75):
    """
    Create AWS Budget to monitor Bedrock usage across all regions.

    Args:
        project_name: Project name for resource naming
        alert_email: Email address for budget alerts
        budget_amount: Monthly budget limit in USD (default: $75)
    """

    # Create SNS topic for budget alerts
    budget_topic = aws.sns.Topic(
        f"{project_name}-bedrock-budget-alerts",
        name=f"{project_name}-bedrock-budget-alerts"
    )

    # Subscribe email to SNS topic
    email_subscription = aws.sns.TopicSubscription(
        f"{project_name}-budget-email-sub",
        topic=budget_topic.arn,
        protocol="email",
        endpoint=alert_email
    )

    # Create budget for Bedrock usage
    bedrock_budget = aws.budgets.Budget(
        f"{project_name}-bedrock-budget",
        name=f"{project_name}-bedrock-monthly",
        budget_type="COST",
        limit_amount=str(budget_amount),
        limit_unit="USD",
        time_unit="MONTHLY",
        cost_filters={
            "Service": ["Amazon Bedrock"]  # Only Bedrock costs
        },
        notifications=[
            # Alert at 80% of budget
            {
                "comparison_operator": "GREATER_THAN",
                "threshold": 80,
                "threshold_type": "PERCENTAGE",
                "notification_type": "ACTUAL",
                "subscriber_sns_topic_arns": [budget_topic.arn]
            },
            # Alert at 100% of budget
            {
                "comparison_operator": "GREATER_THAN",
                "threshold": 100,
                "threshold_type": "PERCENTAGE",
                "notification_type": "ACTUAL",
                "subscriber_sns_topic_arns": [budget_topic.arn]
            },
            # Forecast alert at 100%
            {
                "comparison_operator": "GREATER_THAN",
                "threshold": 100,
                "threshold_type": "PERCENTAGE",
                "notification_type": "FORECASTED",
                "subscriber_sns_topic_arns": [budget_topic.arn]
            }
        ]
    )

    return {
        "budget": bedrock_budget,
        "sns_topic": budget_topic,
        "email_subscription": email_subscription
    }
```

**Alert Triggers:**
1. **80% threshold** (ACTUAL): Alert when actual spending reaches $60 ($75 × 0.80)
2. **100% threshold** (ACTUAL): Alert when actual spending reaches $75
3. **100% threshold** (FORECAST): Alert when AWS forecasts you'll exceed $75 by month end

**What Gets Monitored:**
- All Bedrock model usage (text and image generation)
- Both ca-central-1 (Claude models) and us-east-1 (Titan Image) regions
- Total combined cost across all models

**Email Notifications:**
You'll receive emails at the specified address when:
- Spending reaches 80% of budget ($60)
- Spending reaches 100% of budget ($75)
- AWS forecasts spending will exceed budget by end of month

**Cost Breakdown in Alerts:**
Emails will include:
- Current spending vs. budget
- Percentage of budget used
- Service breakdown (all Bedrock)
- Time period (current month)

---

## Next Steps

1. **Ask AI to create detailed plan:**
   - Command: "Create a detailed implementation plan for ai-migration-canada-prompt.md"
   - AI will structure this into phases with specific tasks

2. **Review and approve plan:**
   - Review the structured plan
   - Clarify any remaining questions
   - Approve for implementation

3. **Implementation:**
   - Follow the plan step-by-step
   - Test each phase before moving to the next
   - Document any deviations or issues

4. **Validation:**
   - Comprehensive testing of all services
   - Security audit
   - Performance benchmarking
   - Cost monitoring setup
