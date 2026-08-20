# API Layer (`app/api/`)

**Purpose:** 
Contains FastAPI routers and endpoint definitions. This is the HTTP delivery mechanism.

**Rules:**
- **Thin Routers:** Do NOT put business logic, AI prompt generation, or database calls here.
- **Dependency Injection:** Use FastAPI's `Depends()` to inject Services and Database sessions into the routes.
- **Contract:** Endpoints must accept and return strictly defined Pydantic schemas from the `app/models/` directory.

```
app/api/
├── __init__.py
├── README.md
├── v1/
│   ├── __init__.py
│   ├── users.py      <-- v1 endpoints
│   └── products.py   <-- v1 endpoints
└── v2/
    ├── __init__.py
    └── users.py      <-- v2 endpoints (with new features)
```