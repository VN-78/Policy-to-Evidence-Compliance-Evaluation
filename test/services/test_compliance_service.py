import pytest
from pydantic import JsonValue

from app.db.session import AsyncSessionLocal, init_db
from app.models.schema import (
    ComplianceScanResponse,
    ComplianceStatus,
    EvidenceAsset,
    EvidencePayload,
    PolicyIngestionResponse,
)
from app.services.compliance_service import ComplianceOrchestrationService

POLICY_PDF_TEXT: str = """
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


@pytest.mark.anyio
async def test_compliance_service_end_to_end_pipeline() -> None:
    """
    Tests the complete end-to-end compliance orchestration pipeline:
    1. Ingest policy text -> Gemini extraction -> persist in PostgreSQL -> returns PolicyIngestionResponse.
    2. Re-ingest exact policy text -> verifies SHA-256 deduplication cache hit returns same policy_id.
    3. Evaluate non-compliant evidence (CPU 92%) against DB rules -> assert NON_COMPLIANT.
    4. Evaluate compliant evidence (CPU 70%) against DB rules -> assert COMPLIANT.
    """
    await init_db()
    async with AsyncSessionLocal() as session:
        service = ComplianceOrchestrationService(session)

        # 1. Ingest & Persist Policy into PostgreSQL
        extracted_resp = await service.ingest_policy_document(POLICY_PDF_TEXT)
        assert isinstance(extracted_resp, PolicyIngestionResponse)
        assert extracted_resp.policy_id is not None
        assert len(extracted_resp.rules) >= 1

        # 2. Test SHA-256 Deduplication (Cache Hit)
        cached_resp = await service.ingest_policy_document(POLICY_PDF_TEXT)
        assert isinstance(cached_resp, PolicyIngestionResponse)
        assert cached_resp.policy_id == extracted_resp.policy_id
        assert len(cached_resp.rules) == len(extracted_resp.rules)

        # Locate the CPU utilization rule
        rule = next(
            (r for r in extracted_resp.rules if "cpu" in r.target_metric.lower()),
            extracted_resp.rules[0],
        )

        # 3. Evaluate Failing Evidence (CPU 92% > 85%) scoped to policy_id
        metrics_failing: dict[str, JsonValue] = {
            rule.target_metric: 92,
            "auto_scaling_enabled": True,
        }
        if rule.pre_condition:
            metrics_failing[rule.pre_condition.target_metric] = rule.pre_condition.threshold_value

        failing_evidence = EvidencePayload(
            scan_id="SCAN-2026-0812-FAIL",
            environment="production",
            assets=[
                EvidenceAsset(
                    asset_id="prod-db-server-01",
                    asset_type=rule.target_asset_type,
                    metrics=metrics_failing,
                )
            ],
        )

        scan_fail: ComplianceScanResponse = await service.evaluate_evidence(
            evidence=failing_evidence,
            policy_id=extracted_resp.policy_id,
        )
        assert isinstance(scan_fail, ComplianceScanResponse)
        assert scan_fail.overall_status == ComplianceStatus.NON_COMPLIANT
        assert scan_fail.non_compliant_assets_count == 1
        assert len(scan_fail.asset_results) == 1
        assert scan_fail.asset_results[0].overall_status == ComplianceStatus.NON_COMPLIANT

        # 4. Evaluate Passing Evidence (CPU 70% < 85%) scoped to policy_id
        metrics_passing: dict[str, JsonValue] = {
            rule.target_metric: 70,
            "auto_scaling_enabled": True,
        }
        if rule.pre_condition:
            metrics_passing[rule.pre_condition.target_metric] = rule.pre_condition.threshold_value

        passing_evidence = EvidencePayload(
            scan_id="SCAN-2026-0812-PASS",
            environment="production",
            assets=[
                EvidenceAsset(
                    asset_id="prod-db-server-02",
                    asset_type=rule.target_asset_type,
                    metrics=metrics_passing,
                )
            ],
        )

        scan_pass: ComplianceScanResponse = await service.evaluate_evidence(
            evidence=passing_evidence,
            policy_id=extracted_resp.policy_id,
        )
        assert isinstance(scan_pass, ComplianceScanResponse)
        assert scan_pass.overall_status == ComplianceStatus.COMPLIANT
        assert scan_pass.compliant_assets_count == 1
