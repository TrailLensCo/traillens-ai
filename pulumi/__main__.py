# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

"""
TrailLens AI Infrastructure with Pulumi

Simplified infrastructure for single developer use.
Creates IAM user and policies for direct AWS Bedrock access.

Supported Models:
    - Claude Opus 4.6 (Planning/Architecture)
    - Claude Sonnet 4.5 (Coding)
    - Claude Haiku 4.5 (Completion/Autocomplete)
"""

import pulumi

from components.bedrock import create_bedrock_iam_stack
from components.dns import create_dns_stack
from utils.config import load_config, validate_config


def main():
    """
    Main deployment function for simplified Bedrock IAM infrastructure.
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
    pulumi.log.info(f"Region: {config['region']}")
    pulumi.log.info(f"Domain: {config['domain']}")
    pulumi.log.info(f"Zone: {config['zone_name']}")
    pulumi.log.info("Supported Models:")
    pulumi.log.info("  - Claude Opus 4.6 (Planning)")
    pulumi.log.info("  - Claude Sonnet 4.5 (Coding)")
    pulumi.log.info("  - Claude Haiku 4.5 (Completion)")
    pulumi.log.info("=" * 70)

    # ==========================================================================
    # AWS Bedrock IAM Setup
    # ==========================================================================

    pulumi.log.info("Creating Bedrock IAM resources...")

    bedrock = create_bedrock_iam_stack(
        project_name=config["project_name"],
        region=config["region"],
        tags=config.get("tags", {}),
    )

    # ==========================================================================
    # DNS Configuration
    # ==========================================================================

    pulumi.log.info("Creating DNS CNAME to Bedrock endpoint...")

    dns = create_dns_stack(
        project_name=config["project_name"],
        domain=config["domain"],
        region=config["region"],
        zone_name=config["zone_name"],
        tags=config.get("tags", {}),
    )

    # ==========================================================================
    # Exports
    # ==========================================================================

    pulumi.export("iam_user_name", bedrock["iam_user_name"])
    pulumi.export("iam_user_arn", bedrock["iam_user_arn"])
    pulumi.export("access_key_id", bedrock["access_key_id"])
    pulumi.export("secret_access_key", bedrock["secret_access_key"])
    pulumi.export("region", config["region"])
    pulumi.export("bedrock_endpoint", dns["bedrock_endpoint"])
    pulumi.export("custom_domain", dns["domain_name"])
    pulumi.export("models", {
        "opus": "anthropic.claude-opus-4-6",
        "sonnet": "anthropic.claude-sonnet-4-5-v2:0",
        "haiku": "anthropic.claude-haiku-4-5-20251001:0",
    })

    pulumi.log.info("✓ TrailLens AI infrastructure deployment complete!")
    pulumi.log.info("")
    pulumi.log.info("Next steps:")
    pulumi.log.info("  1. Save the access credentials from outputs")
    pulumi.log.info("  2. Configure AWS credentials: ~/.aws/credentials")
    pulumi.log.info("  3. Configure Continue.dev with model selection")
    pulumi.log.info("  4. Use custom domain or direct Bedrock endpoint")
    pulumi.log.info("  See SETUP.md for detailed instructions")


if __name__ == "__main__":
    main()
