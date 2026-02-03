# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

"""
AWS Bedrock component for TrailLens AI infrastructure.

This component deploys:
- IAM roles and policies for Bedrock access
- API Gateway for Bedrock proxy
- Lambda function for request handling
"""

import json

import pulumi
import pulumi_aws as aws


def create_bedrock_stack(environment, project_name, bedrock_model_id, tags):
    """
    Create AWS Bedrock stack with Claude Sonnet 4.5 access.

    Args:
        environment: The environment (dev or prod).
        project_name: The project name.
        bedrock_model_id: The Bedrock model ID to use.
        tags: Resource tags.

    Returns:
        dict: Dictionary containing Bedrock resources.
    """
    stack_name = f"{project_name}-ai-{environment}"

    pulumi.log.info(f"Creating Bedrock stack: {stack_name}")

    # Create IAM role for Bedrock access
    bedrock_role = aws.iam.Role(
        f"{stack_name}-bedrock-role",
        assume_role_policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "sts:AssumeRole",
                "Effect": "Allow",
                "Principal": {
                    "Service": ["lambda.amazonaws.com", "apigateway.amazonaws.com"]
                }
            }]
        }),
        tags={**tags, "Name": f"{stack_name}-bedrock-role"},
    )

    # Create IAM policy for Bedrock model access
    bedrock_policy = aws.iam.RolePolicy(
        f"{stack_name}-bedrock-policy",
        role=bedrock_role.id,
        policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream",
                        "bedrock:ListFoundationModels",
                        "bedrock:GetFoundationModel",
                    ],
                    "Resource": [
                        f"arn:aws:bedrock:*::foundation-model/{bedrock_model_id}",
                        "arn:aws:bedrock:*::foundation-model/anthropic.claude*",
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                }
            ]
        }),
    )

    # Create Lambda execution role
    lambda_role = aws.iam.Role(
        f"{stack_name}-lambda-role",
        assume_role_policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "sts:AssumeRole",
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                }
            }]
        }),
        tags={**tags, "Name": f"{stack_name}-lambda-role"},
    )

    # Attach basic Lambda execution policy
    lambda_basic_execution = aws.iam.RolePolicyAttachment(
        f"{stack_name}-lambda-basic-execution",
        role=lambda_role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )

    # Create Lambda policy for Bedrock access
    lambda_bedrock_policy = aws.iam.RolePolicy(
        f"{stack_name}-lambda-bedrock-policy",
        role=lambda_role.id,
        policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                "Resource": [
                    f"arn:aws:bedrock:*::foundation-model/{bedrock_model_id}",
                    "arn:aws:bedrock:*::foundation-model/anthropic.claude*",
                ]
            }]
        }),
    )

    # Create CloudWatch log group for API Gateway
    api_log_group = aws.cloudwatch.LogGroup(
        f"{stack_name}-api-logs",
        name=f"/aws/apigateway/{stack_name}",
        retention_in_days=7,
        tags=tags,
    )

    # Return resources
    return {
        "bedrock_role": bedrock_role,
        "bedrock_policy": bedrock_policy,
        "lambda_role": lambda_role,
        "lambda_basic_execution": lambda_basic_execution,
        "lambda_bedrock_policy": lambda_bedrock_policy,
        "api_log_group": api_log_group,
        "bedrock_role_arn": bedrock_role.arn,
        "lambda_role_arn": lambda_role.arn,
        "model_id": bedrock_model_id,
    }
