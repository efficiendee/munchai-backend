# munchai-backend

Security-first FastAPI backend draft for **munch.ai** frontend integration.

## Security principles
- API key protection on app endpoints (`x-api-key` header)
- Basic per-IP rate limiting
- Log redaction for sensitive patterns
- No secrets committed to git

## Quickstart (local)

```bash
cd projects/munchai-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Start service:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Open docs:
- http://localhost:8080/docs

## Frontend integration
Use these endpoints from munchai frontend:
- `GET /health`
- `POST /api/v1/auth/login`
- `GET /api/v1/recipes`

Example request with API key:

```bash
curl -H "x-api-key: change-me" http://localhost:8080/api/v1/recipes
```

## Tests

```bash
pytest -q
```

## Planned next steps
- Replace dummy repository with persistent DB + service layer
- Add JWT auth with rotation
- Add structured audit logging + request ids
- Add CI pipeline + SAST/Dependency scanning
