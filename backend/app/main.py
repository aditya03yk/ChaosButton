"""ChaosButton FastAPI application factory."""
import logging
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.ai.provider import AIProvider
from app.api import experiments, proxy, reports, system, targets
from app.container import build_container
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.storage import database
from app.storage.repositories import ExperimentRepository

logger = logging.getLogger(__name__)


def create_app(settings: Optional[Settings] = None, http_client: Optional[httpx.AsyncClient] = None,
               ai_provider: Optional[AIProvider] = None) -> FastAPI:
    settings = settings or get_settings()
    container = build_container(settings, http_client, ai_provider)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        configure_logging()
        database.configure(settings.database_url)
        with database.session_scope() as session:
            interrupted = ExperimentRepository(session).mark_interrupted()
        if interrupted:
            logger.warning("marked %s interrupted experiment(s) as FAILED", interrupted)
        yield
        await container.orchestrator.shutdown()
        await container.http.aclose()

    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan,
                  description="Break it before your users do.")
    app.state.container = container
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"],
                       allow_headers=["*"])

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message, "code": exc.code})

    @app.exception_handler(Exception)
    async def unhandled_handler(_: Request, exc: Exception):
        logger.exception("unhandled error: %s", type(exc).__name__)
        return JSONResponse(status_code=500, content={"detail": "Internal server error", "code": "internal"})

    for router in (system.router, targets.router, experiments.router, reports.router, proxy.router):
        app.include_router(router)
    return app


app = create_app()
