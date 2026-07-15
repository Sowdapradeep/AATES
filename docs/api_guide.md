# AATES API Endpoint Manual

All API routing is version-first. The prefix `/v1/` is applied to all business endpoints.

## 1. System Health Checks

### GET `/health`
Returns static confirmation that API service is online.
- **Response**: `{"status": "ok"}`

### GET `/live`
Standard Kubernetes liveness probe check.
- **Response**: `{"liveness": "alive"}`

### GET `/ready`
Tests connection pool health to PostgreSQL database and Redis cluster.
- **Response**: `{"readiness": "ready"}`
- **Errors**: `503 Service Unavailable` if database or cache is offline.

### GET `/metrics`
Exposes operational metrics values for scraping.
- **Response**:
  ```json
  {
    "system_cpu_usage_pct": 0.0,
    "system_memory_usage_pct": 0.0,
    "api_active_requests_count": 1.0,
    "api_latency_p95_ms": 12.5
  }
  ```

---

## 2. Authentication API

### POST `/v1/auth/register`
Creates a user account profile.
- **Body**:
  ```json
  {
    "email": "operator@aates.com",
    "password": "securepassword"
  }
  ```
- **Response**: `{"id": "<uuid>", "email": "operator@aates.com"}`

### POST `/v1/auth/login`
Authenticates credentials and injects HttpOnly cookies.
- **Body**:
  ```json
  {
    "email": "operator@aates.com",
    "password": "securepassword"
  }
  ```
- **Response Cookies**:
  - `access_token`: JWT token (valid for 30 minutes, HttpOnly, Secure, SameSite=Lax)
  - `refresh_token`: JWT token (valid for 7 days, HttpOnly, Secure, SameSite=Lax)

### POST `/v1/auth/refresh`
Reads `refresh_token` cookie and issues a fresh `access_token` cookie.
- **Response Cookies**:
  - `access_token`: fresh JWT token.

### POST `/v1/auth/logout`
Deletes access and refresh cookies from client.
