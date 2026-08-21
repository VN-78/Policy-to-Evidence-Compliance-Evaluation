import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import PolicyModel, RuleModel
from app.models.schema import PolicyExtractionPayload


class PolicyRepository:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_content_hash(self, content_hash: str) -> PolicyModel | None:
        """Finds existing policy by its SHA-256 text hash, pre-loading rules."""
        stmt = (
            select(PolicyModel)
            .options(selectinload(PolicyModel.rules))
            .where(PolicyModel.content_hash == content_hash)
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_policy_by_id(self, policy_id: uuid.UUID) -> PolicyModel | None:
        """Fetches a single policy with rules preloaded."""
        stmt = select(PolicyModel).options(selectinload(PolicyModel.rules)).where(PolicyModel.id == policy_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_policy_with_rules(
        self,
        payload: PolicyExtractionPayload,
        content_hash: str,
        raw_text: str | None = None,
    ) -> PolicyModel:
        """Persists extracted policy metadata and associated atomic rules."""
        policy = PolicyModel(
            name=payload.policy_name,
            content_hash=content_hash,
            raw_text=raw_text,
        )
        self.session.add(policy)
        await self.session.flush()  # Generates policy.id without committing

        for rule_data in payload.rules:
            operator_str: str = (
                rule_data.operator.value if hasattr(rule_data.operator, "value") else str(rule_data.operator)
            )
            rule_model = RuleModel(
                policy_id=policy.id,
                control_id=rule_data.control_id,
                title=rule_data.title,
                target_asset_type=rule_data.target_asset_type,
                target_metric=rule_data.target_metric,
                operator=operator_str,
                threshold_value=rule_data.threshold_value,
                source_clause=rule_data.source_clause,
                page_number=rule_data.page_number,
                pre_condition=(rule_data.pre_condition.model_dump() if rule_data.pre_condition else None),
            )
            self.session.add(rule_model)

        await self.session.commit()
        await self.session.refresh(policy)
        return policy

    async def get_active_rules(self, policy_id: uuid.UUID | None = None) -> list[RuleModel]:
        """Fetches active rules for compliance evaluation."""
        stmt = select(RuleModel).where(RuleModel.is_active == True)  # noqa: E712
        if policy_id is not None:
            stmt = stmt.where(RuleModel.policy_id == policy_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_policies_summary(self) -> list[dict[str, object]]:
        """Returns all ingested policies with active rule counts for UI selectors."""
        stmt = (
            select(
                PolicyModel.id,
                PolicyModel.name,
                PolicyModel.created_at,
                func.count(RuleModel.id).label("rule_count"),
            )
            .outerjoin(RuleModel, PolicyModel.id == RuleModel.policy_id)
            .where(RuleModel.is_active == True)  # noqa: E712
            .group_by(PolicyModel.id, PolicyModel.name, PolicyModel.created_at)
            .order_by(PolicyModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        rows: Sequence[tuple[uuid.UUID, str, datetime, int]] = result.tuples().all()
        return [
            {
                "id": p_id,
                "name": p_name,
                "created_at": p_created_at,
                "rule_count": p_rule_count,
            }
            for p_id, p_name, p_created_at, p_rule_count in rows
        ]

    async def get_policy_rules(self, policy_id: uuid.UUID) -> list[RuleModel]:
        """Fetches all rules for a single policy to preview in the UI."""
        stmt = (
            select(RuleModel)
            .options(selectinload(RuleModel.policy))
            .where(RuleModel.policy_id == policy_id, RuleModel.is_active == True)  # noqa: E712
            .order_by(RuleModel.control_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
