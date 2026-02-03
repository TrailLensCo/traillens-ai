# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

"""
Configuration utilities for TrailLens AI infrastructure.
"""

import pulumi


def load_config():
    """
    Load configuration from Pulumi config.

    Returns:
        dict: Configuration dictionary with all required settings.
    """
    config = pulumi.Config()

    # Get stack name to determine environment
    stack = pulumi.get_stack()
    environment = stack  # dev or prod

    # Load configuration values
    config_dict = {
        "environment": environment,
        "project_name": config.get("project_name") or "traillens",
        "region": config.get("region") or "ca-central-1",
        "domain": config.get("domain") or f"ai.{get_base_domain(environment)}",
        "enable_bedrock": config.get_bool("enable_bedrock") or True,
        "bedrock_model_id": config.get("bedrock_model_id") or "anthropic.claude-sonnet-4-5-v2:0",
        "tags": {
            "Project": "TrailLens",
            "Environment": environment,
            "ManagedBy": "Pulumi",
            "Repository": "traillens-ai",
        },
    }

    # Add any custom tags from config
    custom_tags = config.get_object("tags") or {}
    config_dict["tags"].update(custom_tags)

    return config_dict


def get_base_domain(environment):
    """
    Get the base domain for the given environment.

    Args:
        environment: The environment (dev or prod).

    Returns:
        str: The base domain.
    """
    if environment == "prod":
        return "traillenshq.com"
    else:
        return "dev.traillenshq.com"


def validate_config(config):
    """
    Validate configuration to ensure all required values are present.

    Args:
        config: Configuration dictionary.

    Raises:
        Exception: If configuration is invalid.
    """
    required_keys = ["environment", "project_name", "region", "domain"]

    for key in required_keys:
        if key not in config or not config[key]:
            raise Exception(f"Missing required configuration: {key}")

    # Validate region
    if config["region"] != "ca-central-1":
        raise Exception(
            f"Invalid region: {config['region']}. "
            "All TrailLens infrastructure must be deployed to ca-central-1"
        )

    # Validate environment
    if config["environment"] not in ["dev", "prod"]:
        raise Exception(
            f"Invalid environment: {config['environment']}. "
            "Must be 'dev' or 'prod'"
        )

    pulumi.log.info("✓ Configuration validation passed")
