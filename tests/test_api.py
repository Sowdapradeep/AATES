from fastapi.testclient import TestClient

def test_health(client: TestClient) -> None:
    """Verifies that the API GET /health endpoint returns HTTP 200 status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_live(client: TestClient) -> None:
    """Verifies liveness GET /live probe endpoint returns HTTP 200 status."""
    response = client.get("/live")
    assert response.status_code == 200
    assert response.json() == {"liveness": "alive"}

def test_version(client: TestClient) -> None:
    """Verifies application release meta values are readable from /version."""
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()

def test_auth_register_and_login(client: TestClient) -> None:
    """Verifies registering a user profile and logging in using HttpOnly cookie mechanics."""
    reg_response = client.post(
        "/v1/auth/register",
        json={"email": "operator@aates.com", "password": "masterpassword"}
    )
    assert reg_response.status_code == 201
    assert "id" in reg_response.json()
    
    login_response = client.post(
        "/v1/auth/login",
        json={"email": "operator@aates.com", "password": "masterpassword"}
    )
    assert login_response.status_code == 200
    assert login_response.cookies.get("access_token") is not None
    assert login_response.cookies.get("refresh_token") is not None
