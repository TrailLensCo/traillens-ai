#!/bin/bash
# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

# Setup AWS credentials and Python virtual environment for Pulumi
# Usage: source scripts/setup-env.sh [profile_name]
#
# If no profile is specified, uses 'traillens-pulumi' profile
# Automatically creates and activates Python venv if needed
# Detects devcontainer and uses local AWS services automatically

# Determine the script's directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PULUMI_DIR="$AI_ROOT/pulumi"
VENV_DIR="$PULUMI_DIR/venv"

# Detect if running in devcontainer
IN_DEVCONTAINER=false
if [[ -f "/.dockerenv" ]] || [[ -n "$REMOTE_CONTAINERS" ]] || [[ -n "$CODESPACES" ]]; then
    IN_DEVCONTAINER=true
fi

# Setup AWS credentials based on environment
if [[ "$IN_DEVCONTAINER" == "true" ]]; then
    # Use local AWS services (LocalStack)
    echo "🐳 Detected devcontainer - using local AWS services"
    export AWS_ACCESS_KEY_ID="test"
    export AWS_SECRET_ACCESS_KEY="test"
    export AWS_REGION="us-east-1"
    export AWS_DEFAULT_REGION="us-east-1"
    export AWS_ENDPOINT_URL="http://localstack:4566"
    export USE_LOCAL_AWS="true"

    AWS_PROFILE="local-devcontainer"

    echo "✓ Local AWS credentials configured"
    echo "  Profile: $AWS_PROFILE"
    echo "  Region: $AWS_REGION"
    echo "  LocalStack: http://localstack:4566"
else
    # Use AWS credentials from profile
    AWS_PROFILE="${1:-traillens-pulumi}"
    CREDENTIALS_FILE="${AWS_CREDENTIALS_FILE:-$HOME/.aws/credentials}"

    # Check if credentials file exists
    if [[ ! -f "$CREDENTIALS_FILE" ]]; then
        echo "❌ Error: AWS credentials file not found at $CREDENTIALS_FILE"
        echo "   Run 'aws configure' to create it"
        return 1 2>/dev/null || exit 1
    fi

    # Parse credentials from the specified profile
    in_profile=0
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Trim whitespace
        line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

        # Check for profile header
        if [[ "$line" =~ ^\[.*\]$ ]]; then
            profile_name=$(echo "$line" | sed 's/^\[\(.*\)\]$/\1/')
            if [[ "$profile_name" == "$AWS_PROFILE" ]]; then
                in_profile=1
            else
                in_profile=0
            fi
            continue
        fi

        # Parse credentials if in target profile
        if [[ $in_profile -eq 1 ]]; then
            if [[ "$line" =~ ^aws_access_key_id[[:space:]]*=[[:space:]]*(.*) ]]; then
                export AWS_ACCESS_KEY_ID="${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^aws_secret_access_key[[:space:]]*=[[:space:]]*(.*) ]]; then
                export AWS_SECRET_ACCESS_KEY="${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^aws_session_token[[:space:]]*=[[:space:]]*(.*) ]]; then
                export AWS_SESSION_TOKEN="${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^region[[:space:]]*=[[:space:]]*(.*) ]]; then
                export AWS_REGION="${BASH_REMATCH[1]}"
            fi
        fi
    done < "$CREDENTIALS_FILE"

    # Verify credentials were loaded
    if [[ -z "$AWS_ACCESS_KEY_ID" ]]; then
        echo "❌ Error: Could not find profile '$AWS_PROFILE' in $CREDENTIALS_FILE"
        echo "   Available profiles:"
        grep '^\[' "$CREDENTIALS_FILE" | sed 's/^\[\(.*\)\]$/   - \1/'
        return 1 2>/dev/null || exit 1
    fi

    if [[ -z "$AWS_SECRET_ACCESS_KEY" ]]; then
        echo "❌ Error: Profile '$AWS_PROFILE' is missing aws_secret_access_key"
        return 1 2>/dev/null || exit 1
    fi

    # Also export the profile name for tools that use it
    export AWS_PROFILE

    # Load region from config file if not set from credentials
    if [[ -z "$AWS_REGION" ]] && [[ -f "$HOME/.aws/config" ]]; then
        config_profile="$AWS_PROFILE"
        [[ "$config_profile" != "default" ]] && config_profile="profile $config_profile"

        in_config_profile=0
        while IFS= read -r line || [[ -n "$line" ]]; do
            line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

            if [[ "$line" =~ ^\[.*\]$ ]]; then
                profile_name=$(echo "$line" | sed 's/^\[\(.*\)\]$/\1/')
                if [[ "$profile_name" == "$config_profile" ]]; then
                    in_config_profile=1
                else
                    in_config_profile=0
                fi
                continue
            fi

            if [[ $in_config_profile -eq 1 ]] && [[ "$line" =~ ^region[[:space:]]*=[[:space:]]*(.*) ]]; then
                export AWS_REGION="${BASH_REMATCH[1]}"
                break
            fi
        done < "$HOME/.aws/config"
    fi

    # Set default region if still not set
    if [[ -z "$AWS_REGION" ]]; then
        export AWS_REGION="ca-central-1"
    fi

    # Success message
    echo "✓ AWS credentials loaded"
    echo "  Profile: $AWS_PROFILE"
    echo "  Region: $AWS_REGION"
    echo "  Access Key: ${AWS_ACCESS_KEY_ID:0:8}..."
    [[ -n "$AWS_SESSION_TOKEN" ]] && echo "  Session Token: [SET]"
