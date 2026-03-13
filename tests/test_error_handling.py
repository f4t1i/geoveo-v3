"""Tests for error handling: custom exceptions, provider failures, partial runs."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from geoveo.exceptions import (
    BackendError,
    GeoVeoError,
    JobValidationError,
    PipelineError,
    ProviderError,
)
from geoveo.models import GeoVeoJob
from geoveo.orchestrator import Orchestrator
from geoveo.providers.base import BaseRoutingProvider, BaseImageryProvider, BaseDepthProvider
from geoveo.providers.stubs import StubRoutingProvider, StubImageryProvider, StubDepthProvider


# -----------------------------------------------------------------------
# Exception hierarchy tests
# -----------------------------------------------------------------------


class TestExceptionHierarchy:
    def test_all_inherit_from_geoveo_error(self):
        assert issubclass(JobValidationError, GeoVeoError)
        assert issubclass(ProviderError, GeoVeoError)
        assert issubclass(BackendError, GeoVeoError)
        assert issubclass(PipelineError, GeoVeoError)

    def test_geoveo_error_to_dict(self):
        exc = GeoVeoError("something broke", context={"key": "value"})
        d = exc.to_dict()
        assert d["error"] == "GEOVEO_ERROR"
        assert d["message"] == "something broke"
        assert d["context"]["key"] == "value"

    def test_provider_error_includes_provider(self):
        exc = ProviderError("timeout", provider="mapillary")
        assert exc.provider == "mapillary"
        assert exc.to_dict()["context"]["provider"] == "mapillary"

    def test_backend_error_includes_backend(self):
        exc = BackendError("GPU OOM", backend="cogvideox")
        assert exc.backend == "cogvideox"
        assert exc.to_dict()["context"]["backend"] == "cogvideox"

    def test_pipeline_error_includes_partial_artifacts(self):
        exc = PipelineError("failed", stage="imagery", partial_artifacts={"waypoints": 8})
        assert exc.stage == "imagery"
        assert exc.partial_artifacts["waypoints"] == 8


# -----------------------------------------------------------------------
# Orchestrator error handling tests
# -----------------------------------------------------------------------


class FailingRoutingProvider(BaseRoutingProvider):
    def plan_route(self, job):
        raise RuntimeError("OSRM connection refused")


class FailingImageryProvider(BaseImageryProvider):
    def fetch_keyframes(self, route, out_dir):
        raise RuntimeError("Mapillary rate limit exceeded")


class FailingDepthProvider(BaseDepthProvider):
    def estimate_depth(self, keyframe_paths, out_dir):
        raise RuntimeError("ZoeDepth model not found")


class TestOrchestratorErrorHandling:
    def test_routing_failure_raises_provider_error(self, tmp_path):
        orch = Orchestrator(
            routing_provider=FailingRoutingProvider(),
            imagery_provider=StubImageryProvider(),
            depth_provider=StubDepthProvider(),
        )
        job = GeoVeoJob(prompt="test", location="Hamburg")
        with pytest.raises(ProviderError, match="Routing failed"):
            orch.plan(job, str(tmp_path / "out"))

    def test_imagery_failure_raises_provider_error(self, tmp_path):
        orch = Orchestrator(
            routing_provider=StubRoutingProvider(),
            imagery_provider=FailingImageryProvider(),
            depth_provider=StubDepthProvider(),
        )
        job = GeoVeoJob(prompt="test", location="Hamburg")
        with pytest.raises(ProviderError, match="Imagery fetch failed"):
            orch.plan(job, str(tmp_path / "out"))

    def test_depth_failure_raises_provider_error(self, tmp_path):
        orch = Orchestrator(
            routing_provider=StubRoutingProvider(),
            imagery_provider=StubImageryProvider(),
            depth_provider=FailingDepthProvider(),
        )
        job = GeoVeoJob(prompt="test", location="Hamburg")
        with pytest.raises(ProviderError, match="Depth estimation failed"):
            orch.plan(job, str(tmp_path / "out"))

    def test_provider_error_carries_partial_artifacts(self, tmp_path):
        orch = Orchestrator(
            routing_provider=StubRoutingProvider(),
            imagery_provider=FailingImageryProvider(),
            depth_provider=StubDepthProvider(),
        )
        job = GeoVeoJob(prompt="test", location="Hamburg")
        with pytest.raises(ProviderError) as exc_info:
            orch.plan(job, str(tmp_path / "out"))
        # Routing succeeded, so waypoints should be in context
        assert exc_info.value.context.get("waypoints") == 8

    def test_partial_run_result_on_render_failure(self, tmp_path):
        """When rendering fails, run_result.json should be written with status=partial."""
        from unittest.mock import patch

        orch = Orchestrator(
            routing_provider=StubRoutingProvider(),
            imagery_provider=StubImageryProvider(),
            depth_provider=StubDepthProvider(),
        )
        job = GeoVeoJob(prompt="test", location="Hamburg", video_backend="cogvideox")

        class FailingBackend:
            def render(self, prompt, bundle, out_dir):
                raise RuntimeError("GPU exploded")

        with patch("geoveo.orchestrator.get_backend", return_value=FailingBackend()):
            out = str(tmp_path / "out")
            with pytest.raises(BackendError, match="Video rendering failed"):
                orch.run(job, out)

        # Verify partial result was persisted
        result_file = Path(out) / "run_result.json"
        assert result_file.exists()
        import json
        result = json.loads(result_file.read_text())
        assert result["status"] == "partial"
        assert result["metadata"]["stage"] == "rendering"
