from pathlib import Path
from fastapi import APIRouter
from geoveo.models import GeoVeoJob
from geoveo.orchestrator import Orchestrator

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("/validate")
def validate_job(job: GeoVeoJob) -> dict:
    return {"status": "valid", "job": job.model_dump()}

@router.post("/plan")
def plan_job(job: GeoVeoJob) -> dict:
    out = "runs/api-plan"
    planned = Orchestrator().plan(job, out)
    Path(out).mkdir(parents=True, exist_ok=True)
    return planned.model_dump()

@router.post("/run")
def run_job(job: GeoVeoJob) -> dict:
    out = "runs/api-run"
    result = Orchestrator().run(job, out)
    Path(out).mkdir(parents=True, exist_ok=True)
    return result.model_dump()
