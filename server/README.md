# AI Services - Local Testing Environment

This directory contains a complete local testing setup for the TrailLens AI services using Podman Compose.

## Services Included

- **LiteLLM Proxy with Database** - OpenAI-compatible API for AWS Bedrock with cost tracking (port 8000)
  - Container: `docker.litellm.ai/berriai/litellm-database:main-stable`
  - Features: Key generation, usage tracking, spend monitoring, budget management
- **PostgreSQL Database** - For LiteLLM persistence and cost tracking (port 5432, internal only)
- **OpenCode Server** - AI code assistant server (port 4096)
- **OpenCode Web UI** - Official browser interface for OpenCode (port 3001)
- **Nginx** - Reverse proxy for all services (port 8080)
- **Redis** - Cache for LiteLLM response caching (port 6379, internal only)

## Quick Start

```bash
# 1. Start all services
./manage.sh start

# 2. Test connectivity
./manage.sh test

# 3. Stop all services
./manage.sh stop
```

## Available Commands

```bash
./manage.sh build         # Build Docker images
./manage.sh start         # Start all services
./manage.sh stop          # Stop all services
./manage.sh restart       # Restart all services
./manage.sh status        # Show service status
./manage.sh logs [svc]    # Show logs (optionally for specific service)
./manage.sh test          # Test service connectivity
./manage.sh urls          # Show service URLs
./manage.sh clean         # Clean up all containers and data
```

## Service URLs

After starting services, you can access:

- **LiteLLM API**: http://localhost:8001
- **LiteLLM Docs**: http://localhost:8001/docs
- **OpenCode Server**: http://localhost:4096
- **OpenCode Web UI**: http://localhost:3001
- **Nginx Proxy**: http://localhost:8080

## Nginx Routes

The Nginx proxy provides path-based routing:

- `/` → OpenCode Web UI (port 3001) - **root URL**
- `/litellm` → LiteLLM API (port 8001)
- `/health` → Nginx health check

## Architecture

```
┌─────────────────────────────────────────────────┐
│             Nginx (Port 8080)                    │
│  Routes: /, /litellm, /health                   │
└───────────────┬──────────┬──────────────────────┘
                │          │
     ┌──────────▼─────┐   ┌▼───────────┐
     │ OpenCode Web   │   │  LiteLLM   │
     │      UI        │   │ (Port 8001)│
     │  (Port 3001)   │   │            │
     └────────────────┘   └─────┬──────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
         ┌──────────▼─────────┐  ┌─────────▼─────────┐
         │   PostgreSQL       │  │      Redis        │
         │   (Port 5432)      │  │   (Port 6379)     │
         └────────────────────┘  └───────────────────┘
```

## Configuration

### Environment Variables

Edit [`.env`](.env) to configure:
- AWS credentials (fake for local testing)
- LiteLLM API keys
- OpenCode passwords
- Port mappings

### LiteLLM Configuration

Edit [`config/litellm-config.yaml`](config/litellm-config.yaml) to:
- Add/remove Bedrock models
- Configure CORS settings
- Enable/disable logging
- Change timeout settings

## Git Operations

OpenCode Web UI has full access to your `~/src` directory with integrated git support.

### What's Mounted

- **Source code:** `~/src` → `/home/user/src` (inside container, read/write)
- **Git config:** `~/.gitconfig` → `/home/user/.gitconfig` (read-only)
- **SSH keys:** `~/.ssh` → `/home/user/.ssh` (read-only)

### Supported Git Operations

All standard git operations work from OpenCode Web UI:

- Clone repositories (both public and private)
- Commit changes (uses your git config for author info)
- Push/pull to remotes
- Branch management
- Submodule operations
- Stash, rebase, merge, etc.

### User Permissions

The container runs as your host user (UID 501, GID 20), ensuring:

- Files created in container have correct ownership on host
- No permission conflicts between host and container
- Git operations work seamlessly across both environments

### SSH Key Security

Your SSH keys are mounted read-only for security. The container can:

- ✅ Use keys to authenticate with git remotes
- ✅ Clone private repositories
- ❌ Modify or delete your SSH keys

### Troubleshooting Git Issues

**SSH Permission Denied:**

```bash
# Verify SSH keys are accessible in container
podman exec -it opencode-webui ls -la /home/user/.ssh

# Test SSH connection to GitHub
podman exec -it opencode-webui ssh -T git@github.com
```

**Git Author Not Set:**

```bash
# Verify git config is mounted
podman exec -it opencode-webui git config --list

# Check if user.name and user.email are present
```

**Permission Issues:**

```bash
# Check file ownership in mounted directory
ls -la ~/src

# Files should be owned by your user (mark:staff)
```

## Files Structure

```
server/
├── config/
│   ├── litellm-config.yaml      # LiteLLM configuration
│   └── opencode/                # OpenCode configuration
│       └── opencode.json        # OpenCode models and settings
├── nginx/
│   └── nginx.conf               # Nginx reverse proxy config
├── podman-compose.yaml          # Service orchestration
├── Dockerfile.opencode-server   # OpenCode Server container
├── Dockerfile.opencode-webui    # OpenCode Web UI container
├── manage.sh                    # Management script
├── .env                         # Environment variables
└── README.md                    # This file
```

## Testing Services

The `manage.sh test` command verifies:
1. LiteLLM health endpoint responding
2. OpenCode Web UI accepting connections
3. Nginx proxy accepting connections
4. Nginx routing to all backend services
5. Redis cache responding

## Troubleshooting

### LiteLLM not responding
- Check logs: `./manage.sh logs litellm`
- Ensure PostgreSQL is healthy: `podman ps`
- Verify DATABASE_URL in podman-compose.yaml

### OpenCode services not starting
- Check Node.js installation in containers
- Verify opencode-ai npm package is installed
- Check logs: `./manage.sh logs opencode-server`

### Nginx routing issues
- Verify all backend services are running: `./manage.sh status`
- Check Nginx configuration: `cat nginx/nginx.conf`
- Check Nginx logs: `./manage.sh logs nginx`

### Redis cache issues

- Check Redis health: `podman exec litellm-redis redis-cli ping`
- Check Redis logs: `./manage.sh logs redis`
- Verify Redis connection in LiteLLM config

## Production Deployment Notes

For AWS EC2 deployment:
1. Replace fake AWS credentials with real IAM user credentials
2. Update Bedrock model ARNs for your region (ca-central-1)
3. Configure SSL certificates with Let's Encrypt
4. Set secure passwords for OpenCode and LiteLLM
5. Enable CloudWatch monitoring for memory usage
6. Configure automated backups for PostgreSQL database

See [`ai/.github/prompts/ai-migration-canada-prompt.md`](../.github/prompts/ai-migration-canada-prompt.md) for full production deployment plan.

## References

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [LiteLLM Redis Caching](https://docs.litellm.ai/docs/caching/all_caches)
- [OpenCode Documentation](https://opencode.ai/docs/cli/)
- [LiteLLM Docker Quick Start](https://docs.litellm.ai/docs/proxy/docker_quick_start)
- [OpenCode Installation Guide](https://blog.wenhaofree.com/en/posts/articles/opencode-installation-guide/)
