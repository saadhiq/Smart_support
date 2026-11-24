"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.classifier import get_model
from app.config import get_settings
from app.db import create_db_and_tables
from app.routers import api, pages


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """On startup: create tables and load the model once."""
    create_db_and_tables()
    get_model()
    yield


def field_name(loc: tuple) -> str:
    """Turn a Pydantic error location like ('body', 'email') into 'email'."""
    parts = [str(p) for p in loc if p not in ("body", "query", "path")]
    return ".".join(parts) or "body"


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Return 422 with one short, readable message per invalid field."""
    errors = [{"field": field_name(tuple(e["loc"])), "message": e["msg"]} for e in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": "Invalid input.", "errors": errors},
    )


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    settings = get_settings()
    app = FastAPI(title="Smart Support Desk", lifespan=lifespan)
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret,
                       same_site="lax", max_age=8 * 60 * 60)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.include_router(api.router)
    app.include_router(pages.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Return a simple liveness status."""
        return {"status": "ok"}

    return app


app = create_app()
