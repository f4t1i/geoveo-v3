"""Tests for provider factories and stub implementations."""

import pytest
from pathlib import Path

from geoveo.models import GeoVeoJob, RoutePoint
from geoveo.providers.factory import (
    get_routing_provider,
    get_imagery_provider,
    get_depth_provider,
)
from geoveo.providers.stubs import (
    StubRoutingProvider,
    StubImageryProvider,
    StubDepthProvider,
)


# -----------------------------------------------------------------------
# Factory resolution tests
# -----------------------------------------------------------------------


class TestRoutingProviderFactory:
    def test_resolve_stub(self):
        provider = get_routing_provider("stub")
        assert isinstance(provider, StubRoutingProvider)

    def test_resolve_osrm_stub(self):
        provider = get_routing_provider("osrm_stub")
        assert isinstance(provider, StubRoutingProvider)

    def test_resolve_case_insensitive(self):
        provider = get_routing_provider("STUB")
        assert isinstance(provider, StubRoutingProvider)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unsupported routing provider"):
            get_routing_provider("nonexistent_provider")

    def test_error_message_lists_supported(self):
        with pytest.raises(ValueError, match="osrm_stub"):
            get_routing_provider("bad")


class TestImageryProviderFactory:
    def test_resolve_stub(self):
        provider = get_imagery_provider("stub")
        assert isinstance(provider, StubImageryProvider)

    def test_resolve_mapillary_stub(self):
        provider = get_imagery_provider("mapillary_stub")
        assert isinstance(provider, StubImageryProvider)

    def test_resolve_streetview_stub(self):
        provider = get_imagery_provider("streetview_stub")
        assert isinstance(provider, StubImageryProvider)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unsupported imagery provider"):
            get_imagery_provider("nonexistent")


class TestDepthProviderFactory:
    def test_resolve_stub(self):
        provider = get_depth_provider("stub")
        assert isinstance(provider, StubDepthProvider)

    def test_resolve_zoedepth_stub(self):
        provider = get_depth_provider("zoedepth_stub")
        assert isinstance(provider, StubDepthProvider)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unsupported depth provider"):
            get_depth_provider("nonexistent")


# -----------------------------------------------------------------------
# Stub provider behavior tests
# -----------------------------------------------------------------------


class TestStubRoutingProvider:
    def test_returns_eight_waypoints(self):
        job = GeoVeoJob(prompt="test", location="Hamburg")
        provider = StubRoutingProvider()
        route = provider.plan_route(job)
        assert len(route) == 8
        assert all(isinstance(p, RoutePoint) for p in route)

    def test_waypoints_have_increasing_coordinates(self):
        job = GeoVeoJob(prompt="test", location="Hamburg")
        route = StubRoutingProvider().plan_route(job)
        lats = [p.lat for p in route]
        assert lats == sorted(lats)

    def test_provider_name(self):
        assert StubRoutingProvider().name == "StubRoutingProvider"


class TestStubImageryProvider:
    def test_creates_keyframe_files(self, tmp_path: Path):
        route = [RoutePoint(lat=53.0 + i, lng=10.0 + i, heading_deg=90.0) for i in range(3)]
        provider = StubImageryProvider()
        paths = provider.fetch_keyframes(route, tmp_path)
        assert len(paths) == 3
        for p in paths:
            assert Path(p).exists()
            content = Path(p).read_text()
            assert "stub imagery" in content

    def test_creates_frames_subdirectory(self, tmp_path: Path):
        route = [RoutePoint(lat=53.0, lng=10.0, heading_deg=0.0)]
        StubImageryProvider().fetch_keyframes(route, tmp_path)
        assert (tmp_path / "frames").is_dir()


class TestStubDepthProvider:
    def test_creates_depth_files(self, tmp_path: Path):
        keyframes = [str(tmp_path / f"kf_{i}.txt") for i in range(4)]
        for kf in keyframes:
            Path(kf).write_text("keyframe")
        provider = StubDepthProvider()
        paths = provider.estimate_depth(keyframes, tmp_path)
        assert len(paths) == 4
        for p in paths:
            assert Path(p).exists()
            content = Path(p).read_text()
            assert "stub depth map" in content

    def test_creates_depth_subdirectory(self, tmp_path: Path):
        StubDepthProvider().estimate_depth(["kf.txt"], tmp_path)
        assert (tmp_path / "depth").is_dir()
