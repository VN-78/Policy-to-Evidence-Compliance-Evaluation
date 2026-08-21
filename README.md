# Policy-to-Evidence Compliance Evaluation Engine

An automated **Policy-as-Code (PaC)** platform that ingests unstructured compliance policy documents (PDFs), extracts machine-readable atomic rules using GenAI with deterministic SHA-256 deduplication, persists them in PostgreSQL, and evaluates live infrastructure evidence JSON against these rules to render rigorous, traceable audit verdicts.

---

## 📑 Index

| Section | Description |
| :--- | :--- |
| [1. Business Requirements Document (BRD)](#-1-business-requirements-document-brd) | Problem statement, business objective, and core success criteria. |
| [2. Functional Requirements Document (FRD)](#-2-functional-requirements-document-frd) | End-to-end system capabilities from PDF parsing to audit reporting. |
| [3. Architecture Blueprint & Workflow](#-3-architecture-blueprint--workflow) | Mermaid sequence and architectural interaction diagrams. |
| [4. Concrete Input & Output Walkthrough](#-4-concrete-input--output-walkthrough) | Real-world policy snippet $\to$ extracted schema $\to$ evidence evaluation $\to$ verdict. |
| [5. Library & Tooling Justification Table](#-5-library--tooling-justification-table) | Technical rationale and trade-off analysis for selected technologies. |
| [6. Project Structure & Directory Layout](#-6-project-structure--directory-layout) | Repository layout and modular organization. |
| [7. Quickstart & Execution Guide](#-7-quickstart--execution-guide) | Docker setup, `uv` environment, FastAPI Swagger UI, and test runner. |

---

## 💼 1. Business Requirements Document (BRD)

- **The Problem:** Modern engineering organizations must comply with regulatory frameworks (SOC 2, ISO/IEC 27001, HIPAA, PCI-DSS) and internal governance policies. These policies exist as unstructured prose in static PDF documents. Concurrently, operational environments (AWS, GCP, Kubernetes) continuously emit structured configuration telemetry and metrics in JSON format. Traditional compliance audits require human auditors to manually map prose requirements to platform configurations. This manual process is slow, expensive, error-prone, non-continuous, and incapable of scaling with rapid cloud deployments.
- **The Objective:** Deliver an intelligent, automated compliance evaluation platform that extracts structured, machine-evaluatable rules from unstructured policy documents, persists them in a queryable relational database with zero duplicates, deterministically audits live infrastructure evidence against these rules, and renders transparent, human-readable audit reasoning.
- **Key Success Criteria:**
  - **Zero Hardcoded Rules:** Extraction is completely dynamic and driven by structured LLM outputs conforming to strict Pydantic schemas.
  - **Strict Determinism:** Compliance evaluations are calculated using mathematical and logical comparison engines without LLM hallucinations during audit runtime.
  - **Complete Traceability & Provenance:** Every audit verdict directly references the exact policy sentence (`source_clause`) and page number.
  - **Sub-Second Latency & Deduplication:** Pre-computed SHA-256 content hashing guarantees cached policy lookups in $<10\text{ms}$ with zero duplicate LLM costs.

---

## ⚙️ 2. Functional Requirements Document (FRD)

- **FR-1 (Multi-Page PDF & Text Ingestion):** Ingest multi-page policy PDFs via `multipart/form-data` or raw pasted plain text.
- **FR-2 (LLM Extraction & Provenance):** Leverage Google Gemini (`google-genai` SDK with OpenRouter backup) to parse text and extract structured rules conforming to the `ExtractedRuleBase` schema, capturing control IDs, target asset types, target metrics, comparison operators, threshold values, source clauses, and conditional pre-conditions.
- **FR-3 (Deduplication & Rule Persistence):** Calculate the SHA-256 digest of normalized document text. If identical content is re-uploaded, return cached database rules instantly. If new, persist the policy and atomic rules in PostgreSQL using native UUIDs and `JSONB` data types.
- **FR-4 (Policy Listing & Scoped Selection):** Provide endpoints to list all active policies with their rule counts, allowing users to select a specific `policy_id` UUID for targeted scans.
- **FR-5 (Live Evidence Ingestion):** Ingest raw infrastructure evidence payloads (`EvidencePayload`) containing arrays of scanned assets, asset types, and arbitrary dynamic metric key-value dictionaries.
- **FR-6 (Deterministic Evaluation Engine):** Evaluate evidence metrics against rule thresholds using strict operators (`<`, `<=`, `>`, `>=`, `==`, `!=`, `in`, `not_in`). Evaluate optional `pre_condition` clauses first to skip non-applicable rules.
- **FR-7 (Audit Verdict & Posture Dashboard):** Generate structured audit responses (`ComplianceScanResponse`) containing asset-level verdicts (`COMPLIANT`, `NON_COMPLIANT`, `NOT_APPLICABLE`, `UNKNOWN`), counts, and plain-language audit explanations.

---

## 🏗️ 3. Architecture Blueprint & Workflow

### End-to-End System Blueprint

```mermaid
flowchart TD
    subgraph Ingestion ["Phase 1: Ingestion & Extraction"]
        PDF[Unstructured PDF / Plaintext Policy] --> Extractor[pypdf Text Extraction & Normalization]
        Extractor --> Hasher[SHA-256 Checksum Hasher]
        Hasher --> CacheCheck{Cache Hit in DB?}
        CacheCheck -- Yes --> CachedPolicy[PostgreSQL Cached Rules]
        CacheCheck -- No --> Gemini[Google Gemini GenAI Extractor]
        Gemini --> SchemaValidate[Pydantic v2 PolicyExtractionPayload Validation]
        SchemaValidate --> DBPersist[(PostgreSQL: policies & rules tables)]
    end

    subgraph Evaluation ["Phase 2: Scoped Compliance Evaluation"]
        Evidence[Platform Evidence JSON: EvidencePayload] --> PolicySelector[Select Policy UUID]
        PolicySelector --> FetchRules[(Query Active Rules from DB)]
        FetchRules --> Engine[Deterministic Evaluation Engine: app/services/evaluation.py]
        Evidence --> Engine
        Engine --> PreCheck{Pre-Condition Met?}
        PreCheck -- No --> Skip[Skip Rule: NOT_APPLICABLE]
        PreCheck -- Yes --> Evaluate[Execute Comparison Operator: <, <=, >, >=, ==, !=, in]
        Evaluate --> Verdict[Generate Audit Reasoning & Asset Status]
        Verdict --> Response[Aggregate ComplianceScanResponse]
    end
```

### Sequence Flow

```mermaid
sequenceDiagram
    autonumber
    actor Client as Frontend / Client
    participant API as FastAPI Router (/api/v1)
    participant Service as ComplianceOrchestrationService
    participant Repo as PolicyRepository
    participant DB as PostgreSQL Database
    participant AI as Gemini GenAI
    participant Engine as Deterministic Evaluator

    Note over Client,AI: Step 1: Upload Policy Document
    Client->>API: POST /api/v1/policies/upload-pdf (file: sample-policy-1.pdf)
    API->>Service: ingest_policy_document(text, fallback_title)
    Service->>Repo: get_by_content_hash(sha256_hash)
    alt Cache Miss (New Policy)
        Service->>AI: extract_rules_from_text(normalized_text)
        AI-->>Service: PolicyExtractionPayload (rules)
        Service->>Repo: create_policy_with_rules(payload, sha256_hash)
        Repo->>DB: INSERT INTO policies & rules
        DB-->>Repo: Saved PolicyModel (with UUID)
    else Cache Hit (Existing Policy)
        Repo-->>Service: Cached PolicyModel from PostgreSQL
    end
    Service-->>API: PolicyIngestionResponse {policy_id, policy_name, rules}
    API-->>Client: PolicyIngestionResponse

    Note over Client,DB: Step 2: List Policies for Selection
    Client->>API: GET /api/v1/policies
    API->>Repo: list_policies_summary()
    Repo->>DB: SELECT id, name, created_at, count(rules)
    DB-->>Repo: list[dict]
    API-->>Client: list[PolicyListItem]

    Note over Client,Engine: Step 3: Run Policy-Scoped Compliance Scan
    Client->>API: POST /api/v1/compliance/scan?policy_id={policy_id} (Body: sample-evidence-1.json)
    API->>Service: evaluate_evidence(evidence, policy_id)
    Service->>Repo: get_active_rules(policy_id)
    Repo->>DB: SELECT * FROM rules WHERE policy_id = ... AND is_active = true
    DB-->>Service: list[RuleModel]
    loop For each Asset in EvidencePayload
        loop For each ExtractedRuleBase
            Service->>Engine: evaluate_rule(rule, asset)
            Engine-->>Service: RuleEvaluationResult (status, audit_reasoning)
        end
    end
    Service-->>API: ComplianceScanResponse
    API-->>Client: ComplianceScanResponse (overall_status, asset_results, checks)
```

---

## 🔍 4. Concrete Input & Output Walkthrough

### 1. Unstructured Policy Input (from `docs/sample-policy-1.pdf`)
> *"Our production application and database servers are required to operate with CPU utilization below 85% under normal operating conditions. We also keep auto-scaling enabled for applicable production workloads..."*

### 2. Extracted Machine-Readable Rule Schema
```json
{
  "control_id": "OPS-EC2-001",
  "title": "Compute Utilization & Capacity",
  "target_asset_type": "ec2_instance",
  "target_metric": "cpu_utilization",
  "operator": "<",
  "threshold_value": 85,
  "source_clause": "Under baseline operations, Amazon EC2 instances must maintain average cpu_utilization below 85 percent.",
  "page_number": 1,
  "pre_condition": null
}
```

### 3. Live Raw Infrastructure Evidence (from `docs/sample-evidence-1.json`)
```json
{
  "asset_id": "i-098765fedcba43210",
  "asset_type": "ec2_instance",
  "region": "ap-south-1",
  "metrics": {
    "instance_name": "legacy-report-generator",
    "cpu_utilization": 91.8
  }
}
```

### 4. Evaluated Audit Verdict (`ComplianceScanResponse`)
```json
{
  "control_id": "OPS-EC2-001",
  "target_metric": "cpu_utilization",
  "operator": "<",
  "threshold_value": 85,
  "actual_value": 91.8,
  "status": "Non-Compliant",
  "audit_reasoning": "Non-Compliant: Metric 'cpu_utilization' is 91.8, which violates the requirement (< 85). Source: Under baseline operations, Amazon EC2 instances must maintain average cpu_utilization below 85 percent."
}
```

---

## 🛠️ 5. Library & Tooling Justification Table

| Component | Technology Selected | Technical Rationale & Trade-offs |
| :--- | :--- | :--- |
| **Backend Framework** | **FastAPI (Python 3.14)** | Asynchronous event loop native support, automated OpenAPI 3.1 / Swagger generation, high-throughput ASGI performance, and seamless Pydantic v2 integration. |
| **Data Validation & Schemas** | **Pydantic v2** | Rust-backed `pydantic-core` validation engine ensuring sub-millisecond boundary validation for HTTP payloads and structured LLM outputs with zero `Any` type leakage. |
| **AI LLM Extraction** | **Google GenAI (`google-genai` SDK) & OpenRouter** | Direct native support for `gemini-3.7-flash` and `gemini-3.6-flash` with JSON mime-type schema enforcement. OpenRouter provides multi-provider redundancy. |
| **PDF Extraction** | **pypdf** | Pure-Python, lightweight stream parser capable of fast text extraction and page tracking without heavyweight C/OCR dependencies. |
| **Database** | **PostgreSQL 18** | ACID-compliant relational integrity for Policies (1) to Rules ($N$), with native `JSONB` columns for dynamic metric schemas and conditional rule definitions. |
| **Async ORM** | **SQLAlchemy 2.0 (Async) + asyncpg** | Non-blocking async I/O database driver with `NullPool` connection management, eliminating cross-event-loop connection pool deadlocks in test runners and async tasks. |
| **Package Management** | **`uv` (Astral)** | Extremely fast Python package resolver and virtual environment manager written in Rust, reducing setup time to seconds. |
| **Testing Suite** | **pytest + anyio** | Industry-standard async testing framework verifying edge cases, boundary thresholds, LLM extractions, repository CRUD, and API workflows. |
| **Containerization** | **Docker & Docker Compose** | Reproducible environment provisioning PostgreSQL (`compliance_pg`) and Adminer (`compliance_adminer`) with persistent volume management. |

---

## 📁 6. Project Structure & Directory Layout

```text
.
├── app/                              # Core Application Source
│   ├── api/                          # REST API Layer (FastAPI Routers)
│   │   └── v1/                       # Version 1 Endpoints (policies, compliance, router)
│   ├── core/                         # Core Settings (config.py) & LLM Subsystem (llm.py)
│   │   ├── config.py                 # Pydantic BaseSettings loading from .env
│   │   └── llm.py                    # Multi-provider client abstraction (Gemini + OpenRouter)
│   ├── db/                           # Database Layer
│   │   ├── models.py                 # SQLAlchemy 2.0 ORM Declarative Models (PolicyModel, RuleModel)
│   │   └── session.py                # Async database engine, sessionmaker, init_db
│   ├── models/                       # Data Validation Schemas
│   │   └── schema.py                 # Domain Pydantic schemas (ExtractedRuleBase, EvidencePayload, etc.)
│   ├── repositories/                 # Data Access Layer
│   │   └── policy_repo.py            # CRUD operations, SHA-256 lookups, active rule queries
│   ├── services/                     # Core Business Logic (Framework-Agnostic)
│   │   ├── compliance_service.py     # Orchestration service (ingest, deduplicate, evaluate)
│   │   ├── evaluation.py             # Deterministic rule evaluation engine
│   │   └── extractor.py              # LLM rule extraction and markdown parsing
│   └── main.py                       # FastAPI Application Factory, lifespan, CORS, healthcheck
├── docs/                             # Sample Test Artifacts
│   ├── sample-evidence-1.json        # Real-world AWS infrastructure telemetry evidence
│   └── sample-policy-1.pdf           # 2-page ACME Cloud Infrastructure Security policy PDF
├── test/                             # Automated Test Suites
│   ├── api/                          # End-to-end API integration tests (test_v1.py)
│   ├── db/                           # Database session and repository tests (test_session.py)
│   └── services/                     # Extractor, Evaluator, and Compliance Service unit tests
├── docker-compose.yml                # Docker Compose definition (PostgreSQL & Adminer)
├── pyproject.toml                    # UV project configuration and dependencies
└── README.md                         # Root Technical Specification & Documentation
```

---

## 🚀 7. Quickstart & Execution Guide

### Prerequisites
- Python $\ge$ 3.14
- Docker & Docker Compose
- `uv` package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### 1. Environment Configuration
Create a `.env` file in the root directory:
```env
OPENROUTER_API_KEY="your_openrouter_api_key_here"
GEMINI_API_KEY="your_gemini_api_key_here"
LLM_PROVIDER="gemini"
DATABASE_URL="postgresql+asyncpg://compliance_user:compliance_password@localhost:5432/compliance_db"
```

### 2. Start PostgreSQL Database
```bash
docker compose up -d
```

### 3. Install Dependencies & Run Backend Server
```bash
# Sync dependencies in virtual environment
uv sync

# Run FastAPI development server with hot-reload
uv run uvicorn app.main:app --reload --port 8000
```

### 4. Interactive Documentation
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 5. Running the Automated Test Suite
```bash
uv run pytest -v
```
All **20 test cases** across API routes, database sessions, LLM extraction, and compliance evaluation execute and validate in $\approx 20\text{s}$.