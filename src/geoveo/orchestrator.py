"""Central pipeline controller that chains providers, services, and backends.

The orchestrator accepts optional provider overrides for testing and
falls back to config-driven factory resolution when none are supplied.
Each pipeline stage is wrapped in error handling that preserves partial
artifacts on failure.
"""

import json
import time
from pathlib import Path
from uuid import uuid4

from geoveo.backends.factory import get_backend
from geoveo.exceptions import BackendError, PipelineError, ProviderError
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
        """Execute the planning phase: route -> imagery -> depth -> bundle.

        Each stage is wrapped in error handling.  On failure, a
        ``PipelineError`` is raised with ``partial_artifacts`` describing
        what was produced before the failure.
        """
        t0 = time.monotonic()
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)

        route_id = f"route_{uuid4().hex[:8]}"
        partial: dict = {"route_id": route_id, "out_dir": out_dir}
        log.info("plan.start", route_id=route_id, location=job.location, mode=job.mode)

        # Stage 1: Routing
        try:
            route = self.routing.plan_route(job)
            partial["waypoints"] = len(route)
            log.info("plan.route_done", route_id=route_id, waypoints=len(route))
        except Exception as exc:
            log.error("plan.route_failed", route_id=route_id, error=str(exc))
            raise ProviderError(
                f"Routing failed: {exc}", provider=self.routing.name, context=partial
            ) from exc

        # Stage 2: Imagery
        try:
            keyframes = self.imagery.fetch_keyframes(route, out)
            partial["keyframes"] = len(keyframes)
            log.info("plan.imagery_done", route_id=route_id, keyframes=len(keyframes))
        except Exception as exc:
            log.error("plan.imagery_failed", route_id=route_id, error=str(exc))
            raise ProviderError(
                f"Imagery fetch failed: {exc}", provider=self.imagery.name, context=partial
            ) from exc

        # Stage 3: Depth estimation
        try:
            depth_maps = self.depth.estimate_depth(keyframes, out)
            partial["depth_maps"] = len(depth_maps)
            log.info("plan.depth_done", route_id=route_id, depth_maps=len(depth_maps))
        except Exception as exc:
            log.error("plan.depth_failed", route_id=route_id, error=str(exc))
            raise ProviderError(
                f"Depth estimation failed: {exc}", provider=self.depth.name, context=partial
            ) from exc

        # Stage 4: Conditioning bundle
        try:
            bundle = self.conditioning.build_bundle(route_id, route, keyframes, depth_maps, out)
            partial["bundle"] = bundle
        except Exception as exc:
            log.error("plan.conditioning_failed", route_id=route_id, error=str(exc))
            raise PipelineError(
                f"Conditioning bundle assembly failed: {exc}",
                stage="conditioning",
                partial_artifacts=partial,
            ) from exc

        elapsed = time.monotonic() - t0
        log.info("plan.complete", route_id=route_id, bundle=bundle, elapsed_s=round(elapsed, 3))

        return PlannedJob(
            route_id=route_id,
            route=route,
            keyframe_paths=keyframes,
            conditioning_bundle_path=bundle,
        )

    def run(self, job: GeoVeoJob, out_dir: str) -> RunResult:
        """Execute the full pipeline: plan -> render -> evaluate.

        On failure during rendering, returns a ``RunResult`` with
        ``status="partial"`` and preserves all artifacts produced so far.
        """
        t0 = time.monotonic()
        job_id = f"job_{uuid4().hex[:8]}"
        log.info("run.start", job_id=job_id, location=job.location, backend=job.video_backend)

        # Planning phase (may raise ProviderError or PipelineError)
        planned = self.plan(job, out_dir)
        job_id = planned.route_id.replace("route_", "job_")

        # Rendering phase
        try:
            backend = get_backend(job.video_backend)
            log.info("run.render_start", job_id=job_id, backend=backend.__class__.__name__)
            output_video = backend.render(job.prompt, planned.conditioning_bundle_path, out_dir)
            log.info("run.render_done", job_id=job_id, output_video=output_video)
        except Exception as exc:
            log.error("run.render_failed", job_id=job_id, error=str(exc))
            # Preserve partial result
            partial_result = RunResult(
                job_id=job_id,
                status="partial",
                output_video="",
                metadata={
                    "planned_route_id": planned.route_id,
                    "error": str(exc),
                    "stage": "rendering",
                },
            )
            self._persist_result(partial_result, out_dir)
            raise BackendError(
                f"Video rendering failed: {exc}",
                backend=job.video_backend,
                context={"job_id": job_id, "stage": "rendering"},
            ) from exc

        # Evaluation phase (best-effort — never fails the pipeline)
        try:
            metrics = self.evaluation.evaluate(output_video, planned)
        except Exception as exc:
            log.warning("run.evaluation_failed", job_id=job_id, error=str(exc))
            metrics = {"evaluation_error": str(exc)}

        elapsed = time.monotonic() - t0
        log.info("run.complete", job_id=job_id, elapsed_s=round(elapsed, 3))

        result = RunResult(
            job_id=job_id,
            status="done",
            output_video=output_video,
            metadata={"planned_route_id": planned.route_id, "evaluation": metrics},
        )
        self._persist_result(result, out_dir)
        return result

    @staticmethod
    def _persist_result(result: RunResult, out_dir: str) -> None:
        """Write the run result to disk for post-mortem analysis."""
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        result_path = out / "run_result.json"
        result_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
