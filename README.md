# munchai-backend

Security-first FastAPI backend for **munch.ai** with MongoDB and Docker Compose.

## Current architecture
- FastAPI REST API (`api` container)
- MongoDB (`mongo` container)
- Collections:
  - `users` (email_hash unique, username plaintext, password_hash)
  - `recipes` (CRUD documents)

## Security baseline
- API key protection (`x-api-key`)
- Basic per-IP rate limiting
- Redacted logs (no plain API keys/tokens)
- No plaintext password/email persisted in DB
- New users are created with `verified=false`; login only for `verified=true`
- Placeholder verification-mail sender is wired on registration (non-functional by design)
- CORS allowlist via env

## Endpoints (REST)
- `GET /health`
- `POST /api/v1/auth/login`
- `POST /api/v1/users`
- `GET /api/v1/users/{id}`
- `PATCH /api/v1/users/{id}`
- `POST /api/v1/users/{id}/verify` (sets `verified=true`)
- `DELETE /api/v1/users/{id}`
- `POST /api/v1/recipes`
- `GET /api/v1/recipes`
- `GET /api/v1/recipes/{id}`
- `PUT /api/v1/recipes/{id}`
- `PATCH /api/v1/recipes/{id}`
- `DELETE /api/v1/recipes/{id}`

## Local run with Docker (recommended)

```bash
cp .env.example .env
docker compose up --build -d
```

Health checks:

```bash
curl http://localhost:8080/health
curl -H "x-api-key: change-me" http://localhost:8080/api/v1/recipes
```

Stop:

```bash
docker compose down
```

## Tests

### Docker-backed tests (Mongo required)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# start mongo only for tests
docker compose up -d mongo
pytest -q
```

## Notes for frontend integration
- Use `x-api-key` header on all `/api/v1/*` routes except `/health`.
- API base URL for local frontend: `http://localhost:8080`.
