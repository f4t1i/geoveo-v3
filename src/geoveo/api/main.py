"""FastAPI application factory for GeoVeo.

Configures structured logging on startup and includes request logging
middleware for observability.
"""

import time

from fastapi import FastAPI, Request, Response

from geoveo.api.routers.health import router as health_router
from geoveo.api.routers.jobs import router as jobs_router
from geoveo.config import settings
from geoveo.logging import configure_logging, get_logger

configure_logging(settings.geoveo_log_level)
log = get_logger(__name__)

app = FastAPI(title="GeoVeo API", version="0.3.0")
app.include_router(health_router)
app.include_router(jobs_router)


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
