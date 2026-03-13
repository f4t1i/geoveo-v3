"""Tests for evaluation metrics: route fidelity, temporal consistency, prompt alignment."""

import json
from pathlib import Path

import pytest

from geoveo.models import PlannedJob, RoutePoint
from geoveo.services.evaluation import EvaluationService


@pytest.fixture
def evaluation_service():
    return EvaluationService()


@pytest.fixture
def sample_route():
    return [
        RoutePoint(lat=53.566 + i * 0.0005, lng=9.992 + i * 0.0007, heading_deg=70.0)
        for i in range(8)
    ]


@pytest.fixture
def planned_job(tmp_path: Path, sample_route: list[RoutePoint]):
    """Create a PlannedJob with matching conditioning bundle and keyframes."""
    # Create keyframe files
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    keyframe_paths = []
    for i in range(8):
        kf = frames_dir / f"frame_{i:03d}.txt"
        kf.write_text(f"keyframe {i}")
        keyframe_paths.append(str(kf))

    # Create conditioning bundle
    bundle = {
        "route_id": "route_test123",
        "frame_count": 8,
        "frames": [
            {
                "index": i,
                "lat": sample_route[i].lat,
                "lng": sample_route[i].lng,
                "heading_deg": sample_route[i].heading_deg,
                "image_path": keyframe_paths[i],
                "depth_path": f"depth_{i}.png",
            }
            for i in range(8)
        ],
    }
    bundle_path = tmp_path / "conditioning_bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2))

    return PlannedJob(
        route_id="route_test123",
        route=sample_route,
        keyframe_paths=keyframe_paths,
        conditioning_bundle_path=str(bundle_path),
    )


class TestArtifactCompleteness:
    def test_all_artifacts_present(self, tmp_path, evaluation_service, planned_job):
        video = tmp_path / "video.mp4"
        video.write_text("video content")
        result = evaluation_service.evaluate(str(video), planned_job)
        assert result["artifact_completeness"] == 1.0

    def test_missing_video(self, evaluation_service, planned_job):
        result = evaluation_service.evaluate("/nonexistent/video.mp4", planned_job)
        assert result["video_exists"] is False
        assert result["artifact_completeness"] < 1.0

    def test_video_file_size(self, tmp_path, evaluation_service, planned_job):
        video = tmp_path / "video.mp4"
        video.write_text("x" * 1024)
        result = evaluation_service.evaluate(str(video), planned_job)
        assert result["video_file_size_bytes"] == 1024


class TestRouteFidelity:
    def test_perfect_fidelity(self, tmp_path, evaluation_service, planned_job):
        video = tmp_path / "video.mp4"
        video.write_text("video")
        result = evaluation_service.evaluate(str(video), planned_job)
        assert result["route_fidelity_score"] == 1.0

    def test_mismatched_bundle(self, tmp_path, evaluation_service, sample_route):
        # Create bundle with wrong coordinates
        bundle = {
            "route_id": "route_test",
            "frame_count": 8,
            "frames": [
                {"index": i, "lat": 0.0, "lng": 0.0, "heading_deg": 0.0,
                 "image_path": "", "depth_path": ""}
                for i in range(8)
            ],
        }
        bundle_path = tmp_path / "conditioning_bundle.json"
        bundle_path.write_text(json.dumps(bundle))

        planned = PlannedJob(
            route_id="route_test",
            route=sample_route,
            keyframe_paths=["" for _ in range(8)],
            conditioning_bundle_path=str(bundle_path),
        )
        video = tmp_path / "video.mp4"
        video.write_text("video")
        result = evaluation_service.evaluate(str(video), planned)
        assert result["route_fidelity_score"] == 0.0

    def test_missing_bundle_file(self, tmp_path, evaluation_service, sample_route):
        planned = PlannedJob(
            route_id="route_test",
            route=sample_route,
            keyframe_paths=[],
            conditioning_bundle_path="/nonexistent/bundle.json",
        )
        video = tmp_path / "video.mp4"
        video.write_text("video")
        result = evaluation_service.evaluate(str(video), planned)
        assert result["route_fidelity_score"] == 0.0


class TestTemporalConsistency:
    def test_constant_heading_scores_one(self, tmp_path, evaluation_service, planned_job):
        video = tmp_path / "video.mp4"
        video.write_text("video")
        result = evaluation_service.evaluate(str(video), planned_job)
        # All headings are 70.0, so delta is 0 → score is 1.0
        assert result["temporal_consistency_score"] == 1.0

    def test_reversing_headings_scores_low(self, tmp_path, evaluation_service):
        # Headings alternate between 0 and 180 → maximum discontinuity
        route = [
            RoutePoint(lat=53.0, lng=10.0, heading_deg=0.0 if i % 2 == 0 else 180.0)
            for i in range(8)
        ]
        bundle = {
            "route_id": "route_flip",
            "frame_count": 8,
            "frames": [
                {"index": i, "lat": 53.0, "lng": 10.0,
                 "heading_deg": route[i].heading_deg,
                 "image_path": "", "depth_path": ""}
                for i in range(8)
            ],
        }
        bundle_path = tmp_path / "conditioning_bundle.json"
        bundle_path.write_text(json.dumps(bundle))

        planned = PlannedJob(
            route_id="route_flip",
            route=route,
            keyframe_paths=["" for _ in range(8)],
            conditioning_bundle_path=str(bundle_path),
        )
        video = tmp_path / "video.mp4"
        video.write_text("video")
        result = evaluation_service.evaluate(str(video), planned)
        assert result["temporal_consistency_score"] == 0.0

    def test_single_waypoint_scores_one(self, tmp_path, evaluation_service):
        route = [RoutePoint(lat=53.0, lng=10.0, heading_deg=90.0)]
        bundle_path = tmp_path / "conditioning_bundle.json"
        bundle_path.write_text(json.dumps({"route_id": "r", "frame_count": 1, "frames": []}))
        planned = PlannedJob(
            route_id="r", route=route, keyframe_paths=[], conditioning_bundle_path=str(bundle_path)
        )
        video = tmp_path / "video.mp4"
        video.write_text("video")
        result = evaluation_service.evaluate(str(video), planned)
        assert result["temporal_consistency_score"] == 1.0


class TestPromptAlignment:
    def test_well_formed_bundle_scores_high(self, tmp_path, evaluation_service, planned_job):
        video = tmp_path / "video.mp4"
        video.write_text("video")
        result = evaluation_service.evaluate(str(video), planned_job)
        assert result["prompt_alignment_score"] == 1.0

    def test_missing_bundle_scores_zero(self, tmp_path, evaluation_service, sample_route):
        planned = PlannedJob(
            route_id="route_test",
            route=sample_route,
            keyframe_paths=[],
            conditioning_bundle_path="/nonexistent/bundle.json",
        )
        video = tmp_path / "video.mp4"
        video.write_text("video")
        result = evaluation_service.evaluate(str(video), planned)
        assert result["prompt_alignment_score"] == 0.0


class TestOverallScore:
    def test_perfect_run_scores_one(self, tmp_path, evaluation_service, planned_job):
        video = tmp_path / "video.mp4"
        video.write_text("video")
        result = evaluation_service.evaluate(str(video), planned_job)
        assert result["overall_score"] == 1.0

    def test_no_planned_context(self, tmp_path, evaluation_service):
        video = tmp_path / "video.mp4"
        video.write_text("video")
        result = evaluation_service.evaluate(str(video), None)
        assert result["video_exists"] is True
        assert result["artifact_completeness"] == 1.0
        # Other metrics default to 0 without planned context
        assert result["overall_score"] == 0.25  # only completeness contributes
