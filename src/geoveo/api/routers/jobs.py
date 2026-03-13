"""Async job endpoints for the GeoVeo API.

All orchestrator calls are wrapped with ``asyncio.to_thread()`` so they
run in a thread pool and don't block the event loop.  This is essential
when real providers make network calls that take seconds or minutes.
"""

import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from geoveo.logging import get_logger
from geoveo.models import GeoVeoJob
from geoveo.orchestrator import Orchestrator

log = get_logger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])

# In-memory job status store (replace with Redis/DB for production)
_job_status: dict[str, dict] = {}


@router.post("/validate")
async def validate_job(job: GeoVeoJob) -> dict:
    """Validate a job payload and return the parsed model."""
    return {"status": "valid", "job": job.model_dump()}


@router.post("/plan")
async def plan_job(job: GeoVeoJob) -> dict:
    """Execute the planning phase asynchronously."""
    run_id = uuid4().hex[:8]
    out = f"runs/api-plan-{run_id}"

    def _plan() -> dict:
        return Orchestrator().plan(job, out).model_dump()

    try:
        result = await asyncio.to_thread(_plan)
        Path(out, "planned_job.json").write_text(
            str(result), encoding="utf-8"
        )
        return result
    except Exception as exc:
        log.error("api.plan.error", error=str(exc), run_id=run_id)
        raise HTTPException(status_code=500, detail={
            "error": "PlanningFailed",
            "message": str(exc),
            "run_id": run_id,
        })


@router.post("/run")
async def run_job(job: GeoVeoJob) -> dict:
    """Execute the full pipeline asynchronously."""
    run_id = uuid4().hex[:8]
    out = f"runs/api-run-{run_id}"

    # Track job status
    _job_status[run_id] = {"status": "running", "run_id": run_id}

    def _run() -> dict:
        return Orchestrator().run(job, out).model_dump()

    try:
        result = await asyncio.to_thread(_run)
        _job_status[run_id] = {"status": "done", "run_id": run_id, "result": result}
        return result
    except Exception as exc:
        _job_status[run_id] = {"status": "failed", "run_id": run_id, "error": str(exc)}
        log.error("api.run.error", error=str(exc), run_id=run_id)
        raise HTTPException(status_code=500, detail={
            "error": "RunFailed",
            "message": str(exc),
            "run_id": run_id,
        })


@router.get("/status/{run_id}")
async def get_job_status(run_id: str) -> dict:
    """Query the status of a previously submitted job.

    This is a stub for future async job tracking.  Currently only tracks
    jobs submitted during the current server lifetime.
    """
    if run_id not in _job_status:
        raise HTTPException(status_code=404, detail={
            "error": "JobNotFound",
            "message": f"No job found with run_id={run_id!r}",
        })
    return _job_status[run_id]
