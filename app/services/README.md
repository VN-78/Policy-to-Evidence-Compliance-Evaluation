# Services Layer (`app/services/`)

**Purpose:**
Houses the core business logic, AI integrations, and prompt processing.

**Rules:**
- **No HTTP/FastAPI imports:** This layer should not know about HTTP requests or responses.
- **AI Integration:** OpenAI API calls, LangChain wrappers, or custom prompt processing functions live here.
- **Data Fetching:** Services must call functions from `app/repositories/` to get or save data. Do not write SQL queries here.