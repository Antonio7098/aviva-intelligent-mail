# API Documentation

Aviva Intelligent Mail (AIM) provides a FastAPI-based REST API. Interactive API documentation is available via:

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

---

## Base URL

```
http://localhost:8000
```

---

## Endpoints

### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Basic liveness check |
| `GET` | `/ready` | Readiness check with database validation |

#### GET /health

Basic health check endpoint. Returns `200 OK` if the application is running.

**Response**

```json
{
  "status": "ok"
}
```

---

#### GET /ready

Readiness check that verifies:
- Database connection is established
- Database migrations have been applied

**Response (200 OK)**

```json
{
  "status": "ready",
  "database": "connected",
  "migrations": "applied"
}
```

**Response (503 Service Unavailable)**

```json
{
  "status": "not_ready",
  "reason": "database not connected"
}
```

Possible reasons:
- `database not connected` - Database connection failed
- `database connection lost` - Previously connected database disconnected
- `migrations not applied` - Database tables not created
- `failed to verify migrations` - Migration check query failed

---

## Authentication

Currently, the API does not implement authentication. In production, integrate with Azure AD or similar identity provider.

---

## Rate Limiting

Not currently implemented. Add API gateway rate limiting for production use.

---

## Error Responses

All endpoints may return:

| Status Code | Description |
|-------------|-------------|
| `500` | Internal server error |
| `422` | Validation error (Pydantic) |

---

## SDK / Client Usage

### Python (httpx)

```python
import httpx

async def check_health():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        return response.json()
```

### cURL

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

---

## OpenAPI Schema

Full OpenAPI 3.0 schema available at:
- `/openapi.json`
- `/docs` (Swagger UI)
- `/redoc` (ReDoc)
