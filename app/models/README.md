# Pydantic Models (`app/models/`)

**Purpose:**
Defines the Pydantic schemas for request validation and response serialization.

**Rules:**
- Separate models into specific files (e.g., `requests.py`, `responses.py`, or by domain like `user_models.py`).
- Keep database ORM definitions OUT of this folder.
- Use these schemas strictly in the `app/api/` routes to enforce strict API contracts.