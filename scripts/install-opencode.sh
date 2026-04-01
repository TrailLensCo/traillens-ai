#!/bin/bash
# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

set -euo pipefail

# Install OpenCode configuration for TrailLens AI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
OPENCODE_DIR="${HOME}/.config/opencode"
CONFIG_FILE="${OPENCODE_DIR}/opencode.json"
BACKUP_FILE="${OPENCODE_DIR}/opencode.json.backup.$(date +%Y%m%d_%H%M%S)"
SOURCE_CONFIG="${PROJECT_ROOT}/ai/server/config/opencode/opencode.json"
SOURCE_ENV="${PROJECT_ROOT}/ai/server/.env"

echo "TrailLens AI - OpenCode Configuration Installer"
echo "==============================================="
echo ""

# Check if source config exists
if [ ! -f "${SOURCE_CONFIG}" ]; then
    echo "Error: Source config not found at ${SOURCE_CONFIG}" >&2
    exit 1
fi

# Create OpenCode directory if it doesn't exist
if [ ! -d "${OPENCODE_DIR}" ]; then
    echo "Creating OpenCode directory: ${OPENCODE_DIR}"
    mkdir -p "${OPENCODE_DIR}"
fi

# Backup existing config if present
if [ -f "${CONFIG_FILE}" ]; then
    echo "Backing up existing config to: ${BACKUP_FILE}"
    cp "${CONFIG_FILE}" "${BACKUP_FILE}"
fi

# Extract LITELLM_MASTER_KEY from project .env
echo "Reading LiteLLM configuration..."

if [ -f "${SOURCE_ENV}" ]; then
    LITELLM_KEY=$(grep "^LITELLM_MASTER_KEY=" "${SOURCE_ENV}" | cut -d '=' -f2- || echo "")

    if [ -z "${LITELLM_KEY}" ]; then
        echo "Warning: LITELLM_MASTER_KEY not found in ${SOURCE_ENV}" >&2
        LITELLM_KEY="sk-test-1234567890"
    fi
else
    echo "Warning: Project .env not found, using default key" >&2
    LITELLM_KEY="sk-test-1234567890"
fi

# Copy config and substitute the API key
echo "Installing OpenCode config with API key..."
sed "s/{env:LITELLM_MASTER_KEY}/${LITELLM_KEY}/g" "${SOURCE_CONFIG}" > "${CONFIG_FILE}"

echo ""
echo "✓ Configuration installed successfully!"
echo ""
echo "Installation Summary:"
echo "  - Config: ${CONFIG_FILE}"
echo "  - API Key: ${LITELLM_KEY}"
echo ""
echo "Next steps:"
echo "  1. Ensure LiteLLM server is running:"
echo "     cd ai/server && ./manage.sh up"
echo "  2. Start OpenCode:"
echo "     - VSCode: Install OpenCode extension and it will auto-detect config"
echo "     - TUI: Run 'opencode' in terminal"
echo "  3. Verify LiteLLM is accessible:"
echo "     curl http://localhost:8001/health"
echo ""
echo "Models available:"
echo "  - Claude Sonnet 4.6 (Default)"
echo "  - Claude Haiku 4.5"
echo "  - Claude 3.5 Haiku"
echo "  - Claude Opus 4.6"
echo "  - Kimi K2.5 (Multimodal + Agent Swarm)"
echo "  - Titan Image Generator V2"
echo "  - Titan Embed Text V2"
echo "  - Cohere Rerank V3.5"
echo ""
echo "To verify installation:"
echo "  cat ${CONFIG_FILE}"
echo ""
