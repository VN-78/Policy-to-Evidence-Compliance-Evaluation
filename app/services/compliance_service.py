import hashlib
import uuid
from typing import cast

from pydantic import JsonValue
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schema import (
    AssetEvaluationResult,
    ComparisonOperator,
    ComplianceScanResponse,
    ComplianceStatus,
    EvidencePayload,
    ExtractedRuleBase,
    PolicyIngestionResponse,
    PreCondition,
    RuleEvaluationResult,
)
from app.repositories.policy_repo import PolicyRepository
from app.services.evaluation import evaluate_rule
from app.services.extractor import extract_rules_from_text


class ComplianceOrchestrationService:
    def __init__(self, session: AsyncSession):
        self.repo = PolicyRepository(session)

    async def ingest_policy_document(
        self, document_text: str, fallback_title: str | None = None
    ) -> PolicyIngestionResponse:
        """
        Deduplicates via SHA-256 hash.
        If document already exists, returns cached DB rules without calling Gemini.
        """
        # 1. Generate deterministic checksum of normalized document text
        normalized_text = document_text.strip()
        content_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()

        # 2. Check if this exact policy document is already in the database
        existing_policy = await self.repo.get_by_content_hash(content_hash)
        if existing_policy is not None:
            cached_rules: list[ExtractedRuleBase] = []
            for r in existing_policy.rules:
                pre_cond: PreCondition | None = None
                if isinstance(r.pre_condition, dict):
                    t_metric = r.pre_condition.get("target_metric")
                    op_val = r.pre_condition.get("operator")
                    t_val = r.pre_condition.get("threshold_value")
                    if isinstance(t_metric, str) and isinstance(op_val, str) and t_val is not None:
                        pre_cond = PreCondition(
                            target_metric=t_metric,
                            operator=ComparisonOperator(op_val),
                            threshold_value=cast(JsonValue, t_val),
                        )

                cached_rules.append(
                    ExtractedRuleBase(
                        control_id=str(r.control_id),
                        title=str(r.title),
                        target_asset_type=str(r.target_asset_type),
                        target_metric=str(r.target_metric),
                        operator=ComparisonOperator(str(r.operator)),
                        threshold_value=cast(JsonValue, r.threshold_value),
                        source_clause=str(r.source_clause),
                        page_number=r.page_number,
                        pre_condition=pre_cond,
                    )
                )

            return PolicyIngestionResponse(
                policy_id=existing_policy.id,
                policy_name=existing_policy.name,
                rules=cached_rules,
            )

        # 3. Cache Miss: Extract via LLM and persist
        extracted_payload = await extract_rules_from_text(normalized_text)

        # Use fallback filename if LLM returns a blank or placeholder title
        if fallback_title and (
            not extracted_payload.policy_name
            or extracted_payload.policy_name.lower() in ("string", "policy", "untitled")
        ):
            extracted_payload.policy_name = fallback_title

        saved_policy = await self.repo.create_policy_with_rules(
            payload=extracted_payload,
            content_hash=content_hash,
            raw_text=normalized_text,
        )

        return PolicyIngestionResponse(
            policy_id=saved_policy.id,
            policy_name=saved_policy.name,
            rules=extracted_payload.rules,
        )

    async def evaluate_evidence(
        self, evidence: EvidencePayload, policy_id: uuid.UUID | None = None
    ) -> ComplianceScanResponse:
        """Step 2: Fetch DB rules -> Deterministic evaluation -> Aggregate dashboard result."""
        db_rules = await self.repo.get_active_rules(policy_id=policy_id)

        domain_rules: list[ExtractedRuleBase] = []
        for r in db_rules:
            pre_cond: PreCondition | None = None
            if isinstance(r.pre_condition, dict):
                target_metric = r.pre_condition.get("target_metric")
                op_val = r.pre_condition.get("operator")
                thresh_val = r.pre_condition.get("threshold_value")

                if isinstance(target_metric, str) and isinstance(op_val, str) and thresh_val is not None:
                    pre_cond = PreCondition(
                        target_metric=target_metric,
                        operator=ComparisonOperator(op_val),
                        threshold_value=cast(JsonValue, thresh_val),
                    )

            domain_rules.append(
                ExtractedRuleBase(
                    control_id=str(r.control_id),
                    title=str(r.title),
                    target_asset_type=str(r.target_asset_type),
                    target_metric=str(r.target_metric),
                    operator=ComparisonOperator(str(r.operator)),
                    threshold_value=cast(JsonValue, r.threshold_value),
                    source_clause=str(r.source_clause),
                    page_number=r.page_number,
                    pre_condition=pre_cond,
                )
            )

        asset_results: list[AssetEvaluationResult] = []
        non_compliant_assets_count = 0
        compliant_assets_count = 0

        for asset in evidence.assets:
            checks: list[RuleEvaluationResult] = []
            asset_is_compliant = True

            for rule in domain_rules:
                eval_res = evaluate_rule(rule=rule, asset=asset)
                checks.append(eval_res)

                if eval_res.status == ComplianceStatus.NON_COMPLIANT:
                    asset_is_compliant = False

            overall_asset_status = ComplianceStatus.COMPLIANT if asset_is_compliant else ComplianceStatus.NON_COMPLIANT

            if asset_is_compliant:
                compliant_assets_count += 1
            else:
                non_compliant_assets_count += 1

            asset_results.append(
                AssetEvaluationResult(
                    asset_id=asset.asset_id,
                    asset_type=asset.asset_type,
                    overall_status=overall_asset_status,
                    checks=checks,
                )
            )

        overall_scan_status = (
            ComplianceStatus.COMPLIANT if non_compliant_assets_count == 0 else ComplianceStatus.NON_COMPLIANT
        )

        return ComplianceScanResponse(
            scan_id=evidence.scan_id,
            environment=evidence.environment,
            overall_status=overall_scan_status,
            total_assets=len(evidence.assets),
            compliant_assets_count=compliant_assets_count,
            non_compliant_assets_count=non_compliant_assets_count,
            asset_results=asset_results,
        )
