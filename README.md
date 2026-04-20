# munchai-backend

Security-first FastAPI backend for **munch.ai** with MongoDB and Docker Compose.

## Current architecture
- FastAPI REST API (`api` container)
- MongoDB (`mongo` container)
- Collections:
  - `users`: username (plaintext), email_hash (unique), password_hash, verified, taste_profile
  - `recipes`: user-owned recipe documents
  - `sessions`: hashed bearer tokens with sliding expiration

## Security baseline
- Bearer token auth on protected API routes
- Token TTL: 24h with sliding renewal on each authenticated request
- Logout revokes current token immediately
- Email + password are never stored in plaintext
- Per-IP rate limiting
- Redacted logs (no plaintext secrets)

## Environment
Copy and edit local env:

```bash
cp .env.example .env
```

Required AI provider keys (for future AI integration):
- `TEXT_MODEL_API_KEY`
- `IMAGE_MODEL_API_KEY`

## Endpoints (REST)
Public:
- `GET /health`
- `POST /api/v1/users` (register; creates `verified=false`)
- `POST /api/v1/auth/verify-account` (placeholder verification action)
- `POST /api/v1/auth/login`

Authenticated (Bearer):
- `POST /api/v1/auth/logout`
- `GET /api/v1/users/{id}`
- `PATCH /api/v1/users/{id}`
- `POST /api/v1/users/{id}/verify`
- `POST /api/v1/users/{id}/bootstrap-recipes` (one-time; generates 15 placeholder recipes)
- `DELETE /api/v1/users/{id}`
- `POST /api/v1/recipes`
- `GET /api/v1/recipes`
- `GET /api/v1/recipes/{id}`
- `PUT /api/v1/recipes/{id}`
- `PATCH /api/v1/recipes/{id}`
- `DELETE /api/v1/recipes/{id}`

## Local run with Docker (recommended)

```bash
docker compose up --build -d
```

Health:

```bash
curl http://localhost:8080/health
```

## Auth flow example

```bash
# Register
curl -X POST http://localhost:8080/api/v1/users \
  -H 'content-type: application/json' \
  -d '{"username":"dave","email":"dave@example.com","password":"supersecret1","taste_profile":"umami, spicy, quick"}'

# Verify (placeholder)
curl -X POST http://localhost:8080/api/v1/auth/verify-account \
  -H 'content-type: application/json' \
  -d '{"email":"dave@example.com"}'

# Login
TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"dave@example.com","password":"supersecret1"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["token"])')

# Use authenticated endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/v1/recipes

# Logout
curl -X POST -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/v1/auth/logout
```

## Tests

### Non-container local tests (venv required)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d mongo
pytest -q
docker compose down
```

### Container notes
- No additional Python venv is used inside Docker containers.
