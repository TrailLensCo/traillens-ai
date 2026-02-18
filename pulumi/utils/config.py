# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

"""
Configuration utilities for TrailLens AI infrastructure.

Simplified configuration for production-only deployment.
"""

import pulumi


def load_config():
    """
    Load configuration from Pulumi config.

    Returns:
        dict: Configuration dictionary with all required settings.
    """
    config = pulumi.Config()

    # Load configuration values from Pulumi config
    project_name = config.require("project_name")
    region = config.require("region")
    domain = config.require("domain")
    zone_name = config.require("zone_name")

    # Load configuration values
    config_dict = {
        "project_name": project_name,
        "region": region,
        "domain": domain,
        "zone_name": zone_name,
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
    required_keys = ["project_name", "region", "domain", "zone_name"]

    for key in required_keys:
        if key not in config or not config[key]:
            raise Exception(f"Missing required configuration: {key}")

    # Validate region
    if config["region"] != "ca-central-1":
        raise Exception(
            f"Invalid region: {config['region']}. "
            "All TrailLens infrastructure must be deployed to ca-central-1"
        )

    pulumi.log.info("✓ Configuration validation passed")
