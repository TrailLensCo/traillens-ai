# AWS Server Plan

**Created:** 2026-02-28
**Status:** Draft - Awaiting Review
**Project:** ai
**Target Environment:** AWS ca-central-1

---

## Executive Summary

Migrate the AI services platform from local containerized deployment (Podman) to AWS EC2 bare-metal deployment to reduce operational costs while maintaining service availability and functionality. The system will run LiteLLM, PostgreSQL 16, Redis 7, and OpenCode Server on a single EC2 instance with smart scheduled auto-shutdown during off-hours to optimize costs.

**Key Goals:**
- Reduce infrastructure costs by eliminating container overhead
- Maintain smart schedule availability (weekdays 7 AM - 10 PM, weekends 9 AM - 10 PM Eastern)
- Provide secure, authenticated access to LiteLLM from multiple clients
- Use Pulumi for infrastructure-as-code management
- Achieve <200ms response time for LiteLLM API calls

**Estimated Monthly Cost:** ~$22-24 USD (subject to AWS pricing verification)

---

## Task Overview

Deploy AI services (LiteLLM, PostgreSQL, Redis, OpenCode Server) on AWS EC2 using bare-metal installation instead of containers. Configure scheduled auto-shutdown to reduce costs, expose services via CloudFront + ACM at `https://ai.traillenshq.com`, and manage infrastructure through Pulumi.

**Why this is needed:**
- Current containerized local deployment works but requires always-on local machine
- Need to provide global access to LiteLLM for multiple AI clients (IDE, mobile, Continue.dev)
- Cost optimization: bare metal eliminates Podman/Docker overhead
- Smart schedule operation reduces costs by ~40% vs 24/7 (weekdays 15hr/day, weekends 13hr/day)

**Success Criteria:**
- All four services running successfully on EC2 bare metal
- Services accessible via `https://ai.traillenshq.com`
- Automatic shutdown/startup based on weekday/weekend schedules
- Total monthly cost <$50 USD (target: ~$22-24)
- Zero downtime during operational hours (weekdays 7 AM - 10 PM, weekends 9 AM - 10 PM)

---

## Context

### Current State

**Existing Setup:**
- Location: Local development machine
- Orchestration: Podman Compose ([ai/server/podman-compose.yaml](../../server/podman-compose.yaml))
- Services:
  - LiteLLM (port 8001→4000): OpenAI-compatible proxy for AWS Bedrock models
  - PostgreSQL 16 (internal): LiteLLM database backend
  - Redis 7-alpine (internal): LiteLLM caching layer
  - OpenCode Web UI (port 3001): IDE with built-in server
  - Nginx (port 8080): Reverse proxy
- Configuration:
  - Nginx: [ai/server/nginx/nginx.conf](../../server/nginx/nginx.conf)
  - LiteLLM: [ai/server/config/litellm-config.yaml](../../server/config/litellm-config.yaml)
  - OpenCode: [ai/server/config/opencode/opencode.json](../../server/config/opencode/opencode.json)

**Current Architecture:**
```
┌─────────────────────────────────────────────────┐
│ Localhost:8080 (Nginx)                          │
├─────────────────────────────────────────────────┤
│ ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│ │ LiteLLM  │  │ OpenCode │  │ PostgreSQL   │   │
│ │ :4000    │  │ :3001    │  │ :5432        │   │
│ └────┬─────┘  └──────────┘  └──────┬───────┘   │
│      │                              │           │
│      └──────────────┬───────────────┘           │
│                     │                           │
│              ┌──────┴──────┐                    │
│              │   Redis     │                    │
│              │   :6379     │                    │
│              └─────────────┘                    │
└─────────────────────────────────────────────────┘
```

### Target State

**New Architecture:**
```
┌───────────────────────────────────────────────────┐
│ CloudFront → https://ai.traillenshq.com (ACM)     │
└──────────────────────┬────────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────────┐
│ EC2 t3.medium (ca-central-1)                      │
│ Public Elastic IP                                 │
├───────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────┐ │
│ │ Nginx :8080 (systemd service)                 │ │
│ └─────────────────┬─────────────────────────────┘ │
│                   │                               │
│ ┌─────────────────┼─────────────────────────────┐ │
│ │ LiteLLM         │ OpenCode    PostgreSQL 16   │ │
│ │ :4000           │ :3001       :5432           │ │
│ │ (systemd)       │ (systemd)   (systemd)       │ │
│ └─────────┬───────┴─────────────┴───────────────┘ │
│           │                                       │
│    ┌──────┴──────┐                                │
│    │ Redis :6379 │                                │
│    │ (systemd)   │                                │
│    └─────────────┘                                │
│                                                   │
│ Storage: 30GB gp3 EBS volume                      │
│ Monitoring: CloudWatch Logs                       │
│ Access: AWS Systems Manager Session               │
└───────────────────────────────────────────────────┘
                   ▲
                   │
┌──────────────────┴────────────────────────────────┐
│ EventBridge Scheduler (Smart Schedule)            │
│ • Weekdays: 7 AM - 10 PM (Mon-Fri)                │
│ • Weekends: 9 AM - 10 PM (Sat-Sun)                │
└───────────────────────────────────────────────────┘
```

### Related Files

**Infrastructure (Pulumi):**
- **To be created:**
  - `ai/infra/__main__.py` - EC2 instance, security groups, Elastic IP
  - `ai/infra/user-data.sh` - Provisioning script
  - `ai/infra/eventbridge.py` - Auto-shutdown scheduler

**Existing Reference:**
- `infra/` - Main TrailLens infrastructure (VPC, subnets, Route53 hosted zone)
- `infra/CLAUDE.md` - Infrastructure deployment patterns

### Dependencies

**AWS Services:**
- EC2 (t3.medium instance)
- Elastic IP (static public IP)
- EBS (30GB gp3 volume)
- Route 53 (DNS for ai.traillenshq.com)
- ACM (TLS certificate for *.traillenshq.com or ai.traillenshq.com)
- CloudFront (HTTPS termination, CDN)
- CloudWatch Logs (service logging)
- EventBridge Scheduler (auto-shutdown/startup)
- Systems Manager (Session Manager for shell access)
- VPC, Subnets, Internet Gateway (from existing infra)

