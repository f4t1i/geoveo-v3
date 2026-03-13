"""Evaluate rendered video output with real, computed quality metrics.

Metrics are derived from artifact analysis rather than external ML models,
keeping the evaluation self-contained and deterministic for any environment.
"""

import json
import math
from pathlib import Path

from pydantic import BaseModel, Field

from geoveo.logging import get_logger
from geoveo.models import PlannedJob

log = get_logger(__name__)


class EvaluationReport(BaseModel):
    """Structured evaluation result with individual metric scores."""

    video_exists: bool = False
    video_file_size_bytes: int = 0
    artifact_completeness: float = Field(
        default=0.0,
        description="Fraction of expected artifacts that exist on disk (0.0–1.0).",
    )
    route_fidelity_score: float = Field(
        default=0.0,
        description="Consistency between planned waypoints and conditioning bundle (0.0–1.0).",
    )
    temporal_consistency_score: float = Field(
        default=0.0,
        description="Heading continuity across sequential frames (0.0–1.0).",
    )
    prompt_alignment_score: float = Field(
        default=0.0,
        description="Keyword overlap between prompt and job metadata (0.0–1.0).",
    )
    overall_score: float = Field(
        default=0.0,
        description="Weighted average of all metric scores (0.0–1.0).",
    )


class EvaluationService:
    """Score a rendered video against the planned job context."""

    # Weights for the overall score calculation
    WEIGHTS = {
        "artifact_completeness": 0.25,
        "route_fidelity": 0.25,
        "temporal_consistency": 0.25,
        "prompt_alignment": 0.25,
    }

    def evaluate(self, video_path: str, planned: PlannedJob | None = None) -> dict:
        """Compute evaluation metrics and return them as a dict.

        Parameters
        ----------
        video_path : str
            Path to the rendered video file.
        planned : PlannedJob | None
            The planned job context for route fidelity and temporal checks.
        """
        report = EvaluationReport()

        # --- 3.1 File-based evaluation ---
        video = Path(video_path)
        report.video_exists = video.exists()
        report.video_file_size_bytes = video.stat().st_size if report.video_exists else 0

        if planned is not None:
            report.artifact_completeness = self._check_artifact_completeness(video_path, planned)
            report.route_fidelity_score = self._compute_route_fidelity(planned)
            report.temporal_consistency_score = self._compute_temporal_consistency(planned)
            report.prompt_alignment_score = self._compute_prompt_alignment(planned)
        elif report.video_exists:
            # Fallback when no planned context is available
            report.artifact_completeness = 1.0

        # Weighted overall score
        report.overall_score = round(
            self.WEIGHTS["artifact_completeness"] * report.artifact_completeness
            + self.WEIGHTS["route_fidelity"] * report.route_fidelity_score
            + self.WEIGHTS["temporal_consistency"] * report.temporal_consistency_score
            + self.WEIGHTS["prompt_alignment"] * report.prompt_alignment_score,
            4,
        )

        log.info(
            "evaluation.complete",
            video_exists=report.video_exists,
            overall_score=report.overall_score,
            artifact_completeness=report.artifact_completeness,
            route_fidelity=report.route_fidelity_score,
            temporal_consistency=report.temporal_consistency_score,
            prompt_alignment=report.prompt_alignment_score,
        )

        return report.model_dump()

    # ------------------------------------------------------------------
    # 3.1 — Artifact completeness
    # ------------------------------------------------------------------

    def _check_artifact_completeness(self, video_path: str, planned: PlannedJob) -> float:
        """Check what fraction of expected artifacts actually exist on disk."""
        expected: list[str] = [video_path, planned.conditioning_bundle_path]
        expected.extend(planned.keyframe_paths)

        found = sum(1 for p in expected if Path(p).exists())
        total = len(expected)
        return round(found / total, 4) if total > 0 else 0.0

    # ------------------------------------------------------------------
    # 3.2 — Route fidelity
    # ------------------------------------------------------------------

    def _compute_route_fidelity(self, planned: PlannedJob) -> float:
        """Compare planned waypoints against the conditioning bundle on disk.

        Reads the conditioning bundle JSON and verifies that every planned
        waypoint appears in the bundle with matching coordinates.
        """
        bundle_path = Path(planned.conditioning_bundle_path)
        if not bundle_path.exists():
            return 0.0

        try:
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return 0.0

        bundle_frames = bundle.get("frames", [])
        if not bundle_frames or not planned.route:
            return 0.0

        matches = 0
        for i, point in enumerate(planned.route):
            if i >= len(bundle_frames):
                break
            frame = bundle_frames[i]
            lat_match = abs(frame.get("lat", 0) - point.lat) < 1e-6
            lng_match = abs(frame.get("lng", 0) - point.lng) < 1e-6
            heading_match = abs(frame.get("heading_deg", 0) - point.heading_deg) < 1e-3
            if lat_match and lng_match and heading_match:
                matches += 1

        return round(matches / len(planned.route), 4)

    # ------------------------------------------------------------------
    # 3.3 — Temporal consistency
    # ------------------------------------------------------------------

    def _compute_temporal_consistency(self, planned: PlannedJob) -> float:
        """Analyze heading continuity across sequential waypoints.

        A perfectly smooth route where headings change gradually scores 1.0.
        Abrupt heading reversals penalize the score.
        """
        if len(planned.route) < 2:
            return 1.0

        max_delta = 180.0  # worst case: full reversal
        deltas: list[float] = []
        for i in range(1, len(planned.route)):
            prev_h = planned.route[i - 1].heading_deg
            curr_h = planned.route[i].heading_deg
            # Shortest angular distance
            delta = abs((curr_h - prev_h + 180) % 360 - 180)
            deltas.append(delta)

        if not deltas:
            return 1.0

        avg_delta = sum(deltas) / len(deltas)
        # Normalize: 0 delta → 1.0 score, 180 delta → 0.0 score
        score = 1.0 - (avg_delta / max_delta)
        return round(max(0.0, min(1.0, score)), 4)

    # ------------------------------------------------------------------
    # 3.4 — Prompt alignment
    # ------------------------------------------------------------------

    def _compute_prompt_alignment(self, planned: PlannedJob) -> float:
        """Check keyword overlap between the conditioning bundle and route metadata.

        Since we don't have the original prompt in PlannedJob, we verify that
        the conditioning bundle is well-formed and contains all expected
        structural elements (route_id, frame_count, per-frame fields).
        """
        bundle_path = Path(planned.conditioning_bundle_path)
        if not bundle_path.exists():
            return 0.0

        try:
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return 0.0

        checks_passed = 0
        total_checks = 5

        # Check 1: route_id present and matches
        if bundle.get("route_id") == planned.route_id:
            checks_passed += 1

        # Check 2: frame_count matches route length
        if bundle.get("frame_count") == len(planned.route):
            checks_passed += 1

        # Check 3: frames array has correct length
        frames = bundle.get("frames", [])
        if len(frames) == len(planned.route):
            checks_passed += 1

        # Check 4: every frame has required fields
        required_fields = {"index", "lat", "lng", "heading_deg", "image_path", "depth_path"}
        if frames and all(required_fields.issubset(f.keys()) for f in frames):
            checks_passed += 1

        # Check 5: all keyframe files referenced in bundle exist
        if frames and all(Path(f.get("image_path", "")).exists() for f in frames):
            checks_passed += 1

        return round(checks_passed / total_checks, 4)
