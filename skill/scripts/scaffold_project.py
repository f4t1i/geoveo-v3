#!/usr/bin/env python3
"""Generate a minimal local project scaffold for the GeoVeo pipeline."""

from __future__ import annotations
import argparse
from pathlib import Path
import json

FILES = {
    "app.py": """from pathlib import Path

def main() -> None:
    print('GeoVeo scaffold ready.')

if __name__ == '__main__':
    main()
""",
    "config.py": """from dataclasses import dataclass

@dataclass
class Settings:
    imagery_source: str = 'mapillary'
    video_backend: str = 'cogvideox_i2v'
""",
    "planner.py": """def plan_job(job: dict) -> dict:
    return {'status': 'planned', 'job': job}
""",
    "routing.py": """def sample_route(location: str, sampling_meters: float) -> list[dict]:
    return []
""",
    "imagery.py": """def fetch_keyframes(points: list[dict], source: str) -> list[str]:
    return []
""",
    "conditioning.py": """def build_conditioning_bundle(job: dict, keyframes: list[str]) -> dict:
    return {'job': job, 'keyframes': keyframes}
""",
    "evaluator.py": """def evaluate_render(output_path: str) -> dict:
    return {'geometry_consistency': 'unknown', 'temporal_stability': 'unknown'}
""",
    "backends/__init__.py": """""",
    "backends/cogvideox_i2v.py": """def generate_video(bundle: dict) -> str:
    return 'outputs/video.mp4'
""",
    "backends/veo_adapter.py": """def generate_video(bundle: dict) -> str:
    raise NotImplementedError('Implement provider-specific adapter')
""",
}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True, help='Output directory')
    args = parser.parse_args()

    root = Path(args.out)
    for rel_path, content in FILES.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    (root / 'README.md').write_text(
        '# GeoVeo Scaffold\n\nGenerated local scaffold.\n',
        encoding='utf-8'
    )
    (root / 'job.example.json').write_text(
        json.dumps({
            'prompt': 'Drive along a scenic waterfront route, sunny, cinematic',
            'location': 'Example City',
            'mode': 'drive',
            'sampling_meters': 15,
            'imagery_source': 'mapillary',
            'video_backend': 'cogvideox_i2v'
        }, indent=2),
        encoding='utf-8'
    )
    print(f'Created scaffold at {root}')

if __name__ == '__main__':
    main()