**Software Stack:**
- OS: **Ubuntu 24.04 LTS (Noble Numbat)**
- Python: 3.14 (for LiteLLM and admin scripts)
- PostgreSQL: 16.x
- Redis: 7.x
- Nginx: Latest stable (from Ubuntu apt)
- Node.js: 22.x (for OpenCode Server)
- AWS CLI: v2 (latest)
- AWS Python SDK: boto3, botocore (for ec2-control.py)
- Systemd: For service management

**External Dependencies:**
- AWS Bedrock models (via LiteLLM)
- Existing Pulumi stack outputs from `infra/` (VPC ID, subnet IDs, Route53 zone)

### Constraints

**Technical:**
- **No containers:** Bare-metal installation only (systemd services)
- **Single instance:** No auto-scaling, single point of failure acceptable
- **4GB RAM limit:** Must optimize service memory usage for t3.medium
- **Disk I/O:** Standard gp3 performance (3000 IOPS baseline)
- **Network:** Single Elastic IP, no load balancer
- **Region locked:** ca-central-1 (Canada Central) for ALL resources
  - **Exception:** ACM certificates MUST be in us-east-1 for CloudFront (AWS requirement)
  - All other resources (EC2, EBS, Elastic IP, Security Groups, EventBridge, CloudWatch, Route 53 records) in ca-central-1

**Operational:**
- **Scheduled downtime:** Services unavailable 10 PM - 7 AM weekdays, 10 PM - 9 AM weekends
- **No HA/DR:** Single instance, acceptable risk for development/testing workload
- **Manual scaling:** No auto-scaling, vertical scaling requires instance replacement

**Cost:**
- **Target:** <$50 USD/month total (achieving ~$22-24/month)
- **Smart schedule operation:** ~$18/month EC2 (vs ~$30 for 24/7) - 437 hours/month
- **Data transfer:** Must stay within CloudFront free tier (1TB/month)

**Security:**
- **API keys in environment variables:** Less secure than Secrets Manager but acceptable for this use case
- **Public access:** Services exposed to internet (protected by CloudFront + auth)
- **No VPN:** Direct public access via HTTPS

**Compliance:**
- Follow TrailLens Constitution (CLAUDE.md, CONSTITUTION-*.md)
- Python 3.14 required (infra/)
- No Makefiles - use Python scripts
- Pulumi for all infrastructure

---

## Requirements

### 1. EC2 Instance Configuration

**Instance Specification:**
- Type: `t3.medium` (2 vCPUs, 4 GB RAM)
- Region: `ca-central-1` (Canada Central)
- AMI: **Ubuntu 24.04 LTS (Noble Numbat)** - `ubuntu/images/hvm-ssd/ubuntu-noble-24.04-amd64-server-*`
  - Owner: Canonical (099720109477)
  - Reason: Best package availability for Python 3.14, PostgreSQL 16, Redis 7, Node.js 22
- EBS Volume: 30 GB gp3 (3000 IOPS baseline, 125 MB/s throughput)
- Elastic IP: Single public static IP address
- IAM Role: EC2 instance role with:
  - CloudWatch Logs write permissions
  - Systems Manager core permissions (SSM Session Manager)
  - Read-only access to Parameter Store (for configuration)
  - EC2 describe permissions (for ec2-control.py script)

**Acceptance Criteria:**
- [ ] EC2 instance launches successfully in ca-central-1
- [ ] Elastic IP attached and persistent across stop/start cycles
- [ ] User `mark` exists with home directory `/home/mark`
- [ ] User `mark` has full sudo access (in sudo group, passwordless configured)
- [ ] Systems Manager Session Manager access works (no SSH required)
- [ ] CloudWatch agent installed and streaming logs
- [ ] Instance tagged: `Environment=dev`, `Project=ai`, `ManagedBy=pulumi`

### 2. Service Installation (User Data Script)

**System Packages to Install:**
1. **System Updates & Base Tools**
   - Update package lists: `apt-get update && apt-get upgrade -y`
   - Install build essentials: `build-essential`, `curl`, `wget`, `git`, `unzip`
   - Install AWS CLI v2: Latest version from official AWS installer
   - Install CloudWatch Logs agent: `amazon-cloudwatch-agent`
   - Create user directory structure:
     ```bash
     # Create mark user with sudo access and src directory
     useradd -m -s /bin/bash mark
     usermod -aG sudo mark

     # Configure passwordless sudo for mark
     echo "mark ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/mark
     chmod 0440 /etc/sudoers.d/mark

     # Create src directory for code repositories
     mkdir -p /home/mark/src
     chown -R mark:mark /home/mark
     ```

2. **AWS Tools & Libraries**
   - **AWS CLI v2**: Command-line interface for AWS services
     - Install via: `curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && ./aws/install`
     - Used by: ec2-control.py script, manual operations
   - **AWS Python Libraries** (system-wide for admin scripts):
     - `boto3`: AWS SDK for Python (EC2, CloudWatch, Systems Manager)
     - `botocore`: Low-level AWS service access
     - Install via: `pip3 install boto3 botocore`

3. **PostgreSQL 16**
   - Repository: PostgreSQL APT repository (apt.postgresql.org)
   - Database name: `litellm`
   - User: `llmproxy`
   - Password: Stored in environment variable `POSTGRES_PASSWORD`
   - Data directory: `/var/lib/postgresql/16/main`
   - Systemd service: `postgresql`
   - Install:
     ```bash
     sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
     wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
     apt-get update && apt-get install -y postgresql-16
     ```

4. **Redis 7**
   - Port: 6379 (localhost only)
   - Persistence: AOF enabled
   - Data directory: `/var/lib/redis`
   - Systemd service: `redis-server`
   - Install: `apt-get install -y redis-server`

5. **Python 3.14**
   - Repository: deadsnakes PPA (ppa:deadsnakes/ppa)
   - Packages: `python3.14`, `python3.14-venv`, `python3.14-dev`, `python3-pip`
   - Install:
     ```bash
     add-apt-repository -y ppa:deadsnakes/ppa
     apt-get update
     apt-get install -y python3.14 python3.14-venv python3.14-dev python3-pip
     ```

