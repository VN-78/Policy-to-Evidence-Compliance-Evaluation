# Test Suite (`test/`)

This directory contains automated unit and integration tests for the FastAPI application. The test suite uses **`pytest`** to ensure code reliability and contract adherence.

## 📁 Directory Structure

```text
test/
├── api/
│   ├── README.md       # API-specific test documentation
│   └── test_v1.py      # Integration tests for v1 endpoints
└── README.md           # This file
```

## 🚀 Running Tests

All commands should be executed from the root of the workspace using `uv run`.

### Run All Tests
```bash
uv run pytest
```

### Run in Verbose Mode (lists each test name and outcome)
```bash
uv run pytest -v
```

### Run Tests in a Specific File
```bash
uv run pytest test/api/test_v1.py
```

### Run Tests and View Print/StdOut Statements (`-s`)
```bash
uv run pytest -s
```

## 🛠️ Guidelines for Writing Tests

1. **Discovery Patterns**: `pytest` looks for files matching `test_*.py` or `*_test.py`, and functions prefixed with `test_`. Follow this naming convention strictly to ensure tests are discovered.
2. **Use `TestClient` for API Tests**: Import `TestClient` from `fastapi.testclient` and pass the FastAPI app instance to mock API requests. This handles routing and schema validation without needing a running server process.
3. **Database Test Isolation**: For tests requiring a database connection, use a dedicated test database (e.g. SQLite in-memory or a separate PostgreSQL container) and override dependencies using `app.dependency_overrides`.
4. **Mocking External Services**: Mock third-party APIs (like OpenAI, Stripe, etc.) or complex calculations using `unittest.mock` or pytest fixtures to keep tests fast, reliable, and offline-compatible.
