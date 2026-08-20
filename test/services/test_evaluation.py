import pytest

from app.models.schema import (
    ComparisonOperator,
    ComplianceStatus,
    EvidenceAsset,
    ExtractedRuleBase,
    PreCondition,
)
from app.services.evaluation import evaluate_rule

# =====================================================================
# Mock Rules (The data normally fetched from PostgreSQL)
# =====================================================================

RULE_CPU = ExtractedRuleBase(
    control_id="CAP-001",
    title="Max CPU Limit",
    target_asset_type="database_server",
    target_metric="cpu_utilization",
    operator=ComparisonOperator.LT,
    threshold_value=85,
    source_clause="CPU utilization below 85%.",
)

RULE_ENCRYPTION = ExtractedRuleBase(
    control_id="SEC-002",
    title="Require Storage Encryption",
    target_asset_type="object_storage",
    target_metric="encryption_enabled",
    operator=ComparisonOperator.EQ,
    threshold_value=True,
    source_clause="All object storage must have encryption enabled.",
)

# =====================================================================
# Mock Interdependent Rule
# =====================================================================

RULE_CONDITIONAL_ENCRYPTION = ExtractedRuleBase(
    control_id="SEC-003",
    title="Public Database Encryption",
    target_asset_type="database_server",
    target_metric="encryption_enabled",
    operator=ComparisonOperator.EQ,
    threshold_value=True,
    source_clause="If a database is publicly accessible, it must have encryption enabled.",
    pre_condition=PreCondition(
        target_metric="is_publicly_accessible",
        operator=ComparisonOperator.EQ,
        threshold_value=True,
    ),
)

# =====================================================================
# Test Cases
# =====================================================================


@pytest.mark.parametrize(
    ("rule", "asset_data", "expected_status"),
    [
        # 1. Standard Success: CPU is 70 (< 85)
        (
            RULE_CPU,
            EvidenceAsset(
                asset_id="db-01",
                asset_type="database_server",
                metrics={"cpu_utilization": 70},
            ),
            ComplianceStatus.COMPLIANT,
        ),
        # 2. Standard Failure: CPU is 92 (Not < 85)
        (
            RULE_CPU,
            EvidenceAsset(
                asset_id="db-02",
                asset_type="database_server",
                metrics={"cpu_utilization": 92},
            ),
            ComplianceStatus.NON_COMPLIANT,
        ),
        # 3. Edge Case: Value exactly hits the threshold (85 is not < 85)
        (
            RULE_CPU,
            EvidenceAsset(
                asset_id="db-03",
                asset_type="database_server",
                metrics={"cpu_utilization": 85},
            ),
            ComplianceStatus.NON_COMPLIANT,
        ),
        # 4. Boolean Success: Encryption is True (== True)
        (
            RULE_ENCRYPTION,
            EvidenceAsset(
                asset_id="bucket-01",
                asset_type="object_storage",
                metrics={"encryption_enabled": True},
            ),
            ComplianceStatus.COMPLIANT,
        ),
        # 5. Asset Mismatch: Passing a load_balancer to a database rule
        (
            RULE_CPU,
            EvidenceAsset(
                asset_id="lb-01",
                asset_type="load_balancer",
                metrics={"cpu_utilization": 50},
            ),
            ComplianceStatus.NOT_APPLICABLE,
        ),
        # 6. Missing Metric: Asset matches, but metric is missing from JSON
        (
            RULE_CPU,
            EvidenceAsset(
                asset_id="db-04",
                asset_type="database_server",
                metrics={"memory_utilization": 60},  # CPU key is missing
            ),
            ComplianceStatus.UNKNOWN,
        ),
        # 7. Advanced: Pre-condition Met, Main Rule Fails
        # DB is public (True), but encryption is False -> NON_COMPLIANT
        (
            RULE_CONDITIONAL_ENCRYPTION,
            EvidenceAsset(
                asset_id="db-public-01",
                asset_type="database_server",
                metrics={"is_publicly_accessible": True, "encryption_enabled": False},
            ),
            ComplianceStatus.NON_COMPLIANT,
        ),
        # 8. Advanced: Pre-condition NOT Met, Main Rule Bypassed
        # DB is private (False). The rule doesn't apply -> NOT_APPLICABLE
        (
            RULE_CONDITIONAL_ENCRYPTION,
            EvidenceAsset(
                asset_id="db-private-01",
                asset_type="database_server",
                metrics={"is_publicly_accessible": False, "encryption_enabled": False},
            ),
            ComplianceStatus.NOT_APPLICABLE,
        ),
    ],
)
def test_evaluate_rule(
    rule: ExtractedRuleBase,
    asset_data: EvidenceAsset,
    expected_status: ComplianceStatus,
) -> None:
    """
    Tests the deterministic engine against various operators, data types,
    and missing evidence edge cases.
    """
    result = evaluate_rule(rule=rule, asset=asset_data)

    assert result.status == expected_status
    assert result.control_id == rule.control_id
    assert result.target_metric == rule.target_metric
