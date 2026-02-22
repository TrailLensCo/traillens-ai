# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

"""
DNS component for TrailLens AI infrastructure.

This component creates a CNAME record pointing to the AWS Bedrock endpoint.
"""

import pulumi
import pulumi_aws as aws


def create_dns_stack(project_name, domain, region, zone_name, tags):
    """
    Create DNS stack with Route53 CNAME record to Bedrock endpoint.

    Args:
        project_name: The project name.
        domain: The domain name (e.g., ai.traillenshq.com).
        region: AWS region for Bedrock endpoint.
        zone_name: Route53 hosted zone name.
        tags: Resource tags.

    Returns:
        dict: Dictionary containing DNS resources.
    """
    stack_name = f"{project_name}-ai"

    pulumi.log.info(f"Creating DNS stack: {stack_name}")

    # Look up the existing hosted zone
    zone = aws.route53.get_zone(name=zone_name)

    # Bedrock runtime endpoint for the region
    bedrock_endpoint = f"bedrock-runtime.{region}.amazonaws.com"

    # Create CNAME record pointing to Bedrock endpoint
    cname_record = aws.route53.Record(
        f"{stack_name}-cname",
        zone_id=zone.zone_id,
        name=domain,
        type="CNAME",
        records=[bedrock_endpoint],
        ttl=300,
    )

    pulumi.log.info(f"✓ CNAME created: {domain} → {bedrock_endpoint}")

    return {
        "zone": zone,
        "cname_record": cname_record,
        "domain_name": domain,
        "bedrock_endpoint": bedrock_endpoint,
    }
