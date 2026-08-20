# Core Configuration (`app/core/`)

**Purpose:**
Centralized location for cross-cutting application configurations and external client initializations.

**Rules:**
- `config.py`: Use Pydantic `BaseSettings` to load and validate environment variables (e.g., `DATABASE_URL`, `OPENAI_API_KEY`).
- `security.py`: JWT token generation, password hashing.
- `ai.py` (or similar): Initialize external clients (like the OpenAI client instance) here, so they can be imported and used cleanly by the `services/` layer without recreating the connection every time.