fi
echo ""
echo "Setting up Python environment..."

# Check for --recreate flag
FORCE_RECREATE=false
if [[ "$2" == "--recreate" ]] || [[ "$1" == "--recreate" && -z "$2" ]]; then
    FORCE_RECREATE=true
fi

# Check if venv exists
if [[ -d "$VENV_DIR" ]]; then
    if [[ "$FORCE_RECREATE" == "true" ]]; then
        echo "  Removing existing virtual environment (--recreate flag)..."
        rm -rf "$VENV_DIR"
        echo "  Creating new virtual environment at $VENV_DIR..."
        python3 -m venv "$VENV_DIR"
        if [[ $? -ne 0 ]]; then
            echo "❌ Error: Failed to create virtual environment"
            return 1 2>/dev/null || exit 1
        fi
        echo "  ✓ Virtual environment created"
    else
        echo "  ✓ Using existing virtual environment (use --recreate to force recreation)"
    fi
elif [[ ! -d "$VENV_DIR" ]]; then
    echo "  Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    if [[ $? -ne 0 ]]; then
        echo "❌ Error: Failed to create virtual environment"
        return 1 2>/dev/null || exit 1
    fi
    echo "  ✓ Virtual environment created"
fi

# Check if already activated
if [[ -z "$VIRTUAL_ENV" ]] || [[ "$VIRTUAL_ENV" != "$VENV_DIR" ]]; then
    echo "  Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    if [[ $? -ne 0 ]]; then
        echo "❌ Error: Failed to activate virtual environment"
        return 1 2>/dev/null || exit 1
    fi
    echo "  ✓ Virtual environment activated: $VENV_DIR"

    # Install/update requirements if requirements.txt exists
    if [[ -f "$PULUMI_DIR/requirements.txt" ]]; then
        echo "  Checking Python dependencies..."
        pip install -q -r "$PULUMI_DIR/requirements.txt"
        if [[ $? -eq 0 ]]; then
            echo "  ✓ Python dependencies ready"
        else
            echo "⚠️  Warning: Some dependencies may not have installed correctly"
        fi
    fi
else
    echo "  ✓ Virtual environment already activated"
fi

echo ""
echo "✓ Environment setup complete!"
echo "  Working directory: $PULUMI_DIR"
