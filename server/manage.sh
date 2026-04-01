#!/bin/bash
# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check if podman-compose is installed
check_dependencies() {
    if ! command -v podman-compose &> /dev/null; then
        log_error "podman-compose is not installed"
        log_info "Install with: pip install podman-compose"
        exit 1
    fi
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    podman-compose build
    log_success "Docker images built successfully"
}

# Start all services
start_services() {
    log_info "Starting AI services..."

    # Load environment variables
    if [[ -f .env ]]; then
        set -a
        source .env
        set +a
    fi

    # Export current user's UID/GID for container user mapping
    # This ensures files created in container match host ownership
    export USER_UID=$(id -u)
    export USER_GID=$(id -g)

    log_info "Configuring OpenCode container:"
    log_info "  User: $(whoami) (UID=$USER_UID, GID=$USER_GID)"
    log_info "  Source directory: $HOME/src"

    # Build custom images first
    log_info "Building custom container images..."
    podman-compose build

    # Start services
    log_info "Starting containers..."
    podman-compose up -d

    log_success "All services started"
    log_info "Waiting for services to be healthy..."
    sleep 10

    # Show status
    show_status
}

# Stop all services
stop_services() {
    log_info "Stopping AI services..."
    podman-compose down
    log_success "All services stopped"
}

# Restart all services
restart_services() {
    log_info "Restarting AI services..."
    stop_services
    sleep 2
    start_services
}

# Show service status
show_status() {
    log_info "Service Status:"
    podman-compose ps
}

# Show service logs
show_logs() {
    local service="${1:-}"

    if [[ -z "$service" ]]; then
        log_info "Showing logs for all services (Ctrl+C to exit)..."
        podman-compose logs -f
    else
        log_info "Showing logs for $service (Ctrl+C to exit)..."
        podman-compose logs -f "$service"
    fi
}

# Test service connectivity
test_services() {
    log_info "Testing service connectivity..."
    local all_ok=true

    # Test LiteLLM
    log_info "Testing LiteLLM (http://localhost:8001)..."
    if curl -s -f http://localhost:8001/health/liveliness > /dev/null; then
        log_success "LiteLLM is responding"
    else
        log_error "LiteLLM is not responding"
        all_ok=false
    fi

    # Test OpenCode Web (Server + UI combined)
    log_info "Testing OpenCode Web (http://localhost:3001)..."
    if curl -s -f http://localhost:3001 > /dev/null 2>&1 || nc -z localhost 3001 2>/dev/null; then
        log_success "OpenCode Web is responding"
    else
        log_error "OpenCode Web is not responding"
        all_ok=false
    fi

    # Test Nginx
    log_info "Testing Nginx (http://localhost:8080)..."
    if curl -s -f http://localhost:8080/health > /dev/null; then
        log_success "Nginx is responding"
    else
        log_error "Nginx is not responding"
        all_ok=false
    fi

    # Test Nginx routes
    log_info "Testing Nginx routing..."

    # Test / -> OpenCode Web
    if curl -s -f http://localhost:8080/ > /dev/null 2>&1; then
        log_success "Nginx route / -> OpenCode Web is working"
    else
        log_warning "Nginx route / -> OpenCode Web may not be working"
    fi

    # Test /litellm -> LiteLLM
    if curl -s -f http://localhost:8080/litellm/health/liveliness > /dev/null; then
        log_success "Nginx route /litellm -> LiteLLM is working"
    else
        log_warning "Nginx route /litellm -> LiteLLM may not be working"
    fi

    if [[ "$all_ok" == true ]]; then
        log_success "All services are healthy!"
        show_service_urls
    else
        log_error "Some services are not responding correctly"
        return 1
    fi
}

# Show service URLs
show_service_urls() {
    echo ""
    log_info "Service URLs:"
    echo "  - LiteLLM API:          http://localhost:8001"
    echo "  - LiteLLM Docs:         http://localhost:8001/docs"
    echo "  - OpenCode Web:         http://localhost:3001  (auth: opencode / local-test-password-123)"
    echo "  - Nginx Proxy:          http://localhost:8080"
    echo ""
    log_info "Nginx Routes:"
    echo "  - OpenCode Web:         http://localhost:8080/       (auth required)"
    echo "  - LiteLLM API:          http://localhost:8080/litellm"
    echo "  - Health Check:         http://localhost:8080/health"
    echo ""
    log_info "OpenCode Authentication:"
    echo "  - Username: opencode"
    echo "  - Password: local-test-password-123"
    echo ""
    log_info "LiteLLM API Key:"
    echo "  - Master Key: sk-test-1234567890"
    echo ""
}

# Sync Podman machine time
sync_time() {
    log_info "Syncing Podman machine time with NTP servers..."

    # Force immediate chrony sync
    if podman machine ssh "sudo chronyc makestep 2>&1" | grep -q "200 OK"; then
        log_success "Time synchronized successfully"
    else
        log_warning "chronyc makestep returned non-standard response (may still work)"
    fi

    # Show current time status
    echo ""
    log_info "Time Status:"
    podman machine ssh "chronyc tracking" | grep -E "(Reference ID|System time|Last offset)"

    echo ""
    log_info "Host time:      $(date)"
    log_info "Container time: $(podman machine ssh 'date')"
}

# Clean up all data
clean() {
    local cleanup_type="${1:-all}"

    case "$cleanup_type" in
        containers)
            log_warning "This will remove all containers only (preserving volumes, images, and data)"
            read -p "Are you sure? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                log_info "Stopping and removing containers..."
                podman-compose down || true
                log_success "Cleanup complete - containers removed"
            else
                log_info "Cleanup cancelled"
            fi
            ;;
        all)
            log_warning "This will remove all containers, volumes, images, networks, and data"
            read -p "Are you sure? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                log_info "Stopping and removing containers..."
                podman-compose down -v --rmi all || true

                log_info "Removing data directory..."
                rm -rf data/

                log_info "Pruning unused networks..."
                podman network prune -f || true

                log_success "Cleanup complete - all containers, volumes, images, and data removed"
            else
                log_info "Cleanup cancelled"
            fi
            ;;
        *)
            log_error "Unknown cleanup type: $cleanup_type"
            log_info "Valid options: all, containers"
            exit 1
            ;;
    esac
}

# Show help
show_help() {
    cat << EOF
AI Services Management Script

Usage: $0 <command>

Commands:
  build              Build Docker images (nginx, opencode-webui)
  start              Start all services
  stop               Stop all services
  restart            Restart all services
  status             Show service status
  logs [svc]         Show logs (optionally for specific service)
  test               Test service connectivity
  urls               Show service URLs
  sync-time          Sync Podman machine time with NTP (fixes AWS signature errors)
  clean [type]       Clean up resources (default: all)
                       - all:        Remove containers, volumes, images, networks, and data
                       - containers: Remove only containers (preserve everything else)
  help               Show this help message

Examples:
  $0 build             # Build Docker images
  $0 start             # Start all services (builds images if needed)
  $0 test              # Test all services
  $0 logs              # Show all logs
  $0 logs litellm      # Show LiteLLM logs only
  $0 clean containers  # Remove only containers
  $0 clean all         # Full cleanup (containers, volumes, images, data)
  $0 stop              # Stop everything

EOF
}

# Main command dispatcher
main() {
    check_dependencies

    local command="${1:-help}"

    case "$command" in
        build)
            build_images
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "${2:-}"
            ;;
        test)
            test_services
            ;;
        urls)
            show_service_urls
            ;;
        sync-time)
            sync_time
            ;;
        clean)
            clean "${2:-all}"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
