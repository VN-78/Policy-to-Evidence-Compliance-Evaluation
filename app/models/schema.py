# region imports

from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, JsonValue

# =====================================================================
# 1. Primitives & Enums
# =====================================================================


class ComparisonOperator(str, Enum):
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="
    EQ = "=="
    NEQ = "!="
    IN = "in"
    NOT_IN = "not_in"


class ComplianceStatus(str, Enum):
    COMPLIANT = "Compliant"
    NON_COMPLIANT = "Non-Compliant"
    NOT_APPLICABLE = "Not Applicable"
    UNKNOWN = "Unknown"


class PreCondition(BaseModel):
    """Evaluated first. If true, the main rule applies. If false, the rule is skipped."""

    target_metric: str = Field(
        ...,
        description="The metric to check before applying the main rule",
        examples=["is_publicly_accessible"]
    )
    operator: ComparisonOperator = Field(
        ...,
        description="The operator for the pre-condition",
        examples=[ComparisonOperator.EQ]
    )
    threshold_value: JsonValue = Field(
        ...,
        description="The value that triggers the main rule",
        examples=[True]
    )

# =====================================================================
# 2. Policy & LLM Extraction Schemas
# =====================================================================


class ExtractedRuleBase(BaseModel):
    """Atomic rule representation extracted from policy text."""

    control_id: str = Field(
        ...,
        description="Unique identifier for the rule/control (e.g., 'SEC-01', 'ISO-27001-8.6')",
        examples=["CAP-001"],
    )
    title: str = Field(
        ...,
        description="Short description of the control",
        examples=["Max CPU Utilization Limit"],
    )
    target_asset_type: str = Field(
        ...,
        description="Asset type this rule applies to (e.g., 'database_server')",
        examples=["database_server"],
    )
    target_metric: str = Field(
        ...,
        description="Exact metric key expected in the evidence payload",
        examples=["cpu_utilization"],
    )
    operator: ComparisonOperator = Field(
        ...,
        description="Comparison operator for the evaluation engine",
        examples=[ComparisonOperator.LT],
    )
    threshold_value: JsonValue = Field(
        ...,
        description="Value to compare the evidence metric against",
        examples=[85],
    )
    source_clause: str = Field(
        ...,
        description="Exact verbatim sentence from the policy document justifying this rule",
        examples=[
            "Our production application and database servers are required to operate with CPU utilization below 85%"
        ],
    )
    page_number: int | None = Field(
        default=1,
        description="Document page where this clause is located",
    )
    pre_condition: PreCondition | None = Field(
            default=None,
            description="Optional condition that must be true for this rule to apply."
    )

    # FIXED: ClassVar tells Pyright this is a class attribute, not an instance attribute
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class PolicyExtractionPayload(BaseModel):
    """Schema passed directly to structured LLM outputs."""

    policy_name: str = Field(..., description="Inferred or extracted name of the policy document")
    rules: list[ExtractedRuleBase] = Field(
        default_factory=list,
        description="List of machine-evaluatable rules extracted from the policy",
    )


class RuleResponse(ExtractedRuleBase):
    """Schema returned to React UI for Screen 1 Preview."""

    id: str = Field(..., description="Database UUID/ID of the persisted rule")
    policy_id: str = Field(..., description="ID of parent policy")


# =====================================================================
# 3. Raw Evidence Ingestion Schemas
# =====================================================================


class EvidenceAsset(BaseModel):
    """Individual infrastructure component containing dynamic metrics."""

    asset_id: str = Field(
        ...,
        description="Unique identifier for the asset",
        examples=["prod-db-server-01"],
    )
    asset_type: str = Field(
        ...,
        description="Category/type of infrastructure",
        examples=["database_server"],
    )
    # FIXED: Safely types an unknown dictionary layout without using 'Any'
    metrics: dict[str, JsonValue] = Field(
        ...,
        description="Dynamic key-value pairs representing metrics or configurations",
        examples=[{"cpu_utilization": 92, "auto_scaling_enabled": True}],
    )


class EvidencePayload(BaseModel):
    """Complete platform evidence JSON payload ingested for evaluation."""

    scan_id: str = Field(..., description="Unique scan run identifier", examples=["SCAN-2026-0812"])
    environment: str = Field(..., description="Target deployment environment", examples=["production"])
    assets: list[EvidenceAsset] = Field(..., description="List of scanned infrastructure assets")


# =====================================================================
# 4. Evaluation Verdict & Audit Schemas (Screen 2 Dashboard)
# =====================================================================


class RuleEvaluationResult(BaseModel):
    """Evaluation result for an individual rule against an asset."""

    control_id: str = Field(..., examples=["CAP-001"])
    target_metric: str = Field(..., examples=["cpu_utilization"])
    operator: str = Field(..., examples=["<"])
    threshold_value: JsonValue = Field(..., examples=[85])
    actual_value: JsonValue | None = Field(default=None, examples=[92])
    status: ComplianceStatus = Field(..., examples=[ComplianceStatus.NON_COMPLIANT])
    audit_reasoning: str = Field(
        ...,
        description="Plain-text human readable explanation of the verdict",
        examples=["Non-Compliant because CPU utilization is 92%, which exceeds the maximum policy threshold of 85%."],
    )
    source_clause: str | None = Field(default=None)


class AssetEvaluationResult(BaseModel):
    """Aggregated compliance posture for a single asset."""

    asset_id: str = Field(..., examples=["prod-db-server-01"])
    asset_type: str = Field(..., examples=["database_server"])
    overall_status: ComplianceStatus = Field(..., examples=[ComplianceStatus.NON_COMPLIANT])
    checks: list[RuleEvaluationResult] = Field(default_factory=list)


class ComplianceScanResponse(BaseModel):
    """Master response schema returned by the POST endpoint."""

    scan_id: str = Field(..., examples=["SCAN-2026-0812"])
    environment: str = Field(..., examples=["production"])
    overall_status: ComplianceStatus = Field(..., examples=[ComplianceStatus.NON_COMPLIANT])
    total_assets: int = Field(..., examples=[1])
    compliant_assets_count: int = Field(..., examples=[0])
    non_compliant_assets_count: int = Field(..., examples=[1])
    asset_results: list[AssetEvaluationResult] = Field(default_factory=list)
