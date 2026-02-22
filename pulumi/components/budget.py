# Copyright (c) 2025 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

"""
AWS Budget component for TrailLens AI infrastructure.

This component creates:
- SNS topic for budget alerts
- Email subscription for notifications
- AWS Budget with $75/month threshold for Amazon Bedrock
- Alerts at 80% and 100% of budget
- Forecast alert at 100%
"""

import pulumi
import pulumi_aws as aws


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

    # Create SNS topic for budget alerts
    budget_topic = aws.sns.Topic(
        f"{stack_name}-budget-alerts",
        name=f"{stack_name}-budget-alerts",
        display_name="TrailLens AI Budget Alerts",
        tags={**tags, "Name": f"{stack_name}-budget-alerts"},
    )

    # Subscribe email to SNS topic
    email_subscription = aws.sns.TopicSubscription(
        f"{stack_name}-budget-email",
        topic=budget_topic.arn,
        protocol="email",
        endpoint=email,
    )

    # Create AWS Budget for Bedrock
    bedrock_budget = aws.budgets.Budget(
        f"{stack_name}-bedrock-budget",
        budget_type="COST",
        limit_amount="75",
        limit_unit="USD",
        time_unit="MONTHLY",
        cost_filters=[
            aws.budgets.BudgetCostFilterArgs(
                name="Service",
                values=["Amazon Bedrock"],
            ),
        ],
        notifications=[
            # Alert at 80% actual spend
            aws.budgets.BudgetNotificationArgs(
                comparison_operator="GREATER_THAN",
                threshold=80,
                threshold_type="PERCENTAGE",
                notification_type="ACTUAL",
                subscriber_sns_topic_arns=[budget_topic.arn],
            ),
            # Alert at 100% actual spend
            aws.budgets.BudgetNotificationArgs(
                comparison_operator="GREATER_THAN",
                threshold=100,
                threshold_type="PERCENTAGE",
                notification_type="ACTUAL",
                subscriber_sns_topic_arns=[budget_topic.arn],
            ),
            # Alert at 100% forecasted spend
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
    pulumi.log.info("  Budget: $75/month for Amazon Bedrock")
    pulumi.log.info("  Alerts: 80%, 100% (actual), 100% (forecast)")
    pulumi.log.info(f"  Email: {email}")

    return {
        "budget_topic": budget_topic,
        "budget_topic_arn": budget_topic.arn,
        "email_subscription": email_subscription,
        "bedrock_budget": bedrock_budget,
        "budget_id": bedrock_budget.id,
    }