6. **LiteLLM**
   - Port: 4000 (localhost only)
   - Config: `/etc/litellm/config.yaml` (copied from existing)
   - Python venv: `/opt/litellm/venv` (Python 3.14)
   - Systemd service: `litellm`
   - Environment variables:
     - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
     - `LITELLM_MASTER_KEY`, `LITELLM_SALT_KEY`
     - `DATABASE_URL`, `REDIS_HOST`, `REDIS_PORT`
   - Install:
     ```bash
     python3.14 -m venv /opt/litellm/venv
     /opt/litellm/venv/bin/pip install litellm
     ```

7. **Node.js 22**
   - Repository: NodeSource (deb.nodesource.com)
   - Used by: OpenCode Server
   - Install:
     ```bash
     curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
     apt-get install -y nodejs
     ```

8. **OpenCode Server**
   - Port: 3001 (localhost only)
   - Working directory: `/home/mark/src` (where code repositories will be located)
   - Install directory: `/opt/opencode` (binary/installation)
   - Config: `/home/mark/.config/opencode/opencode.json`
   - User: `mark` (runs as mark user, not root)
   - Systemd service: `opencode` (runs as User=mark)
   - Environment variables:
     - `OPENCODE_SERVER_PASSWORD`
     - `LITELLM_MASTER_KEY`
     - `HOME=/home/mark`
   - Directory structure:
     ```bash
     /home/mark/
     ├── src/                           # Working directory for code
     └── .config/opencode/
         └── opencode.json              # Configuration file
     ```

9. **Nginx**
   - Port: 8080 (public)
   - Config: `/etc/nginx/nginx.conf` (based on existing)
   - Upstream services: LiteLLM (localhost:4000), OpenCode (localhost:3001)
   - Systemd service: `nginx`
   - Install: `apt-get install -y nginx`

10. **System Configuration**
    - **Swap File**: 2GB swap file (`/swapfile`)
      - Prevents OOM (Out of Memory) issues when services exceed 4GB physical RAM
      - Created via: `dd if=/dev/zero of=/swapfile bs=1M count=2048`
      - Permissions: `chmod 600 /swapfile`
      - Enable: `mkswap /swapfile && swapon /swapfile`
      - Persist: Add to `/etc/fstab`: `/swapfile none swap sw 0 0`

**Acceptance Criteria:**
- [ ] Ubuntu 24.04 LTS AMI selected and instance launches successfully
- [ ] git installed: `git --version` shows 2.x
- [ ] User `mark` created with home directory `/home/mark`
- [ ] User `mark` has full sudo access: `sudo -l -U mark` shows NOPASSWD:ALL
- [ ] Directory `/home/mark/src` exists and is owned by mark:mark
- [ ] AWS CLI v2 installed and working: `aws --version` shows v2.x
- [ ] boto3 installed: `python3 -c "import boto3; print(boto3.__version__)"` succeeds
- [ ] Python 3.14 installed: `python3.14 --version` shows 3.14.x
- [ ] PostgreSQL 16 installed: `psql --version` shows 16.x
- [ ] Redis 7 installed: `redis-server --version` shows 7.x
- [ ] Node.js 22 installed: `node --version` shows v22.x
- [ ] All services start automatically on boot
- [ ] All services restart automatically on failure (systemd restart policies)
- [ ] Health checks pass: PostgreSQL `pg_isready`, Redis `redis-cli ping`, LiteLLM `/health/liveliness`, OpenCode `nc -z localhost 3001`
- [ ] OpenCode running as `mark` user: `ps aux | grep opencode` shows User=mark
- [ ] OpenCode working directory is `/home/mark/src`: accessible from OpenCode UI
- [ ] Nginx proxies requests correctly: `/` → OpenCode, `/litellm` → LiteLLM
- [ ] Configuration files match existing Podman setup functionality
- [ ] Services use <3.5 GB RAM total (leaving 500MB for OS)
- [ ] 2GB swap file active and persistent across reboots (`swapon --show` shows 2GB)
- [ ] CloudWatch agent streaming logs to CloudWatch Logs

### 3. Network & Security

**Security Group:**
- Inbound:
  - TCP 8080 from CloudFront IP ranges (or 0.0.0.0/0 if using custom domain on CloudFront)
  - TCP 443 from CloudFront IP ranges (if ALB used instead)
- Outbound:
  - All traffic (0.0.0.0/0) for AWS API calls, package updates
- No SSH port 22 (use Systems Manager instead)

**DNS Configuration (Route 53):**
- Record: `ai.traillenshq.com` (A record or CNAME)
- Value: CloudFront distribution domain name (e.g., `d111111abcdef8.cloudfront.net`)
- TTL: 300 seconds
- Hosted Zone: Use existing `traillenshq.com` zone from `infra/`

**CloudFront Distribution:**
- Origin: EC2 Elastic IP on port 8080
- Alternate domain names (CNAMEs): `ai.traillenshq.com`
- TLS certificate: ACM certificate for `ai.traillenshq.com` or wildcard `*.traillenshq.com`
- Viewer protocol policy: Redirect HTTP to HTTPS
- Allowed HTTP methods: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
- Cache behavior: No caching (or short TTL) for API responses
- Origin protocol policy: HTTP only (HTTPS termination at CloudFront)

**ACM Certificate:**
- Domain: `ai.traillenshq.com` (or wildcard `*.traillenshq.com` for future subdomains)
- **Status**: No existing certificate found - MUST CREATE NEW
  - Existing: `auth.traillenshq.com` (us-east-1), `api.traillenshq.com` (ca-central-1) don't cover ai.traillenshq.com
- Validation: DNS validation via Route 53
- Region: `us-east-1` (REQUIRED for CloudFront - only exception to ca-central-1 rule)
  - Note: CloudFront is a global service and requires ACM certificates in us-east-1 only

**Acceptance Criteria:**
- [ ] Security group allows inbound 8080 from appropriate sources
- [ ] Security group blocks all other inbound traffic
- [ ] Systems Manager Session Manager works (no SSH key required)
- [ ] Route 53 record `ai.traillenshq.com` resolves to CloudFront
- [ ] CloudFront serves content from EC2 origin
- [ ] HTTPS works with valid ACM certificate
- [ ] HTTP redirects to HTTPS automatically

