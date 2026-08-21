import json
import uuid
from pathlib import Path
from typing import cast

import pytest
from httpx import ASGITransport, AsyncClient, Response

from app.db.session import init_db
from app.main import app
from app.models.schema import ComplianceScanResponse, ComplianceStatus, PolicyIngestionResponse

DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "docs"
SAMPLE_PDF_PATH = DOCS_DIR / "sample-policy-1.pdf"
SAMPLE_EVIDENCE_PATH = DOCS_DIR / "sample-evidence-1.json"


@pytest.mark.anyio
async def test_healthcheck() -> None:
    """Verifies the /health endpoint responds with database status."""
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response: Response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        assert data.get("database") == "connected"


@pytest.mark.anyio
async def test_extract_policy_from_text() -> None:
    """Verifies plain text policy extraction via POST /api/v1/policies/extract-text."""
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", timeout=60.0) as ac:
        payload = {
            "policy_name": "Compute Capacity Policy",
            "raw_text": "Production database servers are required to maintain CPU utilization below 85% under normal operating conditions.",
        }
        response: Response = await ac.post("/api/v1/policies/extract-text", json=payload)
        assert response.status_code == 201
        data = response.json()
        parsed = PolicyIngestionResponse.model_validate(data)
        assert parsed.policy_id is not None
        assert parsed.policy_name
        assert len(parsed.rules) >= 1


@pytest.mark.anyio
async def test_upload_pdf_and_deduplication_cache() -> None:
    """
    Verifies PDF upload via POST /api/v1/policies/upload-pdf and subsequent
    SHA-256 deduplication cache hit on identical file re-upload.
    """
    await init_db()
    assert SAMPLE_PDF_PATH.exists(), f"Sample PDF missing at {SAMPLE_PDF_PATH}"
    pdf_bytes = SAMPLE_PDF_PATH.read_bytes()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", timeout=60.0) as ac:
        # 1. First upload (Cache Miss -> LLM Extraction & DB Save)
        files = {"file": ("sample-policy-1.pdf", pdf_bytes, "application/pdf")}
        resp1: Response = await ac.post("/api/v1/policies/upload-pdf", files=files)
        assert resp1.status_code == 201
        data1 = resp1.json()
        policy1 = PolicyIngestionResponse.model_validate(data1)
        assert policy1.policy_id is not None
        assert len(policy1.rules) >= 1

        # 2. Second upload with exact same bytes (Cache Hit -> Returns existing policy_id)
        files_cached = {"file": ("sample-policy-1.pdf", pdf_bytes, "application/pdf")}
        resp2: Response = await ac.post("/api/v1/policies/upload-pdf", files=files_cached)
        assert resp2.status_code == 201
        data2 = resp2.json()
        policy2 = PolicyIngestionResponse.model_validate(data2)
        assert policy2.policy_id == policy1.policy_id
        assert len(policy2.rules) == len(policy1.rules)


@pytest.mark.anyio
async def test_full_policy_selection_and_compliance_scan_workflow() -> None:
    """
    Tests the complete 4-step user workflow:
    1. Upload policy PDF -> returns PolicyIngestionResponse with policy_id.
    2. List available policies via GET /api/v1/policies -> pick policy UUID.
    3. Review extracted rules via GET /api/v1/policies/{policy_id}/rules.
    4. Run scoped compliance scan via POST /api/v1/compliance/scan?policy_id={policy_id}
       using docs/sample-evidence-1.json and assert deterministic audit results.
    """
    await init_db()
    pdf_bytes = SAMPLE_PDF_PATH.read_bytes()
    evidence_json = json.loads(SAMPLE_EVIDENCE_PATH.read_text(encoding="utf-8"))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", timeout=60.0) as ac:
        # Step 1: Upload PDF
        files = {"file": ("sample-policy-1.pdf", pdf_bytes, "application/pdf")}
        upload_resp: Response = await ac.post("/api/v1/policies/upload-pdf", files=files)
        assert upload_resp.status_code == 201
        uploaded_policy = PolicyIngestionResponse.model_validate(upload_resp.json())
        policy_id = uploaded_policy.policy_id

        # Step 2: List policies for dashboard dropdown
        list_resp: Response = await ac.get("/api/v1/policies")
        assert list_resp.status_code == 200
        policies_list = list_resp.json()
        assert any(p["id"] == str(policy_id) for p in policies_list)

        # Step 3: Inspect extracted rules for this policy
        rules_resp: Response = await ac.get(f"/api/v1/policies/{policy_id}/rules")
        assert rules_resp.status_code == 200
        rules_data = rules_resp.json()
        assert rules_data["id"] == str(policy_id)
        assert len(rules_data["rules"]) >= 1

        # Step 4: Run compliance scan scoped to this specific policy_id
        scan_resp: Response = await ac.post(
            f"/api/v1/compliance/scan?policy_id={policy_id}",
            json=evidence_json,
        )
        assert scan_resp.status_code == 200
        scan_result = ComplianceScanResponse.model_validate(scan_resp.json())

        assert scan_result.scan_id == evidence_json["scan_id"]
        assert scan_result.total_assets == len(evidence_json["assets"])
        assert scan_result.overall_status in (ComplianceStatus.COMPLIANT, ComplianceStatus.NON_COMPLIANT)
        assert len(scan_result.asset_results) == len(evidence_json["assets"])

        # Verify individual check results have audit reasoning
        for asset_res in scan_result.asset_results:
            assert asset_res.asset_id
            for check in asset_res.checks:
                assert check.control_id
                assert check.status
                assert check.audit_reasoning