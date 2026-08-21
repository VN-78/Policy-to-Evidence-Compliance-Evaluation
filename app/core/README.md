# Core Layer (`app/core/`)

This directory houses cross-cutting application configurations, environment variable management, and the multi-provider LLM client abstraction.

---

## 📁 Files & Responsibilities

### 1. `config.py` ([`app/core/config.py`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/app/core/config.py))
- Manages application-wide settings using `pydantic-settings.BaseSettings`.
- Resolves the root `.env` file path reliably regardless of the current working directory.
- Configurable settings:
  - `openrouter_api_key`: API key for OpenRouter fallback.
  - `gemini_api_key`: API key for Google Gemini GenAI.
  - `LLM_PROVIDER`: Active backend provider (`"gemini"` or `"openrouter"`).
  - `database_url`: PostgreSQL async connection string (`postgresql+asyncpg://...`).
  - `PROJECT_NAME`: Application service name.

### 2. `llm.py` ([`app/core/llm.py`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/app/core/llm.py))
- Provides a centralized, modular abstraction over LLM providers:
  - **Google Gemini Provider**: Uses the modern `google-genai` SDK (`genai.Client`) with model fallback sequences (`gemini-3.7-flash`, `gemini-3.6-flash`) and `response_mime_type="application/json"`.
  - **OpenRouter Provider**: Uses `AsyncOpenAI` configured with provider sorting, automatic failovers, and throughput optimization.
- Function: `generate_structured_json(prompt: str, system_instruction: str, provider: str | None = None) -> str`
  - Dynamically routes requests according to `settings.LLM_PROVIDER`.
  - Manages clean client session teardown (`aclose()`) to prevent resource leaks.