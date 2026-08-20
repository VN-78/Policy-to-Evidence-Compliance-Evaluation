from typing import Any
from fastapi.testclient import TestClient
from httpx2 import Response

from app.main import app

client = TestClient(app)


def test_create_user_success() -> None:
    payload = {
        "username": "vishwa",
        "email": "vishwa@archlinux.org"
    }
    
    response: Response = client.post("/api/v1/users/", json=payload)
    
    # 1. Verify HTTP status
    assert response.status_code == 200
    
    # 2. Verify data contract
    data: dict[str, Any] = response.json()
    assert data["username"] == "vishwa"
    assert data["email"] == "vishwa@archlinux.org"
    assert "id" in data  # Ensure our service generated the ID