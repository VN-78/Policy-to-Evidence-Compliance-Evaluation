# API Integration Tests (`test/api/`)

This folder contains integration tests for the HTTP route layer of our application. These tests simulate client requests and verify the server's responses, including status codes, JSON structure, and behavior logic.

## 📂 Current Test Files

* **[`test_v1.py`](file:///home/vn-78/Projects/code/fastapi-base-template/test/api/test_v1.py)**: Test cases verifying the v1 endpoints.

## 🚀 How to Write API Tests

API tests should use `fastapi.testclient.TestClient`. A simple test looks like this:

```python
from fastapi.testclient import TestClient
from app.main import app

# Initialize the test client with our application instance
client = TestClient(app)

def test_endpoint_success():
    # 1. Arrange (setup payload)
    payload = {"username": "vishwa", "email": "vishwa@archlinux.org"}
    
    # 2. Act (send requests)
    response = client.post("/api/v1/users/", json=payload)
    
    # 3. Assert (validate expectations)
    assert response.status_code == 200
    assert response.json()["username"] == "vishwa"
```

## 🛠️ Testing Best Practices

1. **Test Success and Failure Paths**: For every endpoint, write at least one test for success (e.g. status code 200/201) and tests for common failure cases (e.g. status code 400 Bad Request for duplicate values or 422 Unprocessable Entity for invalid schemas).
2. **Database State Cleanup**: Ensure that tests do not leak state to subsequent tests. If the test mutates data, reset/clean the database session after each test runs.
3. **Use Descriptors/Tags**: Keep tests focused on a single logical assertion to make debugging simpler when a test fails.
