"""FastAPI application factory and lifecycle management."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.database import engine
from app.domain.exceptions import DomainError, ForbiddenError, NotFoundError

logger = logging.getLogger("gym-bro")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """
    Arg: app - the FastAPI application instance.
    Operation: yields for the lifetime of the process, then disposes the database engine.
               Schema migration and seeding deliberately happen in the container
               entrypoint instead, so they run once rather than once per uvicorn worker.
    Return: async context manager yielding None.
    """
    logger.info("Starting up…")
    yield
    await engine.dispose()


app = FastAPI(
    title="Gym Bro API",
    version="1.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


# ── Exception handlers — translate domain errors to HTTP responses ─────────────


@app.exception_handler(NotFoundError)
async def handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
    """
    Arg: request - incoming request; exc - NotFoundError raised by a use case.
    Operation: translates the domain exception into a 404 JSON response.
    Return: JSONResponse with status 404 and the exception detail.
    """
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ForbiddenError)
async def handle_forbidden(request: Request, exc: ForbiddenError) -> JSONResponse:
    """
    Arg: request - incoming request; exc - ForbiddenError raised by a use case.
    Operation: translates the domain exception into a 403 JSON response.
    Return: JSONResponse with status 403 and the exception detail.
    """
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(DomainError)
async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    """
    Arg: request - incoming request; exc - any unhandled DomainError subclass.
    Operation: translates unspecialised domain errors into a 422 JSON response.
    Return: JSONResponse with status 422 and the exception detail.
    """
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/health")
async def health() -> JSONResponse:
    """
    Arg: none.
    Operation: returns a simple liveness check payload.
    Return: JSONResponse with status 200 and {"status": "ok"}.
    """
    return JSONResponse({"status": "ok"})
