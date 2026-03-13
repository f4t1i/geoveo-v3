import json
from pathlib import Path
from geoveo.models import RoutePoint

class ConditioningService:
    def build_bundle(self, route_id: str, route: list[RoutePoint], keyframe_paths: list[str], out_dir: Path) -> str:
        bundle = {
            "route_id": route_id,
            "frames": [
                {
                    "index": i,
                    "lat": p.lat,
                    "lng": p.lng,
                    "heading_deg": p.heading_deg,
                    "image_path": keyframe_paths[i],
                    "depth_path": f"depth/frame_{i:03d}.png",
                }
                for i, p in enumerate(route)
            ],
        }
        out_path = out_dir / "conditioning_bundle.json"
        out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
        return str(out_path)
