# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

"""
AWS Bedrock IAM component for TrailLens AI infrastructure.

This component deploys:
- IAM user for Bedrock access
- Access keys for authentication
- Multi-region Bedrock policies:
  - Claude Opus 4.6, Sonnet 4.6, Sonnet 4.5, Haiku 4.5 (ca-central-1)
  - Meta Llama 3 70B Instruct (ca-central-1)
  - Amazon Titan Embed Text V2 (ca-central-1)
  - Cohere Rerank V3.5 (ca-central-1)
  - Moonshot Kimi K2.5 (us-east-1)
  - Amazon Titan Image Generator V2 (us-east-1)
"""

import json

import pulumi_aws as aws

import pulumi


def create_bedrock_iam_stack(project_name, region, tags):
    """
    Create AWS Bedrock IAM stack for multi-region API access.

    Creates a simplified IAM setup for single developer use with support
    for Claude text models, Llama 3, embeddings, and reranking in
    ca-central-1, plus Kimi K2.5 and image generation in us-east-1.

    Args:
        project_name: The project name.
        region: Primary AWS region (ca-central-1).
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

    # IAM policy covering all supported Bedrock models.
    # Supports: Opus 4.6, Sonnet 4.6, Sonnet 4.5, Haiku 4.5 (ca-central-1)
    #           Meta Llama 3 70B Instruct (ca-central-1)
    #           Titan Embed Text V2 (ca-central-1)
    #           Cohere Rerank V3.5 (ca-central-1)
    #           Moonshot Kimi K2.5 (us-east-1)
    #           Titan Image Generator V2 (us-east-1)
    #
    # NOTE: aws.iam.UserPolicy (inline) has a hard 2048-byte limit.
    # Use a managed policy (aws.iam.Policy) instead — limit is 6144 bytes.
    bedrock_managed_policy = aws.iam.Policy(
        f"{stack_name}-bedrock-policy",
        name=f"{stack_name}-bedrock-policy",
        description="Bedrock model access policy for TrailLens AI",
        policy=json.dumps(
            {
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
                            f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-opus-4-6-v1",
                            # Sonnet 4.6
                            f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-sonnet-4-6",
                            # Sonnet 4.5
                            f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0",
                            # Haiku 4.5
                            f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
                            # Wildcard for future Claude versions
                            f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude*",
                        ],
                    },
                    {
                        "Sid": "BedrockInferenceProfileAccess",
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel",
                            "bedrock:InvokeModelWithResponseStream",
                        ],
                        "Resource": [
                            # Inference profiles (required for 4.6 models)
                            # All regions — profiles route across regions
                            "arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude-*",
                            "arn:aws:bedrock:*:*:inference-profile/global.anthropic.claude-*",
                            # Underlying foundation models in all regions
                            "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
                        ],
                    },
                    {
                        "Sid": "BedrockImageModelAccess",
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel",
                        ],
                        "Resource": [
                            # Titan Image Generator V2 (us-east-1 only)
                            "arn:aws:bedrock:us-east-1::foundation-model"
                            "/amazon.titan-image-generator-v2:0",
                        ],
                    },
                    {
                        "Sid": "BedrockEmbeddingModelAccess",
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel",
                        ],
                        "Resource": [
                            # Titan Embed Text V2 (ca-central-1)
                            f"arn:aws:bedrock:{region}::foundation-model"
                            f"/amazon.titan-embed-text-v2:0",
                        ],
                    },
                    {
                        "Sid": "BedrockRerankModelAccess",
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel",
                        ],
                        "Resource": [
                            # Cohere Rerank V3.5 (ca-central-1)
                            f"arn:aws:bedrock:{region}::foundation-model"
                            f"/cohere.rerank-v3-5:0",
                        ],
                    },
                    {
                        "Sid": "BedrockRerankAccess",
                        "Effect": "Allow",
                        "Action": ["bedrock:Rerank"],
                        # Rerank action requires wildcard resource
                        "Resource": "*",
                    },
                    {
                        "Sid": "BedrockLlama3Access",
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel",
                            "bedrock:InvokeModelWithResponseStream",
                        ],
                        "Resource": [
                            # Meta Llama 3 70B Instruct (ca-central-1)
                            f"arn:aws:bedrock:{region}::foundation-model"
                            f"/meta.llama3-70b-instruct-v1:0",
                        ],
                    },
                    {
                        "Sid": "BedrockKimiModelAccess",
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel",
                            "bedrock:InvokeModelWithResponseStream",
                        ],
                        "Resource": [
                            # Kimi K2.5 (us-east-1 only)
                            "arn:aws:bedrock:us-east-1::foundation-model"
                            "/moonshotai.kimi-k2.5",
                        ],
                    },
                    {
                        "Sid": "BedrockModelList",
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:ListFoundationModels",
                            "bedrock:GetFoundationModel",
                        ],
                        "Resource": "*",
                    },
                    {
                        "Sid": "AWSMarketplaceAccess",
                        "Effect": "Allow",
                        "Action": [
                            "aws-marketplace:ViewSubscriptions",
                            "aws-marketplace:Subscribe",
                        ],
                        "Resource": "*",
                    },
                ],
            }
        ),
    )

    # Attach the managed policy to the user.
    bedrock_policy = aws.iam.UserPolicyAttachment(
        f"{stack_name}-bedrock-policy-attachment",
        user=bedrock_user.name,
        policy_arn=bedrock_managed_policy.arn,
    )

    pulumi.log.info("✓ IAM user and policies created")
    bedrock_user.name.apply(lambda name: pulumi.log.info(f"  User: {name}"))
    pulumi.log.info(
        "  Models: Opus 4.6, Sonnet 4.6, Sonnet 4.5, Haiku 4.5, "
        "Llama 3 70B, Titan Embed V2, Cohere Rerank V3.5, Kimi K2.5"
    )

    # Return resources
    return {
        "iam_user": bedrock_user,
        "iam_user_name": bedrock_user.name,
        "iam_user_arn": bedrock_user.arn,
        "bedrock_managed_policy": bedrock_managed_policy,
        "bedrock_policy": bedrock_policy,
        "access_key_id": access_key.id,
        "secret_access_key": access_key.secret,
    }
