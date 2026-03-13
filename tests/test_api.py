"""Tests for the async FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from geoveo.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestValidateEndpoint:
    def test_valid_job(self, client):
        response = client.post("/jobs/validate", json={
            "prompt": "Drive along the Alster",
            "location": "Hamburg",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "valid"
        assert data["job"]["prompt"] == "Drive along the Alster"

    def test_missing_required_field(self, client):
        response = client.post("/jobs/validate", json={"prompt": "test"})
        assert response.status_code == 422  # Pydantic validation error

    def test_invalid_mode(self, client):
        response = client.post("/jobs/validate", json={
            "prompt": "test",
            "location": "Hamburg",
            "mode": "fly",
        })
        assert response.status_code == 422

    def test_sampling_meters_out_of_range(self, client):
        response = client.post("/jobs/validate", json={
            "prompt": "test",
            "location": "Hamburg",
            "sampling_meters": 500,
        })
        assert response.status_code == 422


class TestPlanEndpoint:
    def test_plan_returns_route(self, client):
        response = client.post("/jobs/plan", json={
            "prompt": "test",
            "location": "Hamburg",
        })
        assert response.status_code == 200
        data = response.json()
        assert "route_id" in data
        assert "route" in data
        assert len(data["route"]) == 8
        assert "conditioning_bundle_path" in data


class TestRunEndpoint:
    def test_run_returns_result(self, client):
        response = client.post("/jobs/run", json={
            "prompt": "test",
            "location": "Hamburg",
            "video_backend": "cogvideox",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert "output_video" in data
        assert "evaluation" in data["metadata"]

    def test_run_evaluation_has_real_metrics(self, client):
        response = client.post("/jobs/run", json={
            "prompt": "test",
            "location": "Hamburg",
        })
        data = response.json()
        evaluation = data["metadata"]["evaluation"]
        assert "artifact_completeness" in evaluation
        assert "route_fidelity_score" in evaluation
        assert "temporal_consistency_score" in evaluation
        assert "prompt_alignment_score" in evaluation
        assert "overall_score" in evaluation


class TestStatusEndpoint:
    def test_nonexistent_job_returns_404(self, client):
        response = client.get("/jobs/status/nonexistent")
        assert response.status_code == 404
        assert response.json()["detail"]["error"] == "JobNotFound"
