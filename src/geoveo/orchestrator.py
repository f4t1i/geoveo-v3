"""Central pipeline controller that chains providers, services, and backends.

The orchestrator accepts optional provider overrides for testing and
falls back to config-driven factory resolution when none are supplied.
"""

from pathlib import Path
from uuid import uuid4

from geoveo.backends.factory import get_backend
from geoveo.models import GeoVeoJob, PlannedJob, RunResult
from geoveo.providers.base import BaseRoutingProvider, BaseImageryProvider, BaseDepthProvider
from geoveo.providers.factory import get_routing_provider, get_imagery_provider, get_depth_provider
from geoveo.services.conditioning import ConditioningService
from geoveo.services.evaluation import EvaluationService


class Orchestrator:
    """Orchestrate the full geo-conditioned video generation pipeline.

    Parameters
    ----------
    routing_provider : BaseRoutingProvider | None
        Override for the routing provider.  Resolved from config when *None*.
    imagery_provider : BaseImageryProvider | None
        Override for the imagery provider.  Resolved from config when *None*.
    depth_provider : BaseDepthProvider | None
        Override for the depth provider.  Resolved from config when *None*.
    """

    def __init__(
        self,
        routing_provider: BaseRoutingProvider | None = None,
        imagery_provider: BaseImageryProvider | None = None,
        depth_provider: BaseDepthProvider | None = None,
    ) -> None:
        self.routing = routing_provider or get_routing_provider()
        self.imagery = imagery_provider or get_imagery_provider()
        self.depth = depth_provider or get_depth_provider()
        self.conditioning = ConditioningService()
        self.evaluation = EvaluationService()

    def plan(self, job: GeoVeoJob, out_dir: str) -> PlannedJob:
        """Execute the planning phase: route → imagery → depth → bundle."""
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)

        route_id = f"route_{uuid4().hex[:8]}"
        route = self.routing.plan_route(job)
        keyframes = self.imagery.fetch_keyframes(route, out)
        depth_maps = self.depth.estimate_depth(keyframes, out)
        bundle = self.conditioning.build_bundle(route_id, route, keyframes, depth_maps, out)

        return PlannedJob(
            route_id=route_id,
            route=route,
            keyframe_paths=keyframes,
            conditioning_bundle_path=bundle,
        )

    def run(self, job: GeoVeoJob, out_dir: str) -> RunResult:
        """Execute the full pipeline: plan → render → evaluate."""
        planned = self.plan(job, out_dir)
        backend = get_backend(job.video_backend)
        output_video = backend.render(job.prompt, planned.conditioning_bundle_path, out_dir)
        metrics = self.evaluation.evaluate(output_video, planned)

        return RunResult(
            job_id=planned.route_id.replace("route_", "job_"),
            status="done",
            output_video=output_video,
            metadata={"planned_route_id": planned.route_id, "evaluation": metrics},
        )
