# Application Source (`app/`)

This directory houses the core application code for the FastAPI backend. It is structured to maintain a clean separation of concerns and to make scaling straightforward.

## 📁 Subdirectory Roles

Here is a breakdown of what belongs in each subdirectory:

| Folder | Name | Purpose | Key Guidelines |
|---|---|---|---|
| [`api/`](file:///home/vn-78/Projects/code/fastapi-base-template/app/api) | **API Layer** | Versioned HTTP routing and request validation | Thin routers. Avoid business or DB logic here. Use dependency injection. |
| [`core/`](file:///home/vn-78/Projects/code/fastapi-base-template/app/core) | **Core Configuration** | Environment configurations and security | Settings management (`config.py`), security/hashing, client initialization. |
| [`db/`](file:///home/vn-78/Projects/code/fastapi-base-template/app/db) | **Database Layer** | Database session lifecycle and ORM definitions | Engine configuration, session management, and SQLAlchemy models. |
| [`models/`](file:///home/vn-78/Projects/code/fastapi-base-template/app/models) | **Pydantic Models** | Data contracts (validation & serialization) | Request validation schemas, response schemas. Keep DB elements OUT. |
| [`repositories/`](file:///home/vn-78/Projects/code/fastapi-base-template/app/repositories) | **Repository Layer** | Raw data operations and queries | Strictly CRUD operations. Accepts/returns schemas or ORM objects. |
| [`services/`](file:///home/vn-78/Projects/code/fastapi-base-template/app/services) | **Service Layer** | Core business logic and external integrations | Framework-agnostic. Integrations, rules, computations live here. |
| [`utils/`](file:///home/vn-78/Projects/code/fastapi-base-template/app/utils) | **Utilities** | Stateless, pure helper functions | No DB/API calls. Time formatting, string helpers, and validators. |

## 🚀 Entry Point

The application starts at [`app/main.py`](file:///home/vn-78/Projects/code/fastapi-base-template/app/main.py), which uses the **Application Factory** pattern (`create_app()`). This ensures the app is easily testable because we can instantiate separate instances of the app with different settings during testing.

## 🛠️ Code Conventions & Design Goals

1. **Strict Layers**: Direct database queries must not be done in the API layer or the Service layer. They belong exclusively in the Repositories.
2. **Type Annotations**: All function signatures must be fully typed. Use Python type hints to aid IDE autocomplete and static type checkers like `mypy`.
3. **Clean Imports**: Import from the root of the app namespace (e.g. `from app.core.config import settings`) rather than using relative paths (e.g. `from ..core.config import settings`) where possible to avoid complex relative import issues.