### 4. Auto-Shutdown Scheduler

**EventBridge Schedules (Smart Schedule):**

**Weekday Schedule (Monday-Friday):**
- Start: `0 12 * * 1-5` (7:00 AM Eastern = 12:00 PM UTC, Mon-Fri)
- Stop: `0 3 * * 2-6` (10:00 PM Eastern = 3:00 AM UTC next day, Tue-Sat)
- Runtime: 15 hours/day

**Weekend Schedule (Saturday-Sunday):**
- Start: `0 14 * * 0,6` (9:00 AM Eastern = 2:00 PM UTC, Sat-Sun)
- Stop: `0 3 * * 0,1` (10:00 PM Eastern = 3:00 AM UTC next day, Sun-Mon)
- Runtime: 13 hours/day

**Schedule Summary:**
- Weekdays: 7 AM - 10 PM (15 hours/day × 5 days = 75 hours/week)
- Weekends: 9 AM - 10 PM (13 hours/day × 2 days = 26 hours/week)
- **Total: ~437 hours/month** (vs 720 hours for 24/7)

**Actions:**
- Start: `ec2:StartInstances`
- Stop: `ec2:StopInstances`
- Timezone: UTC (cron expressions adjusted for Eastern Time)
- Target: EC2 instance ID (from Pulumi output)

**IAM Role for EventBridge:**
- Permissions:
  - `ec2:StopInstances` for the specific instance
  - `ec2:StartInstances` for the specific instance

**Acceptance Criteria:**
- [ ] Instance starts at 7 AM Eastern on weekdays (Mon-Fri)
- [ ] Instance starts at 9 AM Eastern on weekends (Sat-Sun)
- [ ] Instance stops at 10 PM Eastern every day
- [ ] Services start automatically after instance start (systemd enabled)
- [ ] EventBridge Scheduler shows successful invocations in CloudWatch Logs
- [ ] Manual start/stop still works via AWS Console or CLI
- [ ] Schedule verified across multiple weeks (handles day transitions correctly)

### 5. Monitoring & Logging

**CloudWatch Logs Configuration:**

**Installation:**
```bash
# Install CloudWatch Logs agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i amazon-cloudwatch-agent.deb
```

**Agent Configuration File:** `/opt/aws/amazon-cloudwatch-agent/etc/config.json`

```json
{
  "agent": {
    "region": "ca-central-1",
    "metrics_collection_interval": 60,
    "run_as_user": "cwagent"
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/litellm/litellm.log",
            "log_group_name": "/ai/litellm",
            "log_stream_name": "{instance_id}",
            "retention_in_days": 7,
            "timezone": "Local"
          },
          {
            "file_path": "/var/log/litellm/error.log",
            "log_group_name": "/ai/litellm",
            "log_stream_name": "{instance_id}-error",
            "retention_in_days": 7,
            "timezone": "Local"
          },
          {
            "file_path": "/var/log/opencode/opencode.log",
            "log_group_name": "/ai/opencode",
            "log_stream_name": "{instance_id}",
            "retention_in_days": 7,
            "timezone": "Local"
          },
          {
            "file_path": "/var/log/opencode/error.log",
            "log_group_name": "/ai/opencode",
            "log_stream_name": "{instance_id}-error",
            "retention_in_days": 7,
            "timezone": "Local"
          },
          {
            "file_path": "/var/log/nginx/access.log",
            "log_group_name": "/ai/nginx",
            "log_stream_name": "{instance_id}-access",
            "retention_in_days": 7,
            "timezone": "Local"
          },
          {
            "file_path": "/var/log/nginx/error.log",
            "log_group_name": "/ai/nginx",
            "log_stream_name": "{instance_id}-error",
            "retention_in_days": 7,
            "timezone": "Local"
          },
          {
            "file_path": "/var/log/syslog",
            "log_group_name": "/ai/system",
            "log_stream_name": "{instance_id}-syslog",
            "retention_in_days": 7,
            "timezone": "Local"
          },
          {
            "file_path": "/var/log/cloud-init-output.log",
            "log_group_name": "/ai/system",
            "log_stream_name": "{instance_id}-cloud-init",
            "retention_in_days": 7,
            "timezone": "Local"
          }
        ]
      }
    }
  },
  "metrics": {
    "namespace": "AI/EC2",
    "metrics_collected": {
      "disk": {
        "measurement": [
          {
            "name": "used_percent",
            "rename": "DiskUsedPercent",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "/"
        ]
      },
      "mem": {
        "measurement": [
          {
            "name": "mem_used_percent",
            "rename": "MemoryUsedPercent",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60
      }
    }
  }
}
```

**Service Logging Setup:**

Each systemd service redirects logs to specific files:

**LiteLLM Service** (`/etc/systemd/system/litellm.service`):
```ini
[Service]
StandardOutput=append:/var/log/litellm/litellm.log
StandardError=append:/var/log/litellm/error.log
```

**OpenCode Service** (`/etc/systemd/system/opencode.service`):
```ini
[Service]
StandardOutput=append:/var/log/opencode/opencode.log
StandardError=append:/var/log/opencode/error.log
```

**PostgreSQL:** Uses default logging to `/var/log/postgresql/postgresql-16-main.log` (optional CloudWatch integration)

**Redis:** Uses syslog, captured by `/var/log/syslog`

**Nginx:** Default logs to `/var/log/nginx/access.log` and `/var/log/nginx/error.log`

**Log Directory Creation:**
```bash
# Create log directories with proper permissions
mkdir -p /var/log/litellm /var/log/opencode
chown -R root:adm /var/log/litellm /var/log/opencode
chmod 755 /var/log/litellm /var/log/opencode
```

**Start CloudWatch Agent:**
```bash
# Start agent with configuration
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json

# Enable on boot
systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent
```

