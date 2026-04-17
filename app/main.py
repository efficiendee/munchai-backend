import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_setup import configure_logging
from app.routes import auth, health, recipes

configure_logging(settings.log_level)
logger = logging.getLogger("munchai-backend")

app = FastAPI(title="munchai-backend", version="0.1.0")

origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
app.include_router(recipes.router)
