# Repository Layer (`app/repositories/`)

This directory encapsulates all database queries and persistence operations for the compliance evaluation system.

---

## 📁 Files & Responsibilities

### `policy_repo.py` ([`app/repositories/policy_repo.py`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/app/repositories/policy_repo.py))

- **`PolicyRepository`**:
  - `get_by_content_hash(content_hash: str) -> PolicyModel | None`: Performs fast SHA-256 hash lookup with `selectinload(PolicyModel.rules)` for zero-latency cached re-ingestions.
  - `get_policy_by_id(policy_id: uuid.UUID) -> PolicyModel | None`: Fetches a single policy with rules preloaded.
  - `create_policy_with_rules(payload: PolicyExtractionPayload, content_hash: str, raw_text: str | None) -> PolicyModel`: Persists a new policy and its child rules within an atomic transaction.
  - `get_active_rules(policy_id: uuid.UUID | None) -> list[RuleModel]`: Queries all active rules, optionally filtering by `policy_id`.
  - `list_policies_summary() -> list[dict[str, object]]`: Optimized aggregation query returning policy list items with active rule counts (`func.count(RuleModel.id)`).
  - `get_policy_rules(policy_id: uuid.UUID) -> list[RuleModel]`: Fetches active rules for UI inspection.