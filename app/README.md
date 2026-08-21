# Application Backend Architecture (`app/`)

This directory houses the core application code for the Policy-to-Evidence Compliance Evaluation FastAPI backend. The codebase is organized strictly following the **Layered Architecture (N-Tier)** pattern with clean separation of concerns and zero framework coupling in the business layer.

---

## 📁 Subdirectory Roles & Responsibilities

| Module | Purpose | Key Technical Directives |
| :--- | :--- | :--- |
| [`api/`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/app/api) | **HTTP Router Layer** | Thin endpoint controllers (`app/api/v1/policies.py`, `app/api/v1/compliance.py`). Validates requests via Pydantic, delegates to Services via Dependency Injection (`Depends(get_db)`). |
| [`core/`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/app/core) | **Configuration & LLM Subsystem** | Central configuration (`config.py`) via `pydantic-settings` and provider-agnostic LLM client dispatcher (`llm.py`) managing Google Gemini and OpenRouter fallback chains. |
| [`db/`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/app/db) | **Persistence & Engine Layer** | Database session lifecycle (`session.py`) using `create_async_engine` with `NullPool` and asyncpg. Declarative SQLAlchemy models (`models.py`) with PostgreSQL `JSONB` support. |
| [`models/`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/app/models) | **Pydantic Validation Schemas** | Strict domain schemas (`schema.py`) enforcing data validation on API inputs, LLM JSON outputs, and evaluation responses with **zero `Any` types**. |
| [`repositories/`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/app/repositories) | **Data Access Layer** | Encapsulated database operations (`policy_repo.py`). Performs SHA-256 hash lookups, creates atomic rules with parent relationships, and runs optimized queries with `selectinload`. |
| [`services/`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/app/services) | **Business Logic Layer** | Pure business services: AI prompt extraction (`extractor.py`), deterministic mathematical evaluator (`evaluation.py`), and compliance orchestration pipeline (`compliance_service.py`). |
| [`utils/`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/app/utils) | **Stateless Helpers** | Pure utility functions and shared formatting helpers without database or network dependencies. |

---

## 📐 Core Pydantic Schemas (`app/models/schema.py`)

The application enforces end-to-end type safety using Pydantic v2. Below are the primary models used across the system:

```python
import uuid
from enum import Enum
from typing import ClassVar
from pydantic import BaseModel, ConfigDict, Field, JsonValue


class ComparisonOperator(str, Enum):
    """Supported mathematical and logical evaluation operators."""
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="
    EQ = "=="
    NEQ = "!="
    IN = "in"
    NOT_IN = "not_in"


class ComplianceStatus(str, Enum):
    """Possible audit evaluation outcomes."""
    COMPLIANT = "Compliant"
    NON_COMPLIANT = "Non-Compliant"
    NOT_APPLICABLE = "Not Applicable"
    UNKNOWN = "Unknown"


class PreCondition(BaseModel):
    """Evaluated first. If true, the rule applies. If false, the rule is skipped."""
    target_metric: str = Field(..., description="Metric key to check before evaluation")
    operator: ComparisonOperator = Field(..., description="Comparison operator for condition")
    threshold_value: JsonValue = Field(..., description="Value that triggers rule evaluation")


class ExtractedRuleBase(BaseModel):
    """Atomic machine-evaluatable rule extracted from policy prose."""
    control_id: str = Field(..., description="Unique rule/control identifier (e.g., 'SEC-S3-001')")
    title: str = Field(..., description="Short title describing the control")
    target_asset_type: str = Field(..., description="Target asset category (e.g., 's3_bucket')")
    target_metric: str = Field(..., description="Exact metric key expected in evidence JSON")
    operator: ComparisonOperator = Field(..., description="Comparison operator for evaluation")
    threshold_value: JsonValue = Field(..., description="Threshold value (number, bool, string, list)")
    source_clause: str = Field(..., description="Verbatim sentence from the policy document")
    page_number: int | None = Field(default=1, description="Page number of the citation")
    pre_condition: PreCondition | None = Field(default=None, description="Optional trigger pre-condition")

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class PolicyExtractionPayload(BaseModel):
    """Schema expected from structured LLM outputs."""
    policy_name: str = Field(..., description="Extracted or inferred policy title")
    rules: list[ExtractedRuleBase] = Field(default_factory=list, description="Extracted rules")


class PolicyIngestionResponse(BaseModel):
    """Response returned after extracting and persisting a policy to PostgreSQL."""
    policy_id: uuid.UUID = Field(..., description="Persistent UUID of the policy in PostgreSQL")
    policy_name: str = Field(..., description="Name of the ingested policy")
    rules: list[ExtractedRuleBase] = Field(default_factory=list, description="Extracted rules")


class EvidenceAsset(BaseModel):
    """Individual scanned infrastructure resource containing telemetry metrics."""
    asset_id: str = Field(..., description="Resource ARN or ID (e.g., 'i-098765fedcba43210')")
    asset_type: str = Field(..., description="Resource category (e.g., 'ec2_instance')")
    metrics: dict[str, JsonValue] = Field(..., description="Dynamic key-value metric attributes")


class EvidencePayload(BaseModel):
    """Complete platform evidence JSON payload ingested for compliance audit."""
    scan_id: str = Field(..., description="Scan run identifier")
    environment: str = Field(..., description="Target deployment environment (e.g., 'production')")
    assets: list[EvidenceAsset] = Field(..., description="Scanned assets")


class RuleEvaluationResult(BaseModel):
    """Evaluation verdict for an individual rule against an asset."""
    control_id: str
    target_metric: str
    operator: str
    threshold_value: JsonValue
    actual_value: JsonValue | None = None
    status: ComplianceStatus
    audit_reasoning: str
    source_clause: str | None = None


class AssetEvaluationResult(BaseModel):
    """Aggregated compliance posture for a single asset."""
    asset_id: str
    asset_type: str
    overall_status: ComplianceStatus
    checks: list[RuleEvaluationResult] = Field(default_factory=list)


class ComplianceScanResponse(BaseModel):
    """Master response schema returned by the POST /api/v1/compliance/scan endpoint."""
    scan_id: str
    environment: str
    overall_status: ComplianceStatus
    total_assets: int
    compliant_assets_count: int
    non_compliant_assets_count: int
    asset_results: list[AssetEvaluationResult] = Field(default_factory=list)
```

---

## 🛠️ Architectural Guidelines & Code Conventions

1. **Strict Layer Boundary Isolation**:
   - HTTP routes in `app/api/` never perform database queries or invoke the LLM directly.
   - Business services in `app/services/` never import `Request`, `Response`, or FastAPI constructs.
   - Repositories in `app/repositories/` handle all SQLAlchemy statements and relationship options (`selectinload`).
2. **Zero `Any` Type Annotations**:
   - All dictionary metric payloads and polymorphic thresholds are strictly typed as `JsonValue` (`None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]`).
3. **Clean Async Lifecycles**:
   - `app/db/session.py` uses `NullPool` to prevent asyncpg connection pool leaks when executing across multiple asynchronous event loops.
