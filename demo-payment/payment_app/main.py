"""Сборка самостоятельного приложения и перевод ошибок в HTTP-ответы."""
import logging
from contextlib import asynccontextmanager
import httpx
import psycopg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .config import Settings, load_settings
from .controller.routes import router
from .repository.records import Repository
from .downstreams.clients import Downstreams
from .models.errors import RecordNotFound, InvalidData, DownstreamError, WorkflowError

logger = logging.getLogger("uvicorn.error")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else load_settings()

    @asynccontextmanager
    async def lifespan(app):
        # Один клиент на процесс. Таймаут внешнего сервиса больше внутреннего.
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.http_timeout, connect=3), trust_env=False
        ) as client:
            app.state.downstreams = Downstreams(client, settings)
            yield

    app = FastAPI(title="Payment Service", lifespan=lifespan)
    app.state.settings = settings
    app.state.repository = Repository(settings.database_url)
    app.state.delivery_address = settings.delivery_address
    # Здесь ошибки приложения переводятся в HTTP-ответы. Это позволяет
    # выполнять service в тестах или другом интерфейсе без веб-фреймворка.
    @app.exception_handler(RecordNotFound)
    async def not_found(request: Request, exc: RecordNotFound):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(InvalidData)
    async def invalid_data(request: Request, exc: InvalidData):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(DownstreamError)
    async def downstream_error(request: Request, exc: DownstreamError):
        detail = {"order_id": exc.order_id, "message": str(exc)} if isinstance(exc, WorkflowError) else str(exc)
        return JSONResponse(status_code=502, content={"detail": detail})

    @app.exception_handler(psycopg.Error)
    async def database_error(request: Request, exc: psycopg.Error):
        logger.exception("Ошибка базы сервиса payment")
        return JSONResponse(status_code=503, content={"detail": "База данных недоступна или отклонила запрос"})

    app.include_router(router)
    return app


app = create_app()