**IAM Role Permissions Required:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:ca-central-1:*:log-group:/ai/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    }
  ]
}
```

**Log Groups Created:**
- `/ai/litellm` - LiteLLM application logs (stdout + stderr)
- `/ai/opencode` - OpenCode server logs (stdout + stderr)
- `/ai/nginx` - Nginx access and error logs
- `/ai/system` - System messages, syslog, cloud-init output

**CloudWatch Metrics:**
- Custom namespace: `AI/EC2`
- Metrics: DiskUsedPercent, MemoryUsedPercent
- Collection interval: 60 seconds
- No additional cost (basic metrics free)

**CloudWatch Alarms:**
- No custom alarms required (cost optimization)
- Use basic EC2 metrics: CPU, Network, Status Checks via AWS Console

**Viewing Logs:**
```bash
# Via AWS CLI
aws logs tail /ai/litellm --follow --region ca-central-1
aws logs tail /ai/opencode --follow --region ca-central-1
aws logs tail /ai/nginx --follow --region ca-central-1
aws logs tail /ai/system --follow --region ca-central-1

# Via ec2-control.py script
python3 ec2-control.py logs litellm
python3 ec2-control.py logs opencode
python3 ec2-control.py logs nginx
python3 ec2-control.py logs system
```

**Acceptance Criteria:**
- [ ] CloudWatch agent installed: `systemctl status amazon-cloudwatch-agent` shows active
- [ ] Configuration file exists: `/opt/aws/amazon-cloudwatch-agent/etc/config.json`
- [ ] All log directories exist: `/var/log/litellm`, `/var/log/opencode`
- [ ] All service logs streaming to CloudWatch Logs
- [ ] Log groups created in ca-central-1: `/ai/litellm`, `/ai/opencode`, `/ai/nginx`, `/ai/system`
- [ ] Logs readable and searchable in CloudWatch console
- [ ] Log retention set to 7 days for all log groups
- [ ] Custom metrics visible in CloudWatch: `AI/EC2` namespace shows DiskUsedPercent, MemoryUsedPercent
- [ ] No excessive log volume (stay within free tier <5GB/month if possible)
- [ ] IAM role has correct CloudWatch permissions

### 6. Infrastructure as Code (Pulumi)

**Pulumi Stack:**
- Stack name: `ai-dev` (separate from main `infra/` stack)
- Language: Python 3.14
- Project structure:
  ```
  ai/infra/
  ├── __main__.py         # Main Pulumi program
  ├── Pulumi.yaml         # Project config
  ├── Pulumi.ai-dev.yaml  # Stack config (secrets encrypted)
  ├── requirements.txt    # pulumi, pulumi-aws, etc.
  ├── user-data.sh        # EC2 user data script
  └── config/             # Service config files to upload
      ├── litellm-config.yaml
      ├── opencode.json
      └── nginx.conf
  ```

**Stack References:**
- Reference existing `infra/` stack outputs:
  - VPC ID
  - Public subnet IDs
  - Route 53 hosted zone ID
  - Existing security groups (if applicable)

**Secrets Management:**
- Use `pulumi config set --secret` for:
  - `LITELLM_MASTER_KEY`
  - `LITELLM_SALT_KEY`
  - `OPENCODE_SERVER_PASSWORD`
  - `POSTGRES_PASSWORD`
  - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (for LiteLLM to call Bedrock)

**Acceptance Criteria:**
- [ ] `pulumi up` successfully deploys all resources
- [ ] `pulumi destroy` successfully removes all resources (except persistent data)
- [ ] Stack outputs include: Elastic IP, CloudFront URL, EC2 instance ID
- [ ] Secrets stored encrypted in Pulumi config
- [ ] User data script successfully provisions all services
- [ ] Code follows Python CONSTITUTION (type hints, imports, .venv)

### 7. Cost Analysis & Optimization

**Cost Breakdown (Estimated Monthly, ca-central-1):**

*Note: Exact pricing must be verified using [AWS Pricing Calculator](https://calculator.aws/) for ca-central-1 region.*

| Service | Configuration | 24/7 Cost | Smart Schedule | Notes |
|---------|--------------|-----------|----------------|-------|
| EC2 t3.medium | 2 vCPU, 4GB RAM | ~$30/mo | ~$18/mo | ~$0.0416/hr × 437hrs/mo (us-east-1 pricing, ca-central-1 varies) |
| EBS gp3 30GB | 3000 IOPS | ~$2.40/mo | ~$2.40/mo | $0.08/GB-mo |
| Elastic IP | While running | $0 | $0 | Free when attached to running instance |
| Elastic IP | While stopped | ~$3.60/mo | ~$1.40/mo | $0.005/hr when not attached (~283hr/mo stopped) |
| CloudFront | <1TB/mo | $0 | $0 | Free tier: 1TB data transfer out |
| CloudWatch Logs | <5GB/mo | $0-$2 | $0-$2 | $0.50/GB ingestion, some free tier |
| EventBridge Scheduler | 4 schedules | $0 | $0 | Free tier: 14M invocations/mo |
| ACM Certificate | 1 certificate | $0 | $0 | Free for public certificates |
| Route 53 | 1 hosted zone + queries | ~$0.50/mo | ~$0.50/mo | Existing zone, minimal query cost |
| **TOTAL** | | **~$36-38/mo** | **~$22-24/mo** | **Savings: ~$14/mo (38%)** |

**Smart Schedule Runtime:**
- Weekdays (Mon-Fri): 15 hours/day × 5 days = 75 hours/week
- Weekends (Sat-Sun): 13 hours/day × 2 days = 26 hours/week
- **Total: 437 hours/month** (vs 720 hours for 24/7)
- **Cost reduction: 39% vs 24/7 operation**

**Cost Verification Required:**
- [ ] Use [AWS Pricing Calculator](https://calculator.aws/) to confirm ca-central-1 pricing
- [ ] Document actual pricing URLs in final plan
- [ ] Consider t3a.medium ($27/mo vs $30/mo) if AMD instances acceptable
- [ ] Monitor first month usage to validate estimates

**Cost Optimization Notes:**
- Smart schedule operation reduces EC2 cost by ~40% vs 24/7
- Elastic IP cost when stopped: ~$1.40/mo (283 hours/month stopped)
- CloudFront free tier covers expected <1TB/month traffic
- No load balancer (~$16/mo saved)
- No NAT Gateway (using Internet Gateway, saves ~$32/mo)
- No RDS (bare-metal PostgreSQL saves ~$15/mo vs db.t3.micro)
- 2GB swap file prevents OOM without upgrading instance size

**Acceptance Criteria:**
- [ ] Actual costs verified using AWS Pricing Calculator for ca-central-1
- [ ] Total monthly cost <$50 USD
- [ ] Cost savings vs 24/7 operation documented
- [ ] Cost monitoring set up (AWS Budgets or Cost Explorer alert)

### 8. Documentation & Handoff

**Documentation to Create:**
- `ai/infra/README.md` - Deployment instructions, cost breakdown, troubleshooting
- `ai/infra/RUNBOOK.md` - Operational procedures (manual start/stop, log access, service restart)
- `ai/scripts/ec2-control.py` - Python script to start/stop EC2 instance locally
  - Commands: `start`, `stop`, `status`, `session` (via Systems Manager)
  - Uses boto3 to interact with EC2 instance
  - Reads instance ID from Pulumi stack outputs or config file
  - Requirements: Python 3.14, boto3, AWS credentials configured
- Update `ai/CLAUDE.md` - Add AWS deployment context
- Update root `CLAUDE.md` - Reference new ai submodule infrastructure

**EC2 Control Script Requirements:**
- Python 3.14 (matches infrastructure code)
- Functions:
  - `start` - Start the EC2 instance, wait for running state, show public IP
  - `stop` - Stop the EC2 instance gracefully
  - `status` - Show current instance state (running/stopped/stopping/starting)
  - `session` - Open Systems Manager Session Manager connection (no SSH keys needed)
  - `logs` - Tail CloudWatch Logs for services
- Configuration:
  - Read instance ID from `ai/infra/Pulumi.<stack>.yaml` outputs or `.env` file
  - AWS region: ca-central-1
  - Uses AWS credentials from `~/.aws/credentials` or environment variables
- Error handling:
  - Check AWS credentials before attempting operations
  - Handle instance not found, permission denied, etc.
  - Show clear error messages with suggestions

**Acceptance Criteria:**
- [ ] README includes deployment commands, prerequisites, cost analysis
- [ ] RUNBOOK includes common troubleshooting steps (service failures, disk full, OOM)
- [ ] CLAUDE.md updated with AWS-specific context
- [ ] All configuration files commented and explained
- [ ] `ai/scripts/ec2-control.py` script works for start/stop/status/session operations
- [ ] Script follows Python CONSTITUTION (type hints, .venv, requirements.txt)

---

## Expected Behavior

### After Successful Deployment

**Infrastructure:**
- [ ] EC2 instance running in ca-central-1 with Elastic IP attached
- [ ] Route 53 record `ai.traillenshq.com` resolves to CloudFront distribution
- [ ] CloudFront distribution serves HTTPS traffic with valid ACM certificate
- [ ] Systems Manager Session Manager provides shell access to EC2 instance
- [ ] EventBridge schedules configured for daily stop/start

**Services:**
- [ ] All services running as systemd units: `systemctl status litellm opencode postgresql redis nginx`
- [ ] LiteLLM accessible at `https://ai.traillenshq.com/litellm/v1/models` (with API key)
- [ ] OpenCode Web UI accessible at `https://ai.traillenshq.com/` (with password)
- [ ] Services automatically start after EC2 instance start
- [ ] Services restart automatically on failure

