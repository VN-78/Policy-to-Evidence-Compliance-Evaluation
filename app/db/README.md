# Database Layer (`app/db/`)

This directory manages the asynchronous PostgreSQL database engine, connection pooling lifecycle, and SQLAlchemy 2.0 ORM declarative models.

---

## 📁 Files & Responsibilities

### 1. `session.py` ([`app/db/session.py`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/app/db/session.py))
- **Engine Setup**: Uses `create_async_engine(settings.database_url, poolclass=NullPool, pool_pre_ping=True)`.
  - `NullPool` ensures each async task or test execution receives a fresh, isolated connection and avoids event-loop connection collisions in `asyncpg`.
- **Session Factory**: `AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)`.
- **Bootstrap Hook**: `init_db()` executes `Base.metadata.create_all` on startup.
- **FastAPI Dependency**: `get_db()` yields a scoped `AsyncSession` with automatic commit and rollback error handling.

### 2. `models.py` ([`app/db/models.py`](file:///home/vn-78/Projects/code/Policy-to-Evidence-Compliance-Evaluation/app/db/models.py))
- **`PolicyModel` (`policies` table)**:
  - `id`: Primary key `UUID(as_uuid=True)`.
  - `name`: Policy title (`String(255)`).
  - `content_hash`: SHA-256 digest of normalized policy text (`String(64)`, `unique=True`, `index=True`).
  - `raw_text`: Full policy text (`Text`).
  - `created_at`: UTC timestamp.
  - `rules`: One-to-many relationship to `RuleModel` with cascade delete and `selectin` loading.
- **`RuleModel` (`rules` table)**:
  - `id`: Primary key `UUID(as_uuid=True)`.
  - `policy_id`: Foreign key to `policies.id` with `CASCADE` deletion.
  - `control_id`: Indexed identifier string (`String(100)`).
  - `title`, `target_asset_type`, `target_metric`, `operator`, `source_clause`, `page_number`.
  - `threshold_value`: Native PostgreSQL `JSONB` supporting polymorphic numbers, booleans, strings, and lists.
  - `pre_condition`: Native PostgreSQL `JSONB` for conditional evaluation triggers.
  - `is_active`: Boolean status flag.