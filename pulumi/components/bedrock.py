# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

"""
AWS Bedrock IAM component for TrailLens AI infrastructure.

This component deploys:
- IAM user for Bedrock access
- Access keys for authentication
- Policies for Claude Opus 4.6, Sonnet 4.5, and Haiku 4.5
"""

import json

import pulumi
import pulumi_aws as aws


def create_bedrock_iam_stack(project_name, region, tags):
    """
    Create AWS Bedrock IAM stack for direct API access.

    This creates a simplified IAM setup for single developer use with support
    for all three Claude models (Opus, Sonnet, Haiku).

    Args:
        project_name: The project name.
        region: AWS region for Bedrock.
        tags: Resource tags.

    Returns:
        dict: Dictionary containing IAM resources and credentials.
    """
    stack_name = f"{project_name}-ai"

    pulumi.log.info(f"Creating Bedrock IAM stack: {stack_name}")

    # Create IAM user for Bedrock access
    bedrock_user = aws.iam.User(
        f"{stack_name}-bedrock-user",
        name=f"{stack_name}-bedrock-user",
        tags={**tags, "Name": f"{stack_name}-bedrock-user"},
    )

    # Create access key for the user
    access_key = aws.iam.AccessKey(
        f"{stack_name}-access-key",
        user=bedrock_user.name,
    )

    # Create IAM policy for all Claude models
    # Supports: Opus 4.6, Sonnet 4.5, Haiku 4.5
    bedrock_policy = aws.iam.UserPolicy(
        f"{stack_name}-bedrock-policy",
        user=bedrock_user.name,
        policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "BedrockModelAccess",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream",
                    ],
                    "Resource": [
                        # Opus 4.6
                        f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-opus-4-6",
                        # Sonnet 4.5
                        f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-sonnet-4-5-v2:0",
                        # Haiku 4.5
                        f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-haiku-4-5-20251001:0",
                        # Allow all Claude models (for future versions)
                        f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude*",
                    ]
                },
                {
                    "Sid": "BedrockModelList",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:ListFoundationModels",
                        "bedrock:GetFoundationModel",
                    ],
                    "Resource": "*"
                }
            ]
        }),
    )

    pulumi.log.info("✓ IAM user and policies created")
    pulumi.log.info(f"  User: {bedrock_user.name}")
    pulumi.log.info("  Models: Opus 4.6, Sonnet 4.5, Haiku 4.5")

    # Return resources
    return {
        "iam_user": bedrock_user,
        "iam_user_name": bedrock_user.name,
        "iam_user_arn": bedrock_user.arn,
        "bedrock_policy": bedrock_policy,
        "access_key_id": access_key.id,
        "secret_access_key": access_key.secret,
    }