**Operational:**
- [ ] Instance stops at 10:00 PM Eastern every day, services gracefully shut down
- [ ] Instance starts at 7:00 AM Eastern on weekdays (Mon-Fri)
- [ ] Instance starts at 9:00 AM Eastern on weekends (Sat-Sun)
- [ ] Services automatically start after instance boot (systemd enabled)
- [ ] CloudWatch Logs show service logs, searchable and up-to-date
- [ ] No errors or warnings in service logs during normal operation
- [ ] API response times <200ms for LiteLLM (excluding model inference time)
- [ ] 2GB swap file active (`swapon --show` shows 2GB)

**Cost:**
- [ ] Actual monthly cost visible in AWS Cost Explorer
- [ ] Cost aligns with estimates (~$22-24/month for smart schedule operation)
- [ ] No unexpected charges (data transfer, CloudWatch overage, etc.)
- [ ] Average ~437 hours/month runtime (weekdays 15hr/day, weekends 13hr/day)

**Access & Security:**
- [ ] LiteLLM API key authentication works (requests without key rejected)
- [ ] OpenCode password authentication works
- [ ] HTTPS enforced (HTTP requests redirect to HTTPS)
- [ ] No unauthorized access attempts succeed (security group blocks)

**Verification Steps:**
1. **DNS:** `dig ai.traillenshq.com` → returns CloudFront domain
2. **HTTPS:** `curl https://ai.traillenshq.com/health` → returns 200 OK
3. **LiteLLM:** `curl https://ai.traillenshq.com/litellm/v1/models -H "Authorization: Bearer $LITELLM_MASTER_KEY"` → returns model list
4. **OpenCode:** Visit `https://ai.traillenshq.com/` in browser → login page loads
5. **Logs:** Check CloudWatch Logs groups `/ai/*` → see recent log entries
6. **Scheduler:** Check EventBridge Scheduler history → see successful invocations
7. **Session Manager:** Connect via AWS Console → get shell access
8. **Cost:** Check Cost Explorer → see daily costs ~$0.90-1.00

---

## Additional Notes

### Security Considerations

**Authentication:**
- LiteLLM: API key in `Authorization: Bearer $LITELLM_MASTER_KEY` header
- OpenCode: Password-based authentication (`OPENCODE_SERVER_PASSWORD`)
- CloudFront: No additional auth (relies on app-level auth)
- Systems Manager: IAM-based access control

**Secrets Handling:**
- API keys stored in environment variables (not Secrets Manager)
- User data script contains secrets (base64-encoded in EC2 metadata)
- Risk: Secrets readable from instance metadata or environment
- Mitigation: Restrict Systems Manager access, rotate keys periodically

**Network Security:**
- No public SSH (port 22 blocked)
- All traffic through CloudFront (HTTPS only)
- Services bound to localhost only (Nginx proxies)
- Security group restricts inbound to port 8080 from CloudFront

**Data Protection:**
- PostgreSQL data on EBS volume (encrypted at rest if enabled)
- Daily EBS snapshots for backup
- No automatic encryption of logs (CloudWatch Logs default)

