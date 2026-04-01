# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

"""
AWS Budget component for TrailLens AI infrastructure.

This component creates:
- SNS topic for budget alerts with correct budgets.amazonaws.com publish policy
- Email subscription for notifications
- AWS Budget with $100/month threshold covering ALL Bedrock-billed services
- Alerts at 40%, 60%, 80%, 100%, 150%, and 200% of budget (actual spend)
- Forecast alert at 100%
- Cost Anomaly Detection subscription for daily digest above $200 impact

Important: AWS bills Claude and other Bedrock-hosted models as separate
top-level services (e.g. "Claude Sonnet 4.6 (Amazon Bedrock Edition)")
rather than under the "Amazon Bedrock" service name. The budget must
therefore use NO service filter so it captures all Bedrock-related spend.

The SNS topic policy must explicitly grant budgets.amazonaws.com permission
to publish, otherwise budget notifications are silently dropped.
"""

import json

import pulumi_aws as aws

import pulumi


def create_budget_stack(project_name, email, tags):
    """
    Create AWS Budget stack for Bedrock cost monitoring.

    Args:
        project_name: The project name.
        email: Email address for budget alerts.
        tags: Resource tags.

    Returns:
        dict: Dictionary containing budget resources.
    """
    stack_name = f"{project_name}-ai"

    pulumi.log.info(f"Creating Budget stack: {stack_name}")

    # Resolve the current account ID for use in policies.
    account_id = aws.get_caller_identity().account_id

    # Create SNS topic for budget alerts.
    budget_topic = aws.sns.Topic(
        f"{stack_name}-budget-alerts",
        name=f"{stack_name}-budget-alerts",
        display_name="TrailLens AI Budget Alerts",
        tags={**tags, "Name": f"{stack_name}-budget-alerts"},
    )

    # Attach a resource policy granting both budgets.amazonaws.com and
    # costalerts.amazonaws.com permission to publish to this topic.
    # Only one TopicPolicy resource is allowed per SNS topic — both service
    # principals must be in the same policy document.
    budget_topic_policy = aws.sns.TopicPolicy(
        f"{stack_name}-budget-topic-policy",
        arn=budget_topic.arn,
        policy=budget_topic.arn.apply(
            lambda arn: json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "AllowBudgetsPublish",
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "budgets.amazonaws.com",
                            },
                            "Action": "SNS:Publish",
                            "Resource": arn,
                            "Condition": {
                                "StringEquals": {
                                    "aws:SourceAccount": account_id,
                                },
                            },
                        },
                        {
                            "Sid": "AllowCostExplorerPublish",
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "costalerts.amazonaws.com",
                            },
                            "Action": "SNS:Publish",
                            "Resource": arn,
                            "Condition": {
                                "StringEquals": {
                                    "aws:SourceAccount": account_id,
                                },
                            },
                        },
                        {
                            "Sid": "AllowAccountOwner",
                            "Effect": "Allow",
                            "Principal": {
                                "AWS": f"arn:aws:iam::{account_id}:root",
                            },
                            "Action": [
                                "SNS:GetTopicAttributes",
                                "SNS:SetTopicAttributes",
                                "SNS:AddPermission",
                                "SNS:RemovePermission",
                                "SNS:DeleteTopic",
                                "SNS:Subscribe",
                                "SNS:ListSubscriptionsByTopic",
                                "SNS:Publish",
                            ],
                            "Resource": arn,
                        },
                    ],
                }
            )
        ),
    )

    # Subscribe email to SNS topic.
    email_subscription = aws.sns.TopicSubscription(
        f"{stack_name}-budget-email",
        topic=budget_topic.arn,
        protocol="email",
        endpoint=email,
    )

    # Create AWS Budget covering ALL Bedrock-related services.
    #
    # AWS bills Claude models as separate top-level services with names like
    # "Claude Sonnet 4.6 (Amazon Bedrock Edition)".  Filtering on
    # Service = "Amazon Bedrock" only captures base infrastructure usage and
    # completely misses all Claude spend.  Using a LinkedAccount filter
    # instead ensures every Bedrock-related service is captured regardless
    # of how AWS names individual models in the future.
    bedrock_budget = aws.budgets.Budget(
        f"{stack_name}-bedrock-budget",
        budget_type="COST",
        limit_amount="100",
        limit_unit="USD",
        time_unit="MONTHLY",
        cost_filters=[
            aws.budgets.BudgetCostFilterArgs(
                name="LinkedAccount",
                values=[account_id],
            ),
        ],
        notifications=[
            # Early warning at 40% actual spend ($40)
            aws.budgets.BudgetNotificationArgs(
                comparison_operator="GREATER_THAN",
                threshold=40,
                threshold_type="PERCENTAGE",
                notification_type="ACTUAL",
                subscriber_sns_topic_arns=[budget_topic.arn],
            ),
            # Early warning at 60% actual spend ($60)
            aws.budgets.BudgetNotificationArgs(
                comparison_operator="GREATER_THAN",
                threshold=60,
                threshold_type="PERCENTAGE",
                notification_type="ACTUAL",
                subscriber_sns_topic_arns=[budget_topic.arn],
            ),
            # Alert at 80% actual spend ($80)
            aws.budgets.BudgetNotificationArgs(
                comparison_operator="GREATER_THAN",
                threshold=80,
                threshold_type="PERCENTAGE",
                notification_type="ACTUAL",
                subscriber_sns_topic_arns=[budget_topic.arn],
            ),
            # Alert at 100% actual spend ($100)
            aws.budgets.BudgetNotificationArgs(
                comparison_operator="GREATER_THAN",
                threshold=100,
                threshold_type="PERCENTAGE",
                notification_type="ACTUAL",
                subscriber_sns_topic_arns=[budget_topic.arn],
            ),
            # Critical alert at 150% actual spend ($150)
            aws.budgets.BudgetNotificationArgs(
                comparison_operator="GREATER_THAN",
                threshold=150,
                threshold_type="PERCENTAGE",
                notification_type="ACTUAL",
                subscriber_sns_topic_arns=[budget_topic.arn],
            ),
            # Severe overage alert at 200% actual spend ($200)
            aws.budgets.BudgetNotificationArgs(
                comparison_operator="GREATER_THAN",
                threshold=200,
                threshold_type="PERCENTAGE",
                notification_type="ACTUAL",
                subscriber_sns_topic_arns=[budget_topic.arn],
            ),
            # Forecast alert at 100% ($100 projected)
            aws.budgets.BudgetNotificationArgs(
                comparison_operator="GREATER_THAN",
                threshold=100,
                threshold_type="PERCENTAGE",
                notification_type="FORECASTED",
                subscriber_sns_topic_arns=[budget_topic.arn],
            ),
        ],
        tags={**tags, "Name": f"{stack_name}-bedrock-budget"},
    )

    pulumi.log.info("✓ Budget and alerts created")
    pulumi.log.info("  Budget: $100/month (all services, LinkedAccount filter)")
    pulumi.log.info("  Alerts: 40%, 60%, 80%, 100%, 150%, 200% (actual), 100% (forecast)")
    pulumi.log.info(f"  Email: {email}")

    # Cost Anomaly Detection — immediate SNS subscription.
    #
    # The existing Default-Services-Monitor (DIMENSIONAL/SERVICE) already
    # tracks all services including Bedrock-billed Claude models.  We attach
    # a subscription to it that sends an immediate alert to the same SNS
    # topic whenever the total anomaly impact exceeds $50.
    #
    # NOTE: AWS only allows DAILY/WEEKLY frequency for EMAIL subscribers.
    # SNS subscribers MUST use IMMEDIATE frequency — any other value raises
    # a ValidationException (StatusCode 400).
    anomaly_subscription = aws.costexplorer.AnomalySubscription(
        f"{stack_name}-anomaly-subscription",
        name=f"{stack_name}-anomaly-alerts",
        frequency="IMMEDIATE",
        monitor_arn_lists=[
            # Reuse the account-level Default-Services-Monitor so we do not
            # create a duplicate monitor resource.
            "arn:aws:ce::{}:anomalymonitor/7535fc5c-ccec-4fbb-95c6-fb65fd6ec6ca".format(account_id),
        ],
        subscribers=[
            aws.costexplorer.AnomalySubscriptionSubscriberArgs(
                type="SNS",
                address=budget_topic.arn,
            ),
        ],
        threshold_expression=(
            aws.costexplorer.AnomalySubscriptionThresholdExpressionArgs(
                dimension=aws.costexplorer.AnomalySubscriptionThresholdExpressionDimensionArgs(
                    key="ANOMALY_TOTAL_IMPACT_ABSOLUTE",
                    match_options=["GREATER_THAN_OR_EQUAL"],
                    values=["50"],
                ),
            )
        ),
        tags={**tags, "Name": f"{stack_name}-anomaly-alerts"},
    )

    pulumi.log.info("✓ Cost Anomaly Detection subscription created")
    pulumi.log.info("  Frequency: immediate SNS alert when impact > $50")

    return {
        "budget_topic": budget_topic,
        "budget_topic_arn": budget_topic.arn,
        "budget_topic_policy": budget_topic_policy,
        "email_subscription": email_subscription,
        "bedrock_budget": bedrock_budget,
        "budget_id": bedrock_budget.id,
        "anomaly_subscription": anomaly_subscription,
    }
