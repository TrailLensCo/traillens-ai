#!/bin/bash
#
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.
#
# Setup AWS credentials and Python virtual environment for the AI project.
#
# Detects devcontainer and uses local AWS services automatically.
#
# Usage: source scripts/setup-env.sh [-r] [-p profile] [-d venv_dir] [-h]
#   or:  ./scripts/setup-env.sh [-r] [-p profile] [-d venv_dir] [-h]
#
# Options:
#   -r            Recreate the virtual environment (wipe and rebuild)
#   -p profile    AWS profile to use (default: traillens-pulumi)
#   -d venv_dir   Virtual environment directory (default: pulumi/venv)
#   -h            Show this help message
#
# Environment Variables:
#   VENV_DIR              Override the virtual environment directory
#   REQUIREMENTS_FILE     Path to requirements.txt
#   AWS_PROFILE           AWS profile name
#   AWS_CREDENTIALS_FILE  AWS credentials file location
#
# Examples:
#   source scripts/setup-env.sh                    # Normal setup
#   source scripts/setup-env.sh -r                 # Recreate venv
#   source scripts/setup-env.sh -p my-profile      # Use specific AWS profile
#   source scripts/setup-env.sh -r -p prod         # Recreate with specific profile

set -uo pipefail

# Script directory and paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
AI_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PULUMI_DIR="${AI_ROOT}/pulumi"
CURRENT_DIR="$(pwd)"

# Defaults (can be overridden by environment variables)
DEFAULT_VENV_DIR="${VENV_DIR:-${PULUMI_DIR}/venv}"
DEFAULT_AWS_PROFILE="traillens-pulumi"

# Parse flags
RECREATE_VENV=0
VENV_DIR_PATH="${DEFAULT_VENV_DIR}"
AWS_PROFILE="${AWS_PROFILE:-${DEFAULT_AWS_PROFILE}}"

show_usage() {
    echo "Usage: source ${BASH_SOURCE[0]} [-r] [-p profile] [-d venv_dir] [-h]"
    echo ""
    echo "Options:"
    echo "  -r            Recreate the virtual environment (wipe and rebuild)"
    echo "  -p profile    AWS profile to use (default: traillens-pulumi)"
    echo "  -d venv_dir   Virtual environment directory (default: pulumi/venv)"
    echo "  -h            Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  VENV_DIR              Override the virtual environment directory"
    echo "  REQUIREMENTS_FILE     Path to requirements.txt"
    echo "  AWS_PROFILE           AWS profile name"
    echo "  AWS_CREDENTIALS_FILE  AWS credentials file location"
    echo ""
    echo "Examples:"
    echo "  source scripts/setup-env.sh                # Normal setup"
    echo "  source scripts/setup-env.sh -r             # Recreate venv"
    echo "  source scripts/setup-env.sh -p my-profile  # Use specific AWS profile"
}

while getopts "rp:d:h" opt; do
    case "${opt}" in
        r)
            RECREATE_VENV=1
            ;;
        p)
            AWS_PROFILE="${OPTARG}"
            ;;
        d)
            VENV_DIR_PATH="${OPTARG}"
            ;;
        h)
            show_usage
            return 0 2>/dev/null || exit 0
            ;;
        \?)
            echo "Error: Invalid option -${OPTARG}" >&2
            show_usage
            return 1 2>/dev/null || exit 1
            ;;
        :)
            echo "Error: Option -${OPTARG} requires an argument" >&2
            show_usage
            return 1 2>/dev/null || exit 1
            ;;
    esac
done
shift $((OPTIND - 1))