**Recommendations for Production:**
- Migrate secrets to AWS Secrets Manager or Parameter Store (SecureString)
- Enable EBS encryption at rest
- Use CloudFront signed URLs or AWS WAF for additional access control
- Implement rate limiting in Nginx or CloudFront
- Enable VPC Flow Logs for network monitoring

### Performance Considerations

**Memory Usage (4GB total):**
- PostgreSQL: ~512 MB (shared_buffers=128MB + connections)
- Redis: ~256 MB (max memory limit)
- LiteLLM (Python): ~1 GB (estimated, depends on concurrency)
- OpenCode Server (Node.js): ~1 GB (estimated)
- Nginx: ~50 MB
- OS + overhead: ~500 MB
- **Total: ~3.3 GB** (leaving ~700 MB headroom)

**Optimization if OOM occurs:**
- Reduce PostgreSQL `shared_buffers` to 64MB
- Set Redis `maxmemory 128mb` with `maxmemory-policy allkeys-lru`
- Limit LiteLLM worker threads
- Enable swap on EBS (2GB swap file)

**Disk I/O:**
- gp3 baseline: 3000 IOPS, 125 MB/s
- Expected load: Low (development workload, <10 concurrent users)
- PostgreSQL + Redis mostly in-memory for active data
- Risk: Low, should be sufficient

**Network:**
- t3.medium: Up to 5 Gbps burst
- Expected load: <100 Mbps (mostly API calls, minimal data transfer)
- CloudFront caching: Disabled or short TTL (API responses not cacheable)
- Risk: Low, sufficient bandwidth

### Edge Cases to Handle

**Instance Stopped During Active Use:**
- User receives 502/503 from CloudFront
- Error message: "Service temporarily unavailable, returns at 7 AM Eastern"
- Solution: Display maintenance page in CloudFront error response

**Service Failure:**
- Systemd restart policy: `Restart=always`, `RestartSec=10`
- Max 5 restart attempts per 5 minutes before giving up
- Monitoring: CloudWatch Logs show restart attempts
- Alerting: None configured (cost optimization), manual monitoring required

**Disk Full:**
- PostgreSQL stops accepting writes
- LiteLLM may crash
- Solution: CloudWatch alarm on disk usage >80% (optional, not required)
- Mitigation: Log retention 7 days, periodic cleanup

**OOM (Out of Memory):**
- Kernel OOM killer terminates process (likely LiteLLM or OpenCode)
- Systemd restarts service
- Solution: Enable swap (2GB) or reduce service memory limits

**API Key Rotation:**
- Update `LITELLM_MASTER_KEY` in Pulumi config
- Run `pulumi up` to update environment variables
- Restart LiteLLM service: `systemctl restart litellm`
- Update clients with new key

**Elastic IP Disassociation:**
- Instance stop/start may disassociate Elastic IP (should not happen)
- Route 53 → CloudFront → EC2 IP chain breaks
- Solution: Pulumi ensures Elastic IP association on every update
- Verification: Check EC2 console after start

### Migration/Deployment Strategy

**Phase 1: Infrastructure Setup (No Services Yet)**
1. Deploy Pulumi stack (`pulumi up`)
2. Verify EC2 instance launches, Elastic IP attached
3. Test Systems Manager Session Manager access
4. Verify CloudWatch Logs agent installed

**Phase 2: Service Installation (User Data)**
1. User data script installs all services
2. Wait for instance to complete user data execution (~10-15 minutes)
3. Check `/var/log/cloud-init-output.log` for errors
4. Verify all services running: `systemctl status litellm opencode postgresql redis nginx`

**Phase 3: DNS & CloudFront Configuration**
1. Create ACM certificate (if not exists), validate via Route 53
2. Create CloudFront distribution pointing to EC2 Elastic IP:8080
3. Create Route 53 A record `ai.traillenshq.com` → CloudFront
4. Wait for DNS propagation (~5-10 minutes)
5. Test HTTPS access: `curl https://ai.traillenshq.com/health`

**Phase 4: Service Configuration**
1. Copy configuration files to EC2:
   - `/etc/litellm/config.yaml`
   - `/etc/opencode/opencode.json`
   - `/etc/nginx/nginx.conf`
2. Restart services: `systemctl restart litellm opencode nginx`
3. Test service functionality:
   - LiteLLM: List models API call
   - OpenCode: Login and create test file
   - PostgreSQL: Verify LiteLLM database tables created

**Phase 5: Scheduler Configuration**
1. Create EventBridge schedules:
   - Weekday start: 7 AM (Mon-Fri)
   - Weekend start: 9 AM (Sat-Sun)
   - Daily stop: 10 PM (every day)
2. Test manual stop: `aws ec2 stop-instances --instance-ids $INSTANCE_ID`
3. Test manual start: `aws ec2 start-instances --instance-ids $INSTANCE_ID`
4. Verify services auto-start after instance start
5. Monitor schedules across a full week to verify day transitions

**Phase 6: Monitoring & Validation**
1. Check CloudWatch Logs for all services
2. Run load test: 10 concurrent LiteLLM API calls
3. Monitor memory usage: `free -h`, CPU usage: `top`
4. Verify cost appears in AWS Cost Explorer
5. Document actual costs vs estimates

**Rollback Plan:**
- Keep Podman setup running during migration
- If AWS deployment fails: continue using Podman
- If AWS costs exceed budget: destroy Pulumi stack (`pulumi destroy`)
- Data loss risk: Low (development workload, no critical production data)

### Constitution Compliance Notes

**CONSTITUTION-PYTHON.md:**
- All Python code (Pulumi, scripts) uses Python 3.14
- Virtual environment: `ai/infra/.venv` (gitignored)
- Dependencies in `ai/infra/requirements.txt` before pip install
- Type hints on all function signatures
- Imports: stdlib → third-party → local, separated by blank lines
- Black formatting, isort for imports, flake8 linting
- No bare `except:`, use specific exceptions

**CONSTITUTION-SHELL.md:**
- User data script: `#!/bin/bash` shebang
- Safety: `set -euo pipefail`
- Quote all variables: `"$VAR"`
- Error messages to STDERR: `echo "Error" >&2`
- If script >100 lines: consider rewriting in Python (current estimate: ~150 lines)
- **Decision:** May need to convert user data to Python script if shell version exceeds 100 lines

