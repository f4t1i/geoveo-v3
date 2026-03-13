"""Central pipeline controller that chains providers, services, and backends.

The orchestrator accepts optional provider overrides for testing and
falls back to config-driven factory resolution when none are supplied.
"""

import time
from pathlib import Path
from uuid import uuid4

from geoveo.backends.factory import get_backend
from geoveo.logging import get_logger
from geoveo.models import GeoVeoJob, PlannedJob, RunResult
from geoveo.providers.base import BaseRoutingProvider, BaseImageryProvider, BaseDepthProvider
from geoveo.providers.factory import get_routing_provider, get_imagery_provider, get_depth_provider
from geoveo.services.conditioning import ConditioningService
from geoveo.services.evaluation import EvaluationService

log = get_logger(__name__)


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

        log.info(
            "orchestrator.init",
            routing_provider=self.routing.name,
            imagery_provider=self.imagery.name,
            depth_provider=self.depth.name,
        )

    def plan(self, job: GeoVeoJob, out_dir: str) -> PlannedJob:
        """Execute the planning phase: route → imagery → depth → bundle."""
        t0 = time.monotonic()
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)

        route_id = f"route_{uuid4().hex[:8]}"
        log.info("plan.start", route_id=route_id, location=job.location, mode=job.mode)

        route = self.routing.plan_route(job)
        log.info("plan.route_done", route_id=route_id, waypoints=len(route))

        keyframes = self.imagery.fetch_keyframes(route, out)
        log.info("plan.imagery_done", route_id=route_id, keyframes=len(keyframes))

        depth_maps = self.depth.estimate_depth(keyframes, out)
        log.info("plan.depth_done", route_id=route_id, depth_maps=len(depth_maps))

        bundle = self.conditioning.build_bundle(route_id, route, keyframes, depth_maps, out)
        elapsed = time.monotonic() - t0
        log.info("plan.complete", route_id=route_id, bundle=bundle, elapsed_s=round(elapsed, 3))

        return PlannedJob(
            route_id=route_id,
            route=route,
            keyframe_paths=keyframes,
            conditioning_bundle_path=bundle,
        )

    def run(self, job: GeoVeoJob, out_dir: str) -> RunResult:
        """Execute the full pipeline: plan → render → evaluate."""
        t0 = time.monotonic()
        log.info("run.start", location=job.location, backend=job.video_backend)

        planned = self.plan(job, out_dir)

        backend = get_backend(job.video_backend)
        log.info("run.render_start", backend=backend.__class__.__name__)
        output_video = backend.render(job.prompt, planned.conditioning_bundle_path, out_dir)
        log.info("run.render_done", output_video=output_video)

        metrics = self.evaluation.evaluate(output_video, planned)
        elapsed = time.monotonic() - t0
        log.info("run.complete", job_id=planned.route_id.replace("route_", "job_"), elapsed_s=round(elapsed, 3))

        return RunResult(
            job_id=planned.route_id.replace("route_", "job_"),
            status="done",
            output_video=output_video,
            metadata={"planned_route_id": planned.route_id, "evaluation": metrics},
        )