# Normalize venv path to absolute
if [[ "${VENV_DIR_PATH}" != /* ]]; then
    VENV_DIR_PATH="${CURRENT_DIR}/${VENV_DIR_PATH}"
fi

# Determine requirements file
if [[ -n "${REQUIREMENTS_FILE:-}" ]]; then
    REQUIREMENTS_PATH="${REQUIREMENTS_FILE}"
elif [[ -f "${PULUMI_DIR}/requirements.txt" ]]; then
    REQUIREMENTS_PATH="${PULUMI_DIR}/requirements.txt"
else
    REQUIREMENTS_PATH=""
fi

CREDENTIALS_FILE="${AWS_CREDENTIALS_FILE:-${HOME}/.aws/credentials}"

# Detect if running in devcontainer
IN_DEVCONTAINER=false
if [[ -f "/.dockerenv" ]] || [[ -n "${REMOTE_CONTAINERS:-}" ]] || [[ -n "${CODESPACES:-}" ]]; then
    IN_DEVCONTAINER=true
fi

# Setup AWS credentials based on environment
if [[ "${IN_DEVCONTAINER}" == "true" ]]; then
    echo "Detected devcontainer - using local AWS services"
    export AWS_ACCESS_KEY_ID="test"
    export AWS_SECRET_ACCESS_KEY="test"
    export AWS_REGION="us-east-1"
    export AWS_DEFAULT_REGION="us-east-1"
    export AWS_ENDPOINT_URL="http://localstack:4566"
    export USE_LOCAL_AWS="true"
    AWS_PROFILE="local-devcontainer"
    echo "  Profile: ${AWS_PROFILE}"
    echo "  Region: ${AWS_REGION}"
    echo "  LocalStack: http://localstack:4566"
else
    # Check if credentials file exists
    if [[ ! -f "${CREDENTIALS_FILE}" ]]; then
        echo "Error: AWS credentials file not found at ${CREDENTIALS_FILE}" >&2
        echo "  Run 'aws configure' to create it" >&2
        return 1 2>/dev/null || exit 1
    fi

    # Parse credentials from the specified profile
    in_profile=0
    while IFS= read -r line || [[ -n "${line}" ]]; do
        line=$(echo "${line}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

        if [[ "${line}" =~ ^\[.*\]$ ]]; then
            profile_name=$(echo "${line}" | sed 's/^\[\(.*\)\]$/\1/')
            if [[ "${profile_name}" == "${AWS_PROFILE}" ]]; then
                in_profile=1
            else
                in_profile=0
            fi
            continue
        fi

        if [[ ${in_profile} -eq 1 ]]; then
            if [[ "${line}" =~ ^aws_access_key_id[[:space:]]*=[[:space:]]*(.*) ]]; then
                export AWS_ACCESS_KEY_ID="${BASH_REMATCH[1]}"
            elif [[ "${line}" =~ ^aws_secret_access_key[[:space:]]*=[[:space:]]*(.*) ]]; then
                export AWS_SECRET_ACCESS_KEY="${BASH_REMATCH[1]}"
            elif [[ "${line}" =~ ^aws_session_token[[:space:]]*=[[:space:]]*(.*) ]]; then
                export AWS_SESSION_TOKEN="${BASH_REMATCH[1]}"
            elif [[ "${line}" =~ ^region[[:space:]]*=[[:space:]]*(.*) ]]; then
                export AWS_REGION="${BASH_REMATCH[1]}"
            fi
        fi
    done < "${CREDENTIALS_FILE}"

    # Verify credentials were loaded
    if [[ -z "${AWS_ACCESS_KEY_ID:-}" ]]; then
        echo "Error: Could not find profile '${AWS_PROFILE}' in ${CREDENTIALS_FILE}" >&2
        echo "  Available profiles:" >&2
        grep '^\[' "${CREDENTIALS_FILE}" | sed 's/^\[\(.*\)\]$/  - \1/' >&2
        return 1 2>/dev/null || exit 1
    fi

    if [[ -z "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
        echo "Error: Profile '${AWS_PROFILE}' is missing aws_secret_access_key" >&2
        return 1 2>/dev/null || exit 1
    fi

    export AWS_PROFILE

    # Load region from config file if not set from credentials
    if [[ -z "${AWS_REGION:-}" ]] && [[ -f "${HOME}/.aws/config" ]]; then
        config_profile="${AWS_PROFILE}"
        [[ "${config_profile}" != "default" ]] && config_profile="profile ${config_profile}"

        in_config_profile=0
        while IFS= read -r line || [[ -n "${line}" ]]; do
            line=$(echo "${line}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

            if [[ "${line}" =~ ^\[.*\]$ ]]; then
                profile_name=$(echo "${line}" | sed 's/^\[\(.*\)\]$/\1/')
                if [[ "${profile_name}" == "${config_profile}" ]]; then
                    in_config_profile=1
                else
                    in_config_profile=0
                fi
                continue
            fi

            if [[ ${in_config_profile} -eq 1 ]] && [[ "${line}" =~ ^region[[:space:]]*=[[:space:]]*(.*) ]]; then
                export AWS_REGION="${BASH_REMATCH[1]}"
                break
            fi
        done < "${HOME}/.aws/config"
    fi

    # Set default region if still not set
    if [[ -z "${AWS_REGION:-}" ]]; then
        export AWS_REGION="ca-central-1"
    fi

    export AWS_DEFAULT_REGION="${AWS_REGION}"

    echo "AWS credentials loaded"
    echo "  Profile:    ${AWS_PROFILE}"
    echo "  Region:     ${AWS_REGION}"
    echo "  Access Key: ${AWS_ACCESS_KEY_ID:0:8}..."
    [[ -n "${AWS_SESSION_TOKEN:-}" ]] && echo "  Session Token: [SET]"
fi

echo ""
echo "Setting up Python environment..."
echo "  Virtual environment: ${VENV_DIR_PATH}"
[[ -n "${REQUIREMENTS_PATH}" ]] && echo "  Requirements file:   ${REQUIREMENTS_PATH}"
echo ""

# Verify Python 3 is available
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is not installed or not in PATH" >&2
    return 1 2>/dev/null || exit 1
fi

# Handle -r (recreate) flag
if [[ ${RECREATE_VENV} -eq 1 ]]; then
    if [[ -d "${VENV_DIR_PATH}" ]]; then
        echo "  Recreating virtual environment..."
        echo "  Removing existing venv at ${VENV_DIR_PATH}..."
        rm -rf "${VENV_DIR_PATH}"
        if [[ $? -ne 0 ]]; then
            echo "Error: Failed to remove existing virtual environment" >&2
            return 1 2>/dev/null || exit 1
        fi
        echo "  Existing venv removed"
    else
        echo "  Creating new virtual environment (-r specified)..."
    fi
fi

# Create venv if it does not exist
if [[ ! -d "${VENV_DIR_PATH}" ]]; then
    echo "  Creating virtual environment at ${VENV_DIR_PATH}..."
    mkdir -p "$(dirname "${VENV_DIR_PATH}")"
    python3 -m venv "${VENV_DIR_PATH}"
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to create virtual environment" >&2
        return 1 2>/dev/null || exit 1
    fi
    echo "  Virtual environment created"
fi

# Activate (or re-activate) the venv
if [[ -z "${VIRTUAL_ENV:-}" ]] || [[ "${VIRTUAL_ENV}" != "${VENV_DIR_PATH}" ]]; then
    echo "  Activating virtual environment..."
    source "${VENV_DIR_PATH}/bin/activate"
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to activate virtual environment" >&2
        return 1 2>/dev/null || exit 1
    fi
    echo "  Virtual environment activated: ${VENV_DIR_PATH}"
else
    echo "  Virtual environment already activated"
    if [[ ${RECREATE_VENV} -eq 1 ]]; then
        echo "Warning: -r was specified but venv is already active" >&2
        echo "  Deactivate first with 'deactivate' then re-run this script" >&2
    fi
fi

# Install or update dependencies
if [[ -n "${REQUIREMENTS_PATH}" ]] && [[ -f "${REQUIREMENTS_PATH}" ]]; then
    if [[ ${RECREATE_VENV} -eq 1 ]]; then
        echo "  Installing Python dependencies (fresh install)..."
        pip install --upgrade pip setuptools wheel
        pip install -r "${REQUIREMENTS_PATH}"
    else
        echo "  Checking Python dependencies..."
        pip install -q --upgrade pip
        pip install -q -r "${REQUIREMENTS_PATH}"
    fi

    if [[ $? -ne 0 ]]; then
        echo "Warning: Some dependencies may not have installed correctly" >&2
    else
        echo "  Python dependencies ready"
    fi
else
    echo "  No requirements.txt found, skipping dependency install"
fi

echo ""
echo "Environment setup complete!"
echo "  Working directory:   ${CURRENT_DIR}"
echo "  Virtual environment: ${VENV_DIR_PATH}"