**CLAUDE.md (Root):**
- No AI advertising (no "Generated with Claude" footers)
- No Makefiles (use Python scripts for automation)
- Infrastructure in `ai/infra/`, not in application code
- AI instructions in `.github/` only
- Copyright headers on all source files

**CLAUDE.md (Project):**
- Deploy to dev first, then prod (N/A - single environment for ai project)
- Use internal tools (Read, Edit, Write, Grep, Glob) in development
- No hardcoded secrets in code (use Pulumi config --secret)

### Open Questions

**Resolved (via user answers):**
- ✅ Instance type: t3.medium (4GB RAM)
- ✅ Region: ca-central-1
- ✅ Operating hours: Smart schedule (weekdays 7 AM - 10 PM, weekends 9 AM - 10 PM)
- ✅ Provisioning: User data script
- ✅ SSL: ACM + CloudFront
- ✅ Secrets: Environment variables only
- ✅ Monitoring: CloudWatch Logs for service logs
- ✅ Backups: None (removed to reduce costs)
- ✅ Swap: 2GB swap file (prevents OOM)
- ✅ OS: Ubuntu 24.04 LTS (better package availability for Python 3.14, PostgreSQL 16, Node.js 22)

**Still open (to be determined during implementation):**

1. **OpenCode Server installation method:**
   - Option A: npm global install
   - Option B: Build from source
   - Option C: Pre-built binary
   - Decision: Research during implementation, prefer simplest method

3. **User data vs configuration management:**
   - Current: User data script (simple, one-time)
   - Alternative: Ansible playbook (idempotent, easier to update)
   - Decision: Start with user data, migrate to Ansible if updates needed frequently

4. **ACM certificate:** New dedicated cert vs reuse wildcard `*.traillenshq.com`?
   - Decision: Check if wildcard exists in `infra/`, reuse if available
   - If not: Create dedicated `ai.traillenshq.com` cert (simpler, scoped)

5. **Cost alerting:** AWS Budgets alert at $40/month?
   - Current: No alerting (cost optimization)
   - Decision: User preference - implement if desired

6. **Swap file:** Enable 2GB swap for OOM protection?
   - Current: No swap (risk: OOM kills services)
   - Recommendation: Enable 2GB swap in user data script

7. **Service user:** Run services as `litellm`, `opencode` users or single `aiuser`?
   - Security best practice: Separate users per service
   - Simplicity: Single `aiuser` for all services
   - Decision: TBD during implementation, lean toward separate users

---

## Instructions for AI Assistant

**IMPORTANT - DO NOT IMPLEMENT YET:**

This is a **PLAN FILE** only. Do NOT proceed with implementation until:
1. User reviews and approves this plan
2. Open questions are resolved
3. Cost estimates are verified using AWS Pricing Calculator
4. User explicitly authorizes proceeding to implementation

**Next Steps (After Approval):**

1. **Verify AWS Pricing:**
   - Use [AWS Pricing Calculator](https://calculator.aws/) to confirm ca-central-1 costs
   - Document actual pricing URLs in this plan
   - Update cost table with verified prices
   - Confirm total monthly cost <$50 USD target

2. **Resolve Open Questions:**
   - Decide OS: Amazon Linux 2023 vs Ubuntu 24.04 LTS
   - Research OpenCode Server installation method
   - Check for existing wildcard ACM certificate in `infra/`
   - Get user input on swap file, service users, cost alerting

3. **Convert Plan to TODO List:**
   - Use `/mktodo ai` command to generate `ai/.github/todo/AWS-SERVER-TODO.md`
   - TODO list should follow todo-template.md structure
   - Break work into phases: Infrastructure Setup → Service Installation → DNS/CloudFront → Scheduler → Testing → Documentation

4. **Implementation (After TODO Approval):**
   - Follow TODO list phases in order
   - Run Constitution linter after each file change
   - Test each phase before proceeding to next
   - Update TODO checkboxes as tasks complete
   - Commit after each logical phase

**Constitution Compliance Checklist:**
- [ ] Python 3.14 for all Pulumi code (ai/infra/)
- [ ] Virtual environment: `ai/infra/.venv` (gitignored)
- [ ] Type hints on all function signatures
- [ ] Black formatting, isort imports, flake8 linting
- [ ] User data script: bash with `set -euo pipefail` (or convert to Python if >100 lines)
- [ ] No Makefiles, use Python scripts for automation
- [ ] Copyright headers on all new source files
- [ ] No AI advertising in code or commits
- [ ] Secrets stored in Pulumi config (encrypted)
- [ ] Use internal tools (Read, Edit, Write, Grep, Glob) in development workflow

**References:**
- [AWS Pricing Calculator](https://calculator.aws/)
- [EC2 On-Demand Instance Pricing](https://aws.amazon.com/ec2/pricing/on-demand/)
- [CloudFront Pricing](https://aws.amazon.com/cloudfront/pricing/)
- [EBS Pricing](https://aws.amazon.com/ebs/pricing/)
- [EventBridge Scheduler Pricing](https://aws.amazon.com/eventbridge/pricing/)
- Existing infrastructure: [infra/CLAUDE.md](../../../infra/CLAUDE.md)
- Existing services: [ai/server/podman-compose.yaml](../../server/podman-compose.yaml)

---

**Sources for Cost Research:**
- [t3.medium pricing - AWS EC2](https://www.economize.cloud/resources/aws/pricing/ec2/t3.medium/)
- [t3.medium pricing and specs - Vantage](https://instances.vantage.sh/aws/ec2/t3.medium)
- [Amazon CloudFront Pricing 2026](https://go-cloud.io/amazon-cloudfront-pricing/)
- [CloudFront Pricing Explained - nOps](https://www.nops.io/blog/cloudfront-pricing/)
- [EBS Pricing](https://aws.amazon.com/ebs/pricing/)
- [AWS GP2 vs GP3 Guide](https://cloudfix.com/blog/aws-gp2-vs-gp3/)
- [Amazon EventBridge Pricing](https://aws.amazon.com/eventbridge/pricing/)
- [AWS Pricing Calculator](https://calculator.aws/)
