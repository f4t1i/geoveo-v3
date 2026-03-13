"""FastAPI application factory for GeoVeo.

Configures structured logging on startup and includes request logging
middleware and global exception handlers for observability.
"""

import time

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from geoveo.api.routers.health import router as health_router
from geoveo.api.routers.jobs import router as jobs_router
from geoveo.config import settings
from geoveo.exceptions import (
    BackendError,
    GeoVeoError,
    JobValidationError,
    PipelineError,
    ProviderError,
)
from geoveo.logging import configure_logging, get_logger

configure_logging(settings.geoveo_log_level)
log = get_logger(__name__)

app = FastAPI(title="GeoVeo API", version="0.3.0")
app.include_router(health_router)
app.include_router(jobs_router)


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(JobValidationError)
async def handle_validation_error(request: Request, exc: JobValidationError) -> JSONResponse:
    log.warning("api.validation_error", path=request.url.path, error=exc.message)
    return JSONResponse(status_code=422, content=exc.to_dict())


@app.exception_handler(ProviderError)
async def handle_provider_error(request: Request, exc: ProviderError) -> JSONResponse:
    log.error("api.provider_error", path=request.url.path, provider=exc.provider, error=exc.message)
    return JSONResponse(status_code=502, content=exc.to_dict())


@app.exception_handler(BackendError)
async def handle_backend_error(request: Request, exc: BackendError) -> JSONResponse:
    log.error("api.backend_error", path=request.url.path, backend=exc.backend, error=exc.message)
    return JSONResponse(status_code=502, content=exc.to_dict())


@app.exception_handler(PipelineError)
async def handle_pipeline_error(request: Request, exc: PipelineError) -> JSONResponse:
    log.error("api.pipeline_error", path=request.url.path, stage=exc.stage, error=exc.message)
    return JSONResponse(
        status_code=500,
        content={**exc.to_dict(), "partial_artifacts": exc.partial_artifacts},
    )


@app.exception_handler(GeoVeoError)
async def handle_geoveo_error(request: Request, exc: GeoVeoError) -> JSONResponse:
    log.error("api.geoveo_error", path=request.url.path, error=exc.message)
    return JSONResponse(status_code=500, content=exc.to_dict())


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next) -> Response:
    """Log every incoming request with method, path, status, and timing."""
    t0 = time.monotonic()
    response: Response = await call_next(request)
    elapsed = time.monotonic() - t0
    log.info(
        "http.request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        elapsed_s=round(elapsed, 4),
    )
    return response


@app.on_event("startup")
async def on_startup() -> None:
    log.info("api.startup", version="0.3.0", env=settings.geoveo_env)
