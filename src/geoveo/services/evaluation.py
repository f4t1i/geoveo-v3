"""Evaluate rendered video output for quality metrics.

Currently returns static stub scores.  Will be replaced with real metrics
in a subsequent improvement step.
"""

from pathlib import Path

from geoveo.models import PlannedJob


class EvaluationService:
    """Score a rendered video against the planned job context."""

    def evaluate(self, video_path: str, planned: PlannedJob | None = None) -> dict:
        """Return evaluation metrics for the rendered video.

        Parameters
        ----------
        video_path : str
            Path to the rendered video file.
        planned : PlannedJob | None
            The planned job context for route fidelity checks.
        """
        exists = Path(video_path).exists()
        return {
            "video_exists": exists,
            "temporal_consistency_score": 0.72 if exists else 0.0,
            "route_fidelity_score": 0.81 if exists else 0.0,
        }
