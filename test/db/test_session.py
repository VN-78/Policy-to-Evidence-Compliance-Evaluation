import hashlib
import uuid
import pytest
from sqlalchemy import text

from app.db.session import AsyncSessionLocal, engine, init_db
from app.models.schema import ComparisonOperator, ExtractedRuleBase, PolicyExtractionPayload
from app.repositories.policy_repo import PolicyRepository


@pytest.mark.anyio
async def test_init_db_and_schema_tables() -> None:
    """Verifies that init_db bootstraps tables in PostgreSQL."""
    await init_db()
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        )
        tables = [row[0] for row in result.fetchall()]
        assert "policies" in tables
        assert "rules" in tables


@pytest.mark.anyio
async def test_policy_repository_crud() -> None:
    """Tests PolicyRepository creation, content_hash lookup, and active rule queries."""
    await init_db()
    async with AsyncSessionLocal() as session:
        repo = PolicyRepository(session)
        raw_content = f"Database Security Policy Test Text {uuid.uuid4()}"
        content_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()

        payload = PolicyExtractionPayload(
            policy_name="Database Security Policy",
            rules=[
                ExtractedRuleBase(
                    control_id="SEC-001",
                    title="Storage Encryption",
                    target_asset_type="object_storage",
                    target_metric="encryption_enabled",
                    operator=ComparisonOperator.EQ,
                    threshold_value=True,
                    source_clause="Storage buckets must have encryption enabled.",
                    pre_condition=None,
                )
            ],
        )

        policy = await repo.create_policy_with_rules(
            payload=payload,
            content_hash=content_hash,
            raw_text=raw_content,
        )
        assert policy.id is not None
        assert policy.name == "Database Security Policy"
        assert policy.content_hash == content_hash

        # Verify get_by_content_hash
        fetched_by_hash = await repo.get_by_content_hash(content_hash)
        assert fetched_by_hash is not None
        assert fetched_by_hash.id == policy.id
        assert len(fetched_by_hash.rules) == 1

        # Verify get_policy_by_id
        fetched_by_id = await repo.get_policy_by_id(policy.id)
        assert fetched_by_id is not None
        assert fetched_by_id.name == "Database Security Policy"

        # Verify get_active_rules
        active_rules = await repo.get_active_rules(policy_id=policy.id)
        assert len(active_rules) == 1
        assert active_rules[0].control_id == "SEC-001"
        assert active_rules[0].threshold_value is True
