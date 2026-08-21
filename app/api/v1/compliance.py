"""
Handles evidence ingestion and evaluation against persistent database rules.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.schema import ComplianceScanResponse, EvidencePayload
from app.services.compliance_service import ComplianceOrchestrationService

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.post(
    "/scan",
    response_model=ComplianceScanResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Compliance Audit Scan",
)
async def run_compliance_scan(
    evidence: EvidencePayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    policy_id: Annotated[
        uuid.UUID | None,
        Query(description="Optional policy UUID filter. If omitted, audits against all active rules."),
    ] = None,
) -> ComplianceScanResponse:
    orchestrator = ComplianceOrchestrationService(db)
    return await orchestrator.evaluate_evidence(evidence=evidence, policy_id=policy_id)
