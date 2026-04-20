import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db_mongo import close_client, ensure_indexes, get_client
from app.logging_setup import configure_logging
from app.routes import auth, health, recipes, users

configure_logging(settings.log_level)
logger = logging.getLogger("munchai-backend")

app = FastAPI(title="munchai-backend", version="0.2.0")

origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    get_client().admin.command("ping")
    ensure_indexes()


@app.on_event("shutdown")
def on_shutdown() -> None:
    close_client()


@app.middleware("http")
async def request_log_middleware(request: Request, call_next):
    response = await call_next(request)
    logger.info(
        "request method=%s path=%s status=%s",
        request.method,
        request.url.path,
        response.status_code,
    )
    return response


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(recipes.router)
