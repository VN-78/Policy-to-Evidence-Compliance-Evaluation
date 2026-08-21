# Domain Models & Schemas (`app/models/`)

This directory defines the Pydantic v2 data models, enums, request bodies, and response contracts for the entire application.

---

## 📁 Files & Responsibilities

### `schema.py` ([`app/models/schema.py`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/app/models/schema.py))

#### 1. Enums & Primitives
- **`ComparisonOperator`**: `"<"`, `"<="`, `">"`, `">="`, `"=="`, `"!="`, `"in"`, `"not_in"`.
- **`ComplianceStatus`**: `"Compliant"`, `"Non-Compliant"`, `"Not Applicable"`, `"Unknown"`.
- **`PreCondition`**: Evaluated prior to main rules to filter asset applicability.

#### 2. Policy Ingestion & Extraction Models
- **`ExtractedRuleBase`**: Canonical representation of an atomic machine-evaluatable compliance rule extracted from prose.
- **`PolicyExtractionPayload`**: JSON schema provided to structured LLM extraction prompts.
- **`PolicyIngestionResponse`**: Response returned after persisting or deduplicating a policy (`policy_id`, `policy_name`, `rules`).

#### 3. Evidence Ingestion Models
- **`EvidenceAsset`**: Infrastructure resource containing `asset_id`, `asset_type`, and `metrics: dict[str, JsonValue]`.
- **`EvidencePayload`**: Master evidence scan payload containing `scan_id`, `environment`, and `assets`.

#### 4. Compliance Verdict Models
- **`RuleEvaluationResult`**: Result of evaluating a single rule against an asset (includes `status` and `audit_reasoning`).
- **`AssetEvaluationResult`**: Aggregated status for a single asset across all checks.
- **`ComplianceScanResponse`**: Comprehensive response returned by the compliance audit endpoint (`/api/v1/compliance/scan`).

#### Strict Typing Rule
- **Zero `Any` Usage**: All dynamic metric dictionaries and polymorphic values use `pydantic.JsonValue`.