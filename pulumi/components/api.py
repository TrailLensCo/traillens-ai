# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

"""
API Gateway component for Bedrock proxy.

This component creates an API Gateway that proxies requests to AWS Bedrock.
"""

import pulumi
import pulumi_aws as aws


def create_api_stack(environment, project_name, bedrock_role_arn, log_group_arn, tags):
    """
    Create API Gateway stack for Bedrock proxy.

    Args:
        environment: The environment (dev or prod).
        project_name: The project name.
        bedrock_role_arn: ARN of the Bedrock IAM role.
        log_group_arn: ARN of the CloudWatch log group.
        tags: Resource tags.

    Returns:
        dict: Dictionary containing API Gateway resources.
    """
    stack_name = f"{project_name}-ai-{environment}"

    pulumi.log.info(f"Creating API Gateway stack: {stack_name}")

    # Create REST API
    api = aws.apigateway.RestApi(
        f"{stack_name}-api",
        name=f"{stack_name}-bedrock-api",
        description=f"Bedrock API Gateway for {environment}",
        endpoint_configuration=aws.apigateway.RestApiEndpointConfigurationArgs(
            types="REGIONAL",
        ),
        tags=tags,
    )

    # Create API Gateway account for CloudWatch logging
    api_account = aws.apigateway.Account(
        f"{stack_name}-api-account",
        cloudwatch_role_arn=bedrock_role_arn,
    )

    # Create deployment
    deployment = aws.apigateway.Deployment(
        f"{stack_name}-deployment",
        rest_api=api.id,
        opts=pulumi.ResourceOptions(depends_on=[api]),
    )

    # Create stage
    stage = aws.apigateway.Stage(
        f"{stack_name}-stage",
        deployment=deployment.id,
        rest_api=api.id,
        stage_name=environment,
        access_log_settings=aws.apigateway.StageAccessLogSettingsArgs(
            destination_arn=log_group_arn,
            format='$context.requestId $context.extendedRequestId $context.identity.sourceIp $context.requestTime $context.httpMethod $context.routeKey $context.status $context.protocol $context.responseLength',
        ),
        tags=tags,
    )

    # Export API endpoint
    api_endpoint = pulumi.Output.concat("https://", api.id, ".execute-api.ca-central-1.amazonaws.com/", stage.stage_name)

    return {
        "api": api,
        "deployment": deployment,
        "stage": stage,
        "api_endpoint": api_endpoint,
        "api_id": api.id,
    }
