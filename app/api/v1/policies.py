"""
Handles document ingestion, PDF text extraction, deduplication, and rule queries.
"""

import io
import uuid
from datetime import datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.schema import (
    ComparisonOperator,
    ExtractedRuleBase,
    JsonValue,
    PolicyIngestionResponse,
    PreCondition,
)
from app.repositories.policy_repo import PolicyRepository
from app.services.compliance_service import ComplianceOrchestrationService

router = APIRouter(prefix="/policies", tags=["Policies"])


class PolicyTextRequest(BaseModel):
    policy_name: str = Field(..., min_length=3, max_length=255)
    raw_text: str = Field(..., min_length=20)


class PolicyListItem(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    rule_count: int


class PolicyDetailResponse(BaseModel):
    id: uuid.UUID
    name: str
    rules: list[ExtractedRuleBase]


def _extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extracts raw text pages from an uploaded PDF stream."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        extracted_pages = [
            page.extract_text() for page in reader.pages if page.extract_text()
        ]
        full_text = "\n".join(extracted_pages).strip()
        if not full_text:
            raise ValueError("No extractable text found in PDF.")
        return full_text
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract text from PDF: {str(exc)}",
        ) from exc


@router.post(
    "/upload-pdf",
    response_model=PolicyIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF Policy Document",
)
async def upload_policy_pdf(
    file: Annotated[UploadFile, File(description="Policy PDF document")],
    db: AsyncSession = Depends(get_db),
) -> PolicyIngestionResponse:
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files are supported.",
        )

    content = await file.read()
    raw_text = _extract_text_from_pdf_bytes(content)

    fallback_title = file.filename.rsplit(".", 1)[0] if file.filename else None
    orchestrator = ComplianceOrchestrationService(db)
    return await orchestrator.ingest_policy_document(
        document_text=raw_text, fallback_title=fallback_title
    )


@router.post(
    "/extract-text",
    response_model=PolicyIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Extract Rules from Plain Text",
)
async def extract_policy_from_text(
    payload: PolicyTextRequest,
    db: AsyncSession = Depends(get_db),
) -> PolicyIngestionResponse:
    orchestrator = ComplianceOrchestrationService(db)
    return await orchestrator.ingest_policy_document(
        document_text=payload.raw_text, fallback_title=payload.policy_name
    )


@router.get(
    "",
    response_model=list[PolicyListItem],
    status_code=status.HTTP_200_OK,
    summary="List all policies for selection dropdown",
)
async def list_policies(db: AsyncSession = Depends(get_db)) -> list[PolicyListItem]:
    repo = PolicyRepository(db)
    policies = await repo.list_policies_summary()
    return [PolicyListItem.model_validate(p) for p in policies]


@router.get(
    "/{policy_id}/rules",
    response_model=PolicyDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full rule list for a specific policy",
)
async def get_policy_details(
    policy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PolicyDetailResponse:
    repo = PolicyRepository(db)
    policy = await repo.get_policy_by_id(policy_id=policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found.",
        )

    rules: list[ExtractedRuleBase] = []
    for r in policy.rules:
        pre_cond: PreCondition | None = None
        if isinstance(r.pre_condition, dict):
            target_metric = r.pre_condition.get("target_metric")
            op_val = r.pre_condition.get("operator")
            thresh_val = r.pre_condition.get("threshold_value")
            if (
                isinstance(target_metric, str)
                and isinstance(op_val, str)
                and thresh_val is not None
            ):
                pre_cond = PreCondition(
                    target_metric=target_metric,
                    operator=ComparisonOperator(op_val),
                    threshold_value=cast(JsonValue, thresh_val),
                )

        rules.append(
            ExtractedRuleBase(
                control_id=r.control_id,
                title=r.title,
                target_asset_type=r.target_asset_type,
                target_metric=r.target_metric,
                operator=ComparisonOperator(r.operator),
                threshold_value=cast(JsonValue, r.threshold_value),
                source_clause=r.source_clause,
                page_number=r.page_number,
                pre_condition=pre_cond,
            )
        )

    return PolicyDetailResponse(
        id=policy.id,
        name=policy.name,
        rules=rules,
    )