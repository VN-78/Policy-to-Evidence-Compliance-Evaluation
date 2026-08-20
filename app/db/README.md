# Database Setup (`app/db/`)

**Purpose:**
Database engine initialization, session management, and SQLAlchemy models.

**Rules:**
- `session.py`: Define the SQLAlchemy `engine`, connection pooling, and the `get_db` dependency for FastAPI.
- `models.py`: Define your SQLAlchemy ORM classes (the actual database tables) here. Do NOT confuse these with the Pydantic schemas in `app/models/`.
- Ensure connection strings are loaded securely via environment variables using `app/core/config.py`.