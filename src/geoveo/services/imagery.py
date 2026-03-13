from pathlib import Path
from geoveo.models import RoutePoint

class ImageryService:
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
        return paths
