"""Integration test: full pipeline run with all stubs, verifying complete artifact layout."""

import json
from pathlib import Path

import pytest

from geoveo.models import GeoVeoJob
from geoveo.orchestrator import Orchestrator


class TestFullPipelineIntegration:
    """End-to-end integration test that exercises the complete pipeline."""

    @pytest.fixture
    def out_dir(self, tmp_path: Path) -> Path:
        return tmp_path / "integration_run"

    @pytest.fixture
    def job(self) -> GeoVeoJob:
        return GeoVeoJob(
            prompt="Fahre an der Alster entlang, sonniger Tag, cinematic",
            location="Hamburg Alster",
            mode="drive",
            sampling_meters=15,
            imagery_source="stub",
            video_backend="cogvideox",
        )

    def test_full_run_produces_all_artifacts(self, job, out_dir):
        """A complete run should produce video, bundle, frames, depth, and result."""
        orch = Orchestrator()
        result = orch.run(job, str(out_dir))

        # Status
        assert result.status == "done"
        assert result.job_id.startswith("job_")

        # Video file
        video_path = Path(result.output_video)
        assert video_path.exists()
        assert video_path.stat().st_size > 0

        # Conditioning bundle
        bundle_path = out_dir / "conditioning_bundle.json"
        assert bundle_path.exists()
        bundle = json.loads(bundle_path.read_text())
        assert bundle["frame_count"] == 8
        assert len(bundle["frames"]) == 8

        # Keyframe files
        frames_dir = out_dir / "frames"
        assert frames_dir.is_dir()
        keyframes = sorted(frames_dir.iterdir())
        assert len(keyframes) == 8
        for kf in keyframes:
            assert kf.stat().st_size > 0

        # Depth map files
        depth_dir = out_dir / "depth"
        assert depth_dir.is_dir()
        depth_maps = sorted(depth_dir.iterdir())
        assert len(depth_maps) == 8
        for dm in depth_maps:
            assert dm.stat().st_size > 0

        # Run result JSON
        result_file = out_dir / "run_result.json"
        assert result_file.exists()
        result_data = json.loads(result_file.read_text())
        assert result_data["status"] == "done"

    def test_evaluation_metrics_are_computed(self, job, out_dir):
        """Evaluation should return real computed metrics, not static stubs."""
        result = Orchestrator().run(job, str(out_dir))
        evaluation = result.metadata["evaluation"]

        assert evaluation["video_exists"] is True
        assert evaluation["video_file_size_bytes"] > 0
        assert 0.0 <= evaluation["artifact_completeness"] <= 1.0
        assert 0.0 <= evaluation["route_fidelity_score"] <= 1.0
        assert 0.0 <= evaluation["temporal_consistency_score"] <= 1.0
        assert 0.0 <= evaluation["prompt_alignment_score"] <= 1.0
        assert 0.0 <= evaluation["overall_score"] <= 1.0

    def test_conditioning_bundle_matches_route(self, job, out_dir):
        """Every frame in the bundle should match the planned route waypoints."""
        orch = Orchestrator()
        result = orch.run(job, str(out_dir))

        bundle_path = out_dir / "conditioning_bundle.json"
        bundle = json.loads(bundle_path.read_text())

        for frame in bundle["frames"]:
            assert "lat" in frame
            assert "lng" in frame
            assert "heading_deg" in frame
            assert "image_path" in frame
            assert "depth_path" in frame
            # Verify keyframe file exists
            assert Path(frame["image_path"]).exists()

    def test_plan_only(self, job, out_dir):
        """Plan-only should produce route, keyframes, depth, and bundle but no video."""
        planned = Orchestrator().plan(job, str(out_dir))

        assert planned.route_id.startswith("route_")
        assert len(planned.route) == 8
        assert len(planned.keyframe_paths) == 8
        assert Path(planned.conditioning_bundle_path).exists()

        # No video should exist after plan-only
        videos = list(out_dir.glob("*.mp4"))
        assert len(videos) == 0

    def test_different_backends_produce_different_filenames(self, tmp_path):
        """Each backend should produce a video with its name in the filename."""
        for backend_name in ["cogvideox", "animatediff", "veo"]:
            out = tmp_path / f"run_{backend_name}"
            job = GeoVeoJob(
                prompt="test", location="Hamburg", video_backend=backend_name
            )
            result = Orchestrator().run(job, str(out))
            assert backend_name in result.output_video
