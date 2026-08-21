# Services Layer (`app/services/`)

This directory contains pure, framework-agnostic business logic services, AI rule extraction pipelines, and deterministic evaluation engines.

---

## 📁 Files & Responsibilities

### 1. `extractor.py` ([`app/services/extractor.py`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/app/services/extractor.py))
- Injects `PolicyExtractionPayload.model_json_schema()` into system instructions.
- Calls `generate_structured_json(...)` from `app/core/llm.py`.
- Cleans markdown fences (`_clean_json_markdown`) and validates against `PolicyExtractionPayload`.

### 2. `evaluation.py` ([`app/services/evaluation.py`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/app/services/evaluation.py))
- Evaluates an `ExtractedRuleBase` against an `EvidenceAsset`.
- Evaluates `pre_condition` first; if not met or metric missing, skips evaluation (`NOT_APPLICABLE`).
- Evaluates comparison operators:
  - Numeric: `<`, `<=`, `>`, `>=`
  - Equality / Difference: `==`, `!=`
  - Membership: `in`, `not_in` (handles list and string containment)
- Formats plain-language `audit_reasoning` with verbatim policy citation.

### 3. `compliance_service.py` ([`app/services/compliance_service.py`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/app/services/compliance_service.py))
- **`ComplianceOrchestrationService`**:
  - `ingest_policy_document(document_text, fallback_title)`: Calculates SHA-256 hash $\to$ checks cache $\to$ extracts via Gemini on cache miss $\to$ returns `PolicyIngestionResponse`.
  - `evaluate_evidence(evidence, policy_id)`: Fetches active DB rules $\to$ evaluates each asset $\to$ aggregates `ComplianceScanResponse`.