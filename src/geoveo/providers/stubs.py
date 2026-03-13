"""Deterministic stub providers for development and testing.

Every stub produces predictable, reproducible output without network access
or API keys.  They mirror the interface contracts of real providers so the
full pipeline can be exercised end-to-end in any environment.
"""

from pathlib import Path

from geoveo.logging import get_logger
from geoveo.models import GeoVeoJob, RoutePoint
from geoveo.providers.base import BaseRoutingProvider, BaseImageryProvider, BaseDepthProvider

log = get_logger(__name__)


class StubRoutingProvider(BaseRoutingProvider):
    """Return a fixed 8-point route near Hamburg Alster for any job."""

    def plan_route(self, job: GeoVeoJob) -> list[RoutePoint]:
        base_lat, base_lng = 53.566, 9.992
        points = [
            RoutePoint(
                lat=base_lat + i * 0.0005,
                lng=base_lng + i * 0.0007,
                heading_deg=70.0,
            )
            for i in range(8)
        ]
        log.debug("stub.routing.plan_route", waypoints=len(points), location=job.location)
        return points


class StubImageryProvider(BaseImageryProvider):
    """Write a text placeholder for each waypoint instead of a real image."""

    def fetch_keyframes(self, route: list[RoutePoint], out_dir: Path) -> list[str]:
        frames_dir = out_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        paths: list[str] = []
        for i, point in enumerate(route):
            path = frames_dir / f"frame_{i:03d}.txt"
            path.write_text(
                f"stub imagery for lat={point.lat} lng={point.lng} heading={point.heading_deg}\n",
                encoding="utf-8",
            )
            paths.append(str(path))
        log.debug("stub.imagery.fetch_keyframes", frames=len(paths), out_dir=str(out_dir))
        return paths


class StubDepthProvider(BaseDepthProvider):
    """Write a text placeholder for each keyframe instead of a real depth map."""

    def estimate_depth(self, keyframe_paths: list[str], out_dir: Path) -> list[str]:
        depth_dir = out_dir / "depth"
        depth_dir.mkdir(parents=True, exist_ok=True)
        paths: list[str] = []
        for i, kf_path in enumerate(keyframe_paths):
            path = depth_dir / f"frame_{i:03d}.png"
            path.write_text(
                f"stub depth map for keyframe={kf_path}\n",
                encoding="utf-8",
            )
            paths.append(str(path))
        log.debug("stub.depth.estimate_depth", depth_maps=len(paths), out_dir=str(out_dir))
        return paths
