"""Assemble conditioning bundles from route, imagery, and depth data.

The conditioning bundle is the central contract between the planning phase
and the video backend — it contains everything needed to render a
geo-conditioned video segment.
"""

import json
from pathlib import Path

from geoveo.logging import get_logger
from geoveo.models import RoutePoint

log = get_logger(__name__)


class ConditioningService:
    """Build a conditioning bundle JSON from route, keyframes, and depth maps."""

    def build_bundle(
        self,
        route_id: str,
        route: list[RoutePoint],
        keyframe_paths: list[str],
        depth_paths: list[str],
        out_dir: Path,
    ) -> str:
        """Assemble and persist the conditioning bundle.

        Parameters
        ----------
        route_id : str
            Unique identifier for this route.
        route : list[RoutePoint]
            Ordered waypoints with GPS and heading data.
        keyframe_paths : list[str]
            File paths to street-level keyframe images.
        depth_paths : list[str]
            File paths to estimated depth maps.
        out_dir : Path
            Directory where the bundle JSON will be written.

        Returns
        -------
        str
            Path to the written ``conditioning_bundle.json``.
        """
        bundle = {
            "route_id": route_id,
            "frame_count": len(route),
            "frames": [
                {
                    "index": i,
                    "lat": point.lat,
                    "lng": point.lng,
                    "heading_deg": point.heading_deg,
                    "image_path": keyframe_paths[i],
                    "depth_path": depth_paths[i] if i < len(depth_paths) else "",
                }
                for i, point in enumerate(route)
            ],
        }
        out_path = out_dir / "conditioning_bundle.json"
        out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
        log.debug(
            "conditioning.bundle_written",
            route_id=route_id,
            frames=len(route),
            path=str(out_path),
        )
        return str(out_path)
