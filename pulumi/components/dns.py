# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

"""
DNS component for TrailLens AI infrastructure.

This component creates Route53 records and ACM certificates for the AI domain.
"""

import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions


def create_dns_stack(
    environment,
    project_name,
    domain,
    api_id,
    api_endpoint,
    tags
):
    """
    Create DNS stack with Route53 and ACM certificate.

    Args:
        environment: The environment (dev or prod).
        project_name: The project name.
        domain: The domain name (e.g., ai.traillenshq.com).
        api_id: API Gateway ID.
        api_endpoint: API Gateway endpoint URL.
        tags: Resource tags.

    Returns:
        dict: Dictionary containing DNS resources.
    """
    stack_name = f"{project_name}-ai-{environment}"

    pulumi.log.info(f"Creating DNS stack: {stack_name}")

    # Determine the hosted zone name based on environment
    if environment == "prod":
        zone_name = "traillenshq.com"
    else:
        zone_name = "dev.traillenshq.com"

    # Look up the existing hosted zone from the infra stack
    # This zone should already exist from the main infrastructure deployment
    zone = aws.route53.get_zone(name=zone_name)

    # Create ACM certificate for the custom domain
    certificate = aws.acm.Certificate(
        f"{stack_name}-cert",
        domain_name=domain,
        validation_method="DNS",
        tags={**tags, "Name": f"{stack_name}-cert"},
        opts=ResourceOptions(
            protect=False,
        ),
    )

    # Create DNS validation records
    validation_records = []
    for i, validation_option in enumerate(certificate.domain_validation_options):
        record = aws.route53.Record(
            f"{stack_name}-cert-validation-{i}",
            zone_id=zone.zone_id,
            name=validation_option.resource_record_name,
            type=validation_option.resource_record_type,
            records=[validation_option.resource_record_value],
            ttl=60,
            opts=ResourceOptions(
                depends_on=[certificate],
            ),
        )
        validation_records.append(record)

    # Wait for certificate validation
    cert_validation = aws.acm.CertificateValidation(
        f"{stack_name}-cert-validation",
        certificate_arn=certificate.arn,
        validation_record_fqdns=[record.fqdn for record in validation_records],
        opts=ResourceOptions(
            depends_on=validation_records,
        ),
    )

    # Create custom domain name for API Gateway
    custom_domain = aws.apigateway.DomainName(
        f"{stack_name}-domain",
        domain_name=domain,
        regional_certificate_arn=certificate.arn,
        endpoint_configuration=aws.apigateway.DomainNameEndpointConfigurationArgs(
            types="REGIONAL",
        ),
        tags=tags,
        opts=ResourceOptions(
            depends_on=[cert_validation],
        ),
    )

    # Create base path mapping
    base_path_mapping = aws.apigateway.BasePathMapping(
        f"{stack_name}-base-path",
        rest_api=api_id,
        stage_name=environment,
        domain_name=custom_domain.domain_name,
        opts=ResourceOptions(
            depends_on=[custom_domain],
        ),
    )

    # Create Route53 A record pointing to API Gateway custom domain
    api_record = aws.route53.Record(
        f"{stack_name}-api-record",
        zone_id=zone.zone_id,
        name=domain,
        type="A",
        aliases=[aws.route53.RecordAliasArgs(
            name=custom_domain.regional_domain_name,
            zone_id=custom_domain.regional_zone_id,
            evaluate_target_health=True,
        )],
        opts=ResourceOptions(
            depends_on=[custom_domain],
        ),
    )

    return {
        "zone": zone,
        "certificate": certificate,
        "cert_validation": cert_validation,
        "custom_domain": custom_domain,
        "base_path_mapping": base_path_mapping,
        "api_record": api_record,
        "domain_name": domain,
        "certificate_arn": certificate.arn,
    }
