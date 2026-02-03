# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

"""
TrailLens AI Infrastructure with Pulumi

Main entry point for deploying AWS Bedrock infrastructure with Claude Sonnet 4.5.
This infrastructure enables Claude Code and Continue.dev VSCode extensions to use
AWS Bedrock for AI-assisted development.

Architecture:
    Phase 1: Bedrock IAM roles and policies
    Phase 2: API Gateway for Bedrock proxy
    Phase 3: DNS configuration with custom domain
"""

import pulumi

from components.api import create_api_stack
from components.bedrock import create_bedrock_stack
from components.dns import create_dns_stack
from utils.config import load_config, validate_config


def main():
    """
    Main deployment function that orchestrates all AI infrastructure components.
    """
    # Load configuration from Pulumi config
    config = load_config()

    # Validate configuration
    try:
        validate_config(config)
    except Exception as e:
        pulumi.log.error(f"Configuration validation failed: {e}")
        raise

    # Print configuration summary for visibility
    pulumi.log.info("=" * 70)
    pulumi.log.info(
        f"TrailLens AI Infrastructure Deployment - Stack: {pulumi.get_stack()}"
    )
    pulumi.log.info(f"Environment: {config['environment']}")
    pulumi.log.info(f"Region: {config['region']}")
    pulumi.log.info(f"Domain: {config['domain']}")
    pulumi.log.info(f"Bedrock Model: {config['bedrock_model_id']}")
    pulumi.log.info("=" * 70)

    # ==========================================================================
    # Phase 1: AWS Bedrock Setup
    # ==========================================================================

    pulumi.log.info("Phase 1: Deploying Bedrock resources...")

    bedrock = create_bedrock_stack(
        environment=config["environment"],
        project_name=config["project_name"],
        bedrock_model_id=config["bedrock_model_id"],
        tags=config.get("tags", {}),
    )

    # ==========================================================================
    # Phase 2: API Gateway
    # ==========================================================================

    pulumi.log.info("Phase 2: Deploying API Gateway...")

    api = create_api_stack(
        environment=config["environment"],
        project_name=config["project_name"],
        bedrock_role_arn=bedrock["bedrock_role_arn"],
        log_group_arn=bedrock["api_log_group"].arn,
        tags=config.get("tags", {}),
    )

    # ==========================================================================
    # Phase 3: DNS Configuration
    # ==========================================================================

    pulumi.log.info("Phase 3: Deploying DNS configuration...")

    dns = create_dns_stack(
        environment=config["environment"],
        project_name=config["project_name"],
        domain=config["domain"],
        api_id=api["api_id"],
        api_endpoint=api["api_endpoint"],
        tags=config.get("tags", {}),
    )

    # ==========================================================================
    # Exports
    # ==========================================================================

    pulumi.export("bedrock_role_arn", bedrock["bedrock_role_arn"])
    pulumi.export("lambda_role_arn", bedrock["lambda_role_arn"])
    pulumi.export("model_id", bedrock["model_id"])
    pulumi.export("api_endpoint", api["api_endpoint"])
    pulumi.export("api_id", api["api_id"])
    pulumi.export("domain_name", dns["domain_name"])
    pulumi.export("certificate_arn", dns["certificate_arn"])
    pulumi.export("custom_domain_endpoint", pulumi.Output.concat("https://", dns["domain_name"]))

    pulumi.log.info("✓ TrailLens AI Infrastructure deployment complete!")


if __name__ == "__main__":
    main()
