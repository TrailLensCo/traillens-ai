#!/bin/bash
# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

set -euo pipefail

# Install Continue.dev configuration for TrailLens AI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTINUE_DIR="${HOME}/.continue"
CONFIG_FILE="${CONTINUE_DIR}/config.yaml"
BACKUP_FILE="${CONTINUE_DIR}/config.yaml.backup.$(date +%Y%m%d_%H%M%S)"

echo "TrailLens AI - Continue.dev Configuration Installer"
echo "===================================================="
echo ""

# Create Continue directory if it doesn't exist
if [ ! -d "${CONTINUE_DIR}" ]; then
    echo "Creating Continue.dev directory: ${CONTINUE_DIR}"
    mkdir -p "${CONTINUE_DIR}"
fi

# Backup existing config if present
if [ -f "${CONFIG_FILE}" ]; then
    echo "Backing up existing config to: ${BACKUP_FILE}"
    cp "${CONFIG_FILE}" "${BACKUP_FILE}"
fi

# Copy new config
echo "Installing Continue.dev config..."
cp "${SCRIPT_DIR}/config.yaml" "${CONFIG_FILE}"

echo ""
echo "✓ Configuration installed successfully!"
echo ""
echo "Next steps:"
echo "  1. Restart VSCode to load the new configuration"
echo "  2. Ensure AWS credentials are configured (~/.aws/credentials)"
echo "  3. Open Continue.dev sidebar (Cmd+L or Ctrl+L)"
echo "  4. Select your preferred model from the dropdown"
echo ""
echo "Models available:"
echo "  - Claude Opus 4.6 (Planning) - For complex architecture"
echo "  - Claude Sonnet 4.5 (Coding) - For general coding (recommended)"
echo "  - Claude Haiku 4.5 (Fast) - For quick questions"
echo ""
echo "See README.md for detailed usage instructions."
