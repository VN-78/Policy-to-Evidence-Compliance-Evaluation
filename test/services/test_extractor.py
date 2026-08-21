import pytest

from app.core.llm import client
from app.models.schema import (
    ComparisonOperator,
    ComplianceStatus,
    EvidenceAsset,
    ExtractedRuleBase,
    PolicyExtractionPayload,
)
from app.services.evaluation import evaluate_rule
from app.services.extractor import (
    _clean_json_markdown,
    extract_rules_from_text,
)

# =====================================================================
# Concrete Policy Texts for Testing
# =====================================================================

# 1. Primary Policy Snippet directly from Flyyy.ai Problem Statement (PDF)
POLICY_PDF_COMPUTE_CAPACITY: str = """
We maintain suficient production computing capacity to ensure reliable service 
delivery and to prevent unexpected outages. As part of our internal infrastructure 
governance rules, we continuously monitor compute resources across our production 
application and database servers, including CPU utilization and related capacity 
indicators. Our production application and database servers are required to operate 
with CPU utilization below 85% under normal operating conditions. We also keep auto-
scaling enabled for applicable production workloads so that additional compute 
capacity can be provisioned automatically when demand increases. We review, 
document, and remediate any sustained capacity threshold breach or disabled auto-
scaling confguration through our established incident and change management 
processes.
"""

# 2. Storage Encryption Policy (Mirroring RULE_ENCRYPTION in test_evaluation.py)
POLICY_STORAGE_ENCRYPTION: str = """
All object storage buckets in our cloud infrastructure must have encryption enabled 
at rest to ensure sensitive data is protected against unauthorized access.
"""

# 3. Conditional Security Policy (Mirroring RULE_CONDITIONAL_ENCRYPTION in test_evaluation.py)
POLICY_CONDITIONAL_SECURITY: str = """
Database servers must follow strict baseline security controls. If a database server is configured 
to be publicly accessible, it must have encryption enabled to protect corporate assets.
"""


# =====================================================================
# Unit & Activation Tests
# =====================================================================


def test_clean_json_markdown() -> None:
    """Verifies that markdown code fence wrappers (```json ... ```) are stripped properly."""
    raw_with_fence = '```json\n{"policy_name": "Test", "rules": []}\n```'
    assert _clean_json_markdown(raw_with_fence) == '{"policy_name": "Test", "rules": []}'

    raw_with_plain_fence = '```\n{"policy_name": "Test", "rules": []}\n```'
    assert _clean_json_markdown(raw_with_plain_fence) == '{"policy_name": "Test", "rules": []}'

    raw_clean = '  {"policy_name": "Test", "rules": []}  '
    assert _clean_json_markdown(raw_clean) == '{"policy_name": "Test", "rules": []}'


@pytest.mark.anyio
async def test_llm_client_activation() -> None:
    """
    Tests whether the OpenRouter LLM client is activated, authenticated,
    and responsive using the configured API key.
    """
    assert client.api_key, "OpenRouter API Key is missing or empty in configuration."
    assert "openrouter.ai" in str(client.base_url), "Base URL must point to OpenRouter."

    # Verify model completion works live
    minimal_policy = "Database servers must operate with CPU utilization below 90%."
    result: PolicyExtractionPayload = await extract_rules_from_text(minimal_policy)

    assert isinstance(result, PolicyExtractionPayload)
    assert len(result.rules) > 0
    assert result.rules[0].threshold_value == 90 or "cpu" in result.rules[0].target_metric.lower()


# =====================================================================
# End-to-End Live LLM Extraction & Evaluation Tests
# =====================================================================


