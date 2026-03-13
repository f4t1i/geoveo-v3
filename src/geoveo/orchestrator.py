from pathlib import Path
from uuid import uuid4
from geoveo.models import GeoVeoJob, PlannedJob, RunResult
from geoveo.services.routing import RoutingService
from geoveo.services.imagery import ImageryService
from geoveo.services.conditioning import ConditioningService
from geoveo.services.evaluation import EvaluationService
from geoveo.backends.factory import get_backend

class Orchestrator:
    def __init__(self) -> None:
        self.routing = RoutingService()
        self.imagery = ImageryService()
        self.conditioning = ConditioningService()
        self.evaluation = EvaluationService()

    def plan(self, job: GeoVeoJob, out_dir: str) -> PlannedJob:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        route_id = f"route_{uuid4().hex[:8]}"
        route = self.routing.plan_route(job)
        keyframes = self.imagery.fetch_keyframes(route, out)
        bundle = self.conditioning.build_bundle(route_id, route, keyframes, out)
        return PlannedJob(
            route_id=route_id,
            route=route,
            keyframe_paths=keyframes,
            conditioning_bundle_path=bundle,
        )

    def run(self, job: GeoVeoJob, out_dir: str) -> RunResult:
        planned = self.plan(job, out_dir)
        backend = get_backend(job.video_backend)
        output_video = backend.render(job.prompt, planned.conditioning_bundle_path, out_dir)
        metrics = self.evaluation.evaluate(output_video)
        return RunResult(
            job_id=planned.route_id.replace("route_", "job_"),
            status="done",
            output_video=output_video,
            metadata={"planned_route_id": planned.route_id, "evaluation": metrics},
        )
