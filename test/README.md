# Automated Test Suites (`test/`)

This directory contains automated unit, integration, and end-to-end regression tests verifying all components of the compliance evaluation platform.

---

## 📁 Test Organization

```text
test/
├── api/
│   └── test_v1.py              # End-to-end API route tests using docs/ sample files
├── db/
│   └── test_session.py         # PostgreSQL schema bootstrapping and repository tests
└── services/
    ├── test_compliance_service.py # Orchestration pipeline & deduplication caching tests
    ├── test_evaluation.py         # Deterministic mathematical operator unit tests
    └── test_extractor.py          # Gemini AI extraction and markdown parsing tests
```

---

## 🧪 Test Suites Breakdown

| Suite | File | Coverage |
| :--- | :--- | :--- |
| **API Endpoints** | [`test/api/test_v1.py`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/test/api/test_v1.py) | `/health`, `/upload-pdf` with `docs/sample-policy-1.pdf`, SHA-256 deduplication cache hit, `/policies` dropdown list, `/policies/{id}/rules` inspection, `/compliance/scan` with `docs/sample-evidence-1.json`. |
| **Database Layer** | [`test/db/test_session.py`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/test/db/test_session.py) | PostgreSQL `init_db()` table creation, `PolicyRepository` CRUD operations, and `content_hash` lookups. |
| **Compliance Orchestration** | [`test/services/test_compliance_service.py`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/test/services/test_compliance_service.py) | Full orchestration pipeline from PDF ingestion to evidence evaluation and deduplication. |
| **Deterministic Evaluator** | [`test/services/test_evaluation.py`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/test/services/test_evaluation.py) | All comparison operators (`<`, `<=`, `>`, `>=`, `==`, `!=`, `in`, `not_in`), missing metrics (`UNKNOWN`), asset mismatches (`NOT_APPLICABLE`), and pre-condition triggers. |
| **AI Extractor** | [`test/services/test_extractor.py`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/test/services/test_extractor.py) | Google Gemini API activation, markdown fence cleaner, live Flyyy.ai PDF policy extraction, and multi-clause rules. |

---

## 🚀 Running Tests

Run the full test suite with `uv`:
```bash
uv run pytest -v
```
