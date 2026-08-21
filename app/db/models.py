import uuid
from datetime import datetime, timezone

from pydantic import JsonValue
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PolicyModel(Base):
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # ADDED: Unique SHA-256 digest of document text
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    rules: Mapped[list["RuleModel"]] = relationship(
        back_populates="policy", cascade="all, delete-orphan", lazy="selectin"
    )


class RuleModel(Base):
    __tablename__ = "rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False
    )
    control_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_asset_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_metric: Mapped[str] = mapped_column(String(100), nullable=False)
    operator: Mapped[str] = mapped_column(String(20), nullable=False)

    # FIXED: Type as JsonValue instead of object
    threshold_value: Mapped[JsonValue] = mapped_column(JSONB, nullable=False)

    source_clause: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, default=1)

    # FIXED: Type as dict[str, JsonValue] instead of dict[str, object]
    pre_condition: Mapped[dict[str, JsonValue] | None] = mapped_column(JSONB, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    policy: Mapped["PolicyModel"] = relationship(back_populates="rules")
