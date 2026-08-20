# Repositories Layer (`app/repositories/`)

**Purpose:**
Handles direct data access and database operations.

**Rules:**
- **Strict Scope:** Write SQLAlchemy ORM queries or raw `psycopg2` SQL statements here.
- **Decoupled:** Accept primitive data or Pydantic models, execute the database transaction, and return the result to the Service layer.
- **No Business Logic:** Do not process AI prompts or validate business rules here. Just CRUD operations.