@pytest.mark.anyio
async def test_extract_rules_pdf_capacity_policy_and_evaluation() -> None:
    """
    Tests live LLM extraction against the exact Flyyy.ai PDF policy snippet
    and evaluates the extracted rule against the raw platform evidence JSON.
    """
    # 1. Feed unstructured policy paragraph into LLM extractor
    payload: PolicyExtractionPayload = await extract_rules_from_text(POLICY_PDF_COMPUTE_CAPACITY)

    # 2. Verify structured schema contract
    assert isinstance(payload, PolicyExtractionPayload)
    assert payload.policy_name, "Extracted policy must have a non-empty name"
    assert len(payload.rules) >= 1, "Extracted payload must contain at least one compliance rule"

    # 3. Locate the CPU utilization rule
    cpu_rule: ExtractedRuleBase | None = next(
        (r for r in payload.rules if "cpu" in r.target_metric.lower()),
        None,
    )
    assert cpu_rule is not None, "LLM must extract a rule targeting CPU utilization"
    assert cpu_rule.threshold_value == 85
    assert cpu_rule.operator in (ComparisonOperator.LT, ComparisonOperator.LTE, "<", "<=")

    # 4. Evaluate against the raw evidence asset from the problem statement:
    # Asset has CPU utilization = 92% -> Expected Status: Non-Compliant
    evidence_failing = EvidenceAsset(
        asset_id="prod-db-server-01",
        asset_type=cpu_rule.target_asset_type,
        metrics={cpu_rule.target_metric: 92, "auto_scaling_enabled": True},
    )

    verdict_failing = evaluate_rule(rule=cpu_rule, asset=evidence_failing)
    assert verdict_failing.status == ComplianceStatus.NON_COMPLIANT
    assert "92" in verdict_failing.audit_reasoning
    assert "85" in verdict_failing.audit_reasoning

    # 5. Verify a passing asset with CPU utilization = 70% -> Expected Status: Compliant
    evidence_passing = EvidenceAsset(
        asset_id="prod-db-server-02",
        asset_type=cpu_rule.target_asset_type,
        metrics={cpu_rule.target_metric: 70, "auto_scaling_enabled": True},
    )

    verdict_passing = evaluate_rule(rule=cpu_rule, asset=evidence_passing)
    assert verdict_passing.status == ComplianceStatus.COMPLIANT

    # 6. Verify asset type mismatch returns NOT_APPLICABLE (following test_evaluation.py)
    evidence_mismatch = EvidenceAsset(
        asset_id="unrelated-lb-01",
        asset_type="load_balancer_mismatch",
        metrics={cpu_rule.target_metric: 50},
    )
    verdict_mismatch = evaluate_rule(rule=cpu_rule, asset=evidence_mismatch)
    assert verdict_mismatch.status == ComplianceStatus.NOT_APPLICABLE


@pytest.mark.anyio
async def test_extract_rules_storage_encryption_policy_and_evaluation() -> None:
    """
    Tests live LLM extraction for object storage encryption policy
    and evaluates the extracted rule against compliant and non-compliant assets.
    """
    # 1. Extract rules from policy text
    payload: PolicyExtractionPayload = await extract_rules_from_text(POLICY_STORAGE_ENCRYPTION)

    assert isinstance(payload, PolicyExtractionPayload)
    assert len(payload.rules) >= 1

    # 2. Locate encryption rule
    enc_rule: ExtractedRuleBase | None = next(
        (r for r in payload.rules if "encrypt" in r.target_metric.lower()),
        None,
    )
    assert enc_rule is not None, "LLM must extract an encryption rule"
    assert enc_rule.operator in (ComparisonOperator.EQ, "==")

    # 3. Evaluate against compliant storage asset
    storage_compliant = EvidenceAsset(
        asset_id="bucket-01",
        asset_type=enc_rule.target_asset_type,
        metrics={enc_rule.target_metric: True},
    )

    verdict_compliant = evaluate_rule(rule=enc_rule, asset=storage_compliant)
    assert verdict_compliant.status == ComplianceStatus.COMPLIANT

    # 4. Evaluate against non-compliant storage asset (encryption disabled)
    storage_non_compliant = EvidenceAsset(
        asset_id="bucket-02",
        asset_type=enc_rule.target_asset_type,
        metrics={enc_rule.target_metric: False},
    )

    verdict_non_compliant = evaluate_rule(rule=enc_rule, asset=storage_non_compliant)
    assert verdict_non_compliant.status == ComplianceStatus.NON_COMPLIANT


@pytest.mark.anyio
async def test_extract_rules_conditional_security_policy() -> None:
    """
    Tests live LLM extraction for conditional / interdependent database security policy.
    """
    payload: PolicyExtractionPayload = await extract_rules_from_text(POLICY_CONDITIONAL_SECURITY)

    assert isinstance(payload, PolicyExtractionPayload)
    assert len(payload.rules) >= 1

    for rule in payload.rules:
        assert isinstance(rule, ExtractedRuleBase)
        assert rule.control_id
        assert rule.target_metric
        assert rule.operator
