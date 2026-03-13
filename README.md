# GeoVeo v3

**Geo-conditioned video orchestration engine** that transforms a natural-language scene description and a real-world location into a fully structured video generation pipeline — from route planning through street-level imagery acquisition, depth conditioning, and multi-backend video rendering.

---

## Overview

GeoVeo takes a simple input like *"Drive along the Alster, sunny day, cinematic"* together with a geographic location and automatically executes a seven-stage pipeline:

1. **Validate** the job definition against a strict JSON Schema and Pydantic model
2. **Plan a route** by generating GPS waypoints along the described path
3. **Fetch street-level imagery** for each waypoint via a pluggable imagery provider
4. **Estimate depth maps** for each keyframe via a pluggable depth provider
5. **Build a conditioning bundle** combining route, imagery, depth maps, and metadata
6. **Render video** through a pluggable backend (CogVideoX, AnimateDiff, Google Veo)
7. **Evaluate** the output with four computed quality metrics and persist all artifacts

The entire system is designed to be **backend-agnostic** and **production-shaped**: every external provider is abstracted behind a clean interface, and the scaffold ships with safe deterministic stubs so the full pipeline runs end-to-end without any API keys or network dependencies.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GeoVeo CLI / Async API                    │
│              (Typer CLI  ·  FastAPI + asyncio)               │
├─────────────────────────────────────────────────────────────┤
│                        Orchestrator                         │
│    plan() → route → imagery → depth → conditioning bundle   │
│    run()  → plan() → render → evaluate → persist result     │
│              (per-stage error handling + recovery)           │
├──────────┬──────────┬──────────┬───────────────────────────-┤
│ Routing  │ Imagery  │  Depth   │  Conditioning · Evaluation │
│ Provider │ Provider │ Provider │      Services              │
├──────────┴──────────┴──────────┴────────────────────────────┤
│                     Video Backends                          │
│        CogVideoX  ·  AnimateDiff  ·  Google Veo            │
├─────────────────────────────────────────────────────────────┤
│  Config (.env) · JSON Schemas · Structured Logging · Errors │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Path | Responsibility |
|---|---|---|
| **Orchestrator** | `src/geoveo/orchestrator.py` | Central pipeline controller — chains all providers and services into `plan()` and `run()` workflows with per-stage error handling |
| **Models** | `src/geoveo/models.py` | Pydantic data models: `GeoVeoJob`, `RoutePoint`, `PlannedJob`, `RunResult` |
| **Validation** | `src/geoveo/validation.py` | Dual validation layer — JSON Schema (draft 2020-12) + Pydantic model parsing |
| **Config** | `src/geoveo/config.py` | Environment-driven settings via `pydantic-settings` with `.env` file support |
| **Exceptions** | `src/geoveo/exceptions.py` | Custom exception hierarchy with machine-readable codes and serializable context |
| **Logging** | `src/geoveo/logging.py` | Centralized structured logging via `structlog` with ISO timestamps |
| **CLI** | `src/geoveo/cli.py` | Typer-based CLI with `validate`, `plan`, and `run` commands and error handling |
| **API** | `src/geoveo/api/` | Async FastAPI application with global exception handlers and request logging |

### Provider Abstraction

All external dependencies (routing, imagery, depth estimation) are abstracted behind provider interfaces. The system uses a **factory pattern** to resolve providers from configuration, making it trivial to swap between stubs and real implementations.

| Provider Type | Base Class | Stub Implementation | Real Providers (planned) |
|---|---|---|---|
| **Routing** | `BaseRoutingProvider` | `StubRoutingProvider` | OSRM, Google Directions, Mapbox |
| **Imagery** | `BaseImageryProvider` | `StubImageryProvider` | Mapillary API, Google Street View |
| **Depth** | `BaseDepthProvider` | `StubDepthProvider` | ZoeDepth, Marigold, MiDaS |

Each provider factory (`src/geoveo/providers/factory.py`) reads the provider name from environment configuration and returns the matching implementation. Unknown names raise a `ValueError` listing all supported options.

### Services

| Service | Path | Function |
|---|---|---|
| **ConditioningService** | `src/geoveo/services/conditioning.py` | Assembles the conditioning bundle (route + imagery + depth paths + metadata) |
| **EvaluationService** | `src/geoveo/services/evaluation.py` | Computes four quality metrics: artifact completeness, route fidelity, temporal consistency, prompt alignment |

### Video Backends

| Backend | Path | Description |
|---|---|---|
| **CogVideoX** | `src/geoveo/backends/cogvideox.py` | Image-to-video generation via CogVideoX |
| **AnimateDiff** | `src/geoveo/backends/animatediff.py` | Depth-conditioned animation via AnimateDiff |
| **Veo** | `src/geoveo/backends/veo.py` | Google Veo video generation API |
| **Factory** | `src/geoveo/backends/factory.py` | Backend resolver — maps string identifiers to concrete implementations |

All backends implement the abstract `VideoBackend` interface (`render(prompt, conditioning_bundle_path, out_dir) -> str`), making them fully interchangeable.

---

## Quickstart

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install GeoVeo with development dependencies
pip install -e .[dev]

# 3. Set up environment configuration
cp .env.example .env

# 4. Validate a job definition
geoveo validate examples/alster_job.json

# 5. Plan a route (generates waypoints, imagery, depth maps, conditioning bundle)
geoveo plan examples/alster_job.json --out runs/alster

# 6. Execute a full pipeline run
geoveo run examples/alster_job.json --out runs/alster

# 7. Start the async REST API server
uvicorn geoveo.api.main:app --reload

# 8. Run the test suite (58 tests)
pytest -v
```

---

## CLI Reference

GeoVeo provides three commands through the `geoveo` entry point. All commands include structured error handling with colored, user-friendly messages.

### `geoveo validate <job_file>`

Validates a job JSON file against the schema and Pydantic model. Prints the parsed job on success, exits with a descriptive error on failure.

```bash
$ geoveo validate examples/alster_job.json
{
  "prompt": "Fahre an der Alster entlang, sonniger Tag, cinematic",
  "location": "Hamburg Alster",
  "mode": "drive",
  "sampling_meters": 15,
  "imagery_source": "stub",
  "video_backend": "cogvideox"
}
```

### `geoveo plan <job_file> --out <directory>`

Runs the planning phase: route generation, imagery fetching, depth estimation, and conditioning bundle assembly. Writes all artifacts to the output directory and saves `planned_job.json`.

### `geoveo run <job_file> --out <directory>`

Executes the full pipeline: planning + video rendering + evaluation. Writes all artifacts including the rendered video, `run_result.json`, and evaluation metrics to the output directory.

```bash
$ geoveo run examples/alster_job.json --out runs/alster
{
  "job_id": "job_c4f40014",
  "status": "done",
  "output_video": "runs/alster/video_cogvideox_stub.mp4",
  "metadata": {
    "planned_route_id": "route_c4f40014",
    "evaluation": {
      "video_exists": true,
      "video_file_size_bytes": 131,
      "artifact_completeness": 1.0,
      "route_fidelity_score": 1.0,
      "temporal_consistency_score": 1.0,
      "prompt_alignment_score": 1.0,
      "overall_score": 1.0
    }
  }
}
```

---

## REST API

Start the server with `uvicorn geoveo.api.main:app --reload` (default: `http://localhost:8000`). All endpoints are **async** with orchestrator calls wrapped in `asyncio.to_thread()` for non-blocking execution.

### Endpoints

| Method | Endpoint | Description | Status Codes |
|---|---|---|---|
| `GET` | `/health` | Health check — returns `{"status": "ok"}` | 200 |
| `POST` | `/jobs/validate` | Validates a job payload and returns the parsed model | 200, 422 |
| `POST` | `/jobs/plan` | Executes the planning phase asynchronously | 200, 500, 502 |
| `POST` | `/jobs/run` | Executes the full pipeline asynchronously | 200, 500, 502 |
| `GET` | `/jobs/status/{run_id}` | Query the status of a previously submitted job | 200, 404 |

### Error Responses

The API returns structured JSON error responses for all failure cases:

| Exception | HTTP Status | Error Code | Description |
|---|---|---|---|
| `JobValidationError` | 422 | `JOB_VALIDATION_ERROR` | Job definition fails schema or model validation |
| `ProviderError` | 502 | `PROVIDER_ERROR` | External provider (routing, imagery, depth) fails |
| `BackendError` | 502 | `BACKEND_ERROR` | Video generation backend fails |
| `PipelineError` | 500 | `PIPELINE_ERROR` | Orchestrator pipeline fails mid-execution |

Each error response includes `error` (machine-readable code), `message` (human-readable description), and `context` (structured metadata for debugging).

### Example Request

```bash
curl -X POST http://localhost:8000/jobs/run \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Fahre an der Alster entlang, sonniger Tag, cinematic",
    "location": "Hamburg Alster",
    "mode": "drive",
    "sampling_meters": 15,
    "video_backend": "cogvideox"
  }'
```

Interactive API documentation is available at `/docs` (Swagger UI) and `/redoc` (ReDoc) when the server is running.

---

## Job Schema

A job is defined as a JSON object with the following fields:

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `prompt` | `string` | Yes | — | Natural-language description of the desired scene or drive |
| `location` | `string` | Yes | — | Geographic location, area, or start/end region for the route |
| `mode` | `string` | No | `drive` | Movement mode: `drive`, `walk`, or `bike` |
| `sampling_meters` | `integer` | No | `15` | Distance in meters between sampled viewpoints along the route (1–200) |
| `imagery_source` | `string` | No | `stub` | Street-level data source: `mapillary`, `streetview`, or `stub` |
| `video_backend` | `string` | No | `stub` | Video generation backend: `cogvideox`, `animatediff`, `veo`, or `stub` |

Full JSON Schema definitions are located in `src/geoveo/schemas/`.

---

## Output Artifacts

A completed run produces a deterministic artifact layout:

```
runs/alster/
├── conditioning_bundle.json    # Route + imagery + depth metadata
├── frames/
│   ├── frame_000.txt           # Keyframe data per waypoint
│   ├── frame_001.txt
│   ├── ...
│   └── frame_007.txt
├── depth/
│   ├── depth_000.txt           # Depth map per waypoint
│   ├── depth_001.txt
│   ├── ...
│   └── depth_007.txt
├── run_result.json             # Final result with evaluation metrics
└── video_cogvideox_stub.mp4    # Rendered video output
```

The **conditioning bundle** contains the full context needed for video rendering: route ID, per-frame GPS coordinates, heading, image paths, and depth map paths. This bundle serves as the contract between the planning phase and the video backend.

---

## Evaluation Metrics

The `EvaluationService` computes four real quality metrics (not static stubs) based on artifact analysis:

| Metric | Weight | Range | Description |
|---|---|---|---|
| **Artifact Completeness** | 25% | 0.0–1.0 | Fraction of expected artifacts (video, bundle, keyframes) that exist on disk |
| **Route Fidelity** | 25% | 0.0–1.0 | Consistency between planned waypoints and conditioning bundle coordinates |
| **Temporal Consistency** | 25% | 0.0–1.0 | Heading continuity across sequential frames — smooth routes score high, abrupt reversals score low |
| **Prompt Alignment** | 25% | 0.0–1.0 | Structural completeness of the conditioning bundle (route_id match, frame count, required fields, file existence) |

The **overall score** is the weighted average of all four metrics. All metrics are deterministic and self-contained — no external ML models or API calls required.

---

## Structured Logging

GeoVeo uses [structlog](https://www.structlog.org/) for structured, machine-parseable logging across the entire pipeline.

### Configuration

Logging is configured via the `GEOVEO_LOG_LEVEL` environment variable (default: `INFO`). Supported levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

### Log Format

All log entries include ISO 8601 timestamps, log level, and structured key-value context:

```
2026-03-13T22:39:04.703Z [info     ] orchestrator.init              depth_provider=StubDepthProvider imagery_provider=StubImageryProvider routing_provider=StubRoutingProvider
2026-03-13T22:39:04.703Z [info     ] run.start                      backend=cogvideox job_id=job_ffa9d0de location='Hamburg Alster'
2026-03-13T22:39:04.703Z [info     ] plan.start                     location='Hamburg Alster' mode=drive route_id=route_c4f40014
2026-03-13T22:39:04.703Z [info     ] plan.route_done                route_id=route_c4f40014 waypoints=8
2026-03-13T22:39:04.704Z [info     ] plan.imagery_done              keyframes=8 route_id=route_c4f40014
2026-03-13T22:39:04.704Z [info     ] plan.depth_done                depth_maps=8 route_id=route_c4f40014
2026-03-13T22:39:04.704Z [info     ] plan.complete                  bundle=runs/alster/conditioning_bundle.json elapsed_s=0.001 route_id=route_c4f40014
2026-03-13T22:39:04.704Z [info     ] run.render_start               backend=CogVideoXBackend job_id=job_c4f40014
2026-03-13T22:39:04.704Z [info     ] run.render_done                job_id=job_c4f40014 output_video=runs/alster/video_cogvideox_stub.mp4
2026-03-13T22:39:04.705Z [info     ] evaluation.complete            overall_score=1.0 artifact_completeness=1.0 route_fidelity=1.0 temporal_consistency=1.0 prompt_alignment=1.0
2026-03-13T22:39:04.705Z [info     ] run.complete                   elapsed_s=0.002 job_id=job_c4f40014
```

The FastAPI application includes **request logging middleware** that logs every HTTP request with method, path, status code, and response time.

### Usage in Code

```python
from geoveo.logging import get_logger

log = get_logger(__name__)
log.info("my_event", key="value", count=42)
```

---

## Error Handling

GeoVeo implements a comprehensive error handling strategy with a custom exception hierarchy, per-stage recovery, and structured error reporting.

### Exception Hierarchy

```
GeoVeoError                     # Base — catch-all for the entire family
├── JobValidationError          # Job definition fails schema or model validation
├── ProviderError               # External provider (routing, imagery, depth) fails
├── BackendError                # Video generation backend fails
└── PipelineError               # Orchestrator pipeline fails mid-execution
```

Every exception carries a machine-readable `code`, a human-readable `message`, and an optional `context` dict. All exceptions serialize to JSON via `.to_dict()` for API responses.

### Pipeline Recovery

The orchestrator wraps each pipeline stage in error handling:

- **Routing failure** raises `ProviderError` with the routing provider name and partial context (route_id, out_dir)
- **Imagery failure** raises `ProviderError` with partial context including the number of waypoints already planned
- **Depth failure** raises `ProviderError` with partial context including waypoints and keyframes already fetched
- **Rendering failure** raises `BackendError` and persists a `run_result.json` with `status: "partial"` for post-mortem analysis
- **Evaluation failure** is best-effort — it never fails the pipeline; errors are logged and the evaluation field contains the error message

### CLI Error Messages

The CLI displays colored, user-friendly error messages with the exception code and context:

```
Error [PROVIDER_ERROR]: Routing failed: OSRM connection refused
  provider: osrm
  route_id: route_abc123
```

---

## Adding a Custom Provider

To add a real provider (e.g., OSRM for routing), implement the corresponding base class and register it in the factory:

### Step 1: Implement the Provider

```python
# src/geoveo/providers/osrm.py
from geoveo.providers.base import BaseRoutingProvider
from geoveo.models import GeoVeoJob, RoutePoint

class OSRMRoutingProvider(BaseRoutingProvider):
    def plan_route(self, job: GeoVeoJob) -> list[RoutePoint]:
        # Call OSRM API and return waypoints
        ...
```

### Step 2: Register in Factory

```python
# src/geoveo/providers/factory.py
from geoveo.providers.osrm import OSRMRoutingProvider

_ROUTING_PROVIDERS["osrm"] = OSRMRoutingProvider
```

### Step 3: Configure

```bash
# .env
ROUTING_PROVIDER=osrm
```

The same pattern applies to imagery providers (`BaseImageryProvider`), depth providers (`BaseDepthProvider`), and video backends (`VideoBackend`).

---

## Configuration

All configuration is managed through environment variables, loaded from a `.env` file via `pydantic-settings`.

| Variable | Default | Description |
|---|---|---|
| `GEOVEO_ENV` | `dev` | Environment identifier (`dev`, `staging`, `production`) |
| `GEOVEO_LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `GEOVEO_OUTPUT_ROOT` | `./runs` | Default output directory for artifacts |
| `ROUTING_PROVIDER` | `osrm_stub` | Routing engine provider (`osrm_stub`, `stub`) |
| `IMAGERY_PROVIDER` | `mapillary_stub` | Street-level imagery provider (`mapillary_stub`, `streetview_stub`, `stub`) |
| `DEPTH_PROVIDER` | `zoedepth_stub` | Depth estimation provider (`zoedepth_stub`, `stub`) |
| `DEFAULT_VIDEO_BACKEND` | `cogvideox_stub` | Default video generation backend (`cogvideox`, `animatediff`, `veo`, `stub`) |
| `MAPILLARY_ACCESS_TOKEN` | — | Mapillary API access token |
| `GOOGLE_MAPS_API_KEY` | — | Google Maps / Street View API key |
| `VEO_API_KEY` | — | Google Veo API key |
| `VEO_BASE_URL` | — | Google Veo API base URL |
| `COGVIDEOX_BASE_URL` | — | CogVideoX API base URL |
| `COGVIDEOX_API_KEY` | — | CogVideoX API key |

---

## OpenClaw Skill Integration

The `skill/` directory contains a complete **OpenClaw-compatible skill package** (`geoveo-orchestrator` v2.0.0) that exposes the GeoVeo pipeline as an agent-callable skill with formal tool contracts.

### Skill Contents

| File | Purpose |
|---|---|
| `skill/SKILL.md` | Main skill definition with workflow steps, tool contracts (I/O schemas), and operational rules |
| `skill/schemas/` | JSON Schemas for `get_route`, `get_street_level_image`, `generate_video`, job, and conditioning bundle |
| `skill/templates/` | Output templates for render plans and structured job logs |
| `skill/examples/` | Sample request/response payloads |
| `skill/docs/` | Operational runbook and implementation notes |
| `skill/scripts/` | Project scaffold generator script |

### Skill Installation

```bash
mkdir -p ~/.openclaw/skills/geoveo-orchestrator
cp -R skill/* ~/.openclaw/skills/geoveo-orchestrator/
```

---

## Testing

The project includes a comprehensive test suite with **58 tests** covering all components:

```bash
# Run all tests
pytest -v

# Run with coverage report
pytest --cov=geoveo --cov-report=term-missing

# Run a specific test module
pytest tests/test_providers.py -v

# Lint and type check
ruff check src/ tests/
mypy src/
```

### Test Modules

| Module | Tests | Coverage |
|---|---|---|
| `test_providers.py` | 15 | Provider factories (resolution, case-insensitive, unknown errors) and stub behavior |
| `test_evaluation.py` | 11 | All four evaluation metrics with edge cases (missing files, mismatched data, single waypoints) |
| `test_error_handling.py` | 12 | Exception hierarchy, provider failures, partial artifact preservation, render failure recovery |
| `test_api.py` | 11 | All async endpoints (health, validate, plan, run, status) including validation errors |
| `test_integration.py` | 5 | End-to-end pipeline runs, artifact layout verification, multi-backend tests |
| `test_orchestrator.py` | 2 | Core orchestrator run and plan workflows |
| `test_validation.py` | 2 | Job file validation against schema and model |

---

## Project Structure

```
geoveo-v3/
├── .env.example                              # Environment variable template
├── .gitignore                                # Git ignore rules
├── README.md                                 # This file
├── TODO.md                                   # Improvement roadmap
├── pyproject.toml                            # Project metadata and dependencies
├── docs/
│   ├── api.md                                # API endpoint reference
│   └── architecture.md                       # Architecture overview
├── examples/
│   └── alster_job.json                       # Example job: Hamburg Alster drive
├── skill/                                    # OpenClaw skill package
│   ├── SKILL.md                              # Skill definition and tool contracts
│   ├── README.md                             # Skill package documentation
│   ├── docs/                                 # Runbook and implementation notes
│   ├── examples/                             # Request/response examples
│   ├── schemas/                              # Tool-specific JSON Schemas
│   ├── scripts/                              # Scaffold generator
│   └── templates/                            # Output templates
├── src/geoveo/
│   ├── __init__.py                           # Package version (0.3.0)
│   ├── cli.py                                # Typer CLI entry point
│   ├── config.py                             # Environment-driven settings
│   ├── exceptions.py                         # Custom exception hierarchy
│   ├── logging.py                            # Structured logging (structlog)
│   ├── models.py                             # Pydantic data models
│   ├── orchestrator.py                       # Central pipeline controller
│   ├── validation.py                         # JSON Schema + Pydantic validation
│   ├── api/
│   │   ├── main.py                           # Async FastAPI app with exception handlers
│   │   └── routers/
│   │       ├── health.py                     # GET /health
│   │       └── jobs.py                       # Async /jobs/{validate,plan,run,status}
│   ├── backends/
│   │   ├── base.py                           # Abstract VideoBackend interface
│   │   ├── cogvideox.py                      # CogVideoX backend
│   │   ├── animatediff.py                    # AnimateDiff backend
│   │   ├── veo.py                            # Google Veo backend
│   │   └── factory.py                        # Backend resolver
│   ├── providers/
│   │   ├── base.py                           # Abstract provider interfaces
│   │   ├── stubs.py                          # Deterministic stub implementations
│   │   └── factory.py                        # Provider resolver with registry
│   ├── schemas/
│   │   ├── job.schema.json                   # Job definition schema (draft 2020-12)
│   │   └── conditioning_bundle.schema.json   # Conditioning bundle schema
│   └── services/
│       ├── conditioning.py                   # Conditioning bundle builder
│       └── evaluation.py                     # Quality evaluation (4 real metrics)
└── tests/
    ├── test_api.py                           # Async API endpoint tests (11)
    ├── test_error_handling.py                # Exception and recovery tests (12)
    ├── test_evaluation.py                    # Evaluation metric tests (11)
    ├── test_integration.py                   # End-to-end pipeline tests (5)
    ├── test_orchestrator.py                  # Core orchestrator tests (2)
    ├── test_providers.py                     # Provider factory and stub tests (15)
    └── test_validation.py                    # Job validation tests (2)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| API Framework | FastAPI 0.115+ with Uvicorn (async) |
| Data Validation | Pydantic 2.8+ and jsonschema 4.23+ |
| CLI | Typer 0.12+ |
| Configuration | pydantic-settings 2.4+ with python-dotenv |
| Structured Logging | structlog 24.4+ |
| HTTP Client | httpx 0.27+ |
| Testing | pytest 8.2+ with pytest-cov (58 tests) |
| Linting | Ruff 0.6+ |
| Type Checking | mypy 1.11+ |

---

## Design Principles

**Production-shaped scaffold.** The codebase mirrors the structure and contracts of a production system while shipping with safe, deterministic stubs. This means the full pipeline — from job validation through video rendering and evaluation — runs reliably without any external dependencies, API keys, or network access.

**Backend-agnostic with factory pattern.** Video backends, imagery sources, depth estimators, and routing engines are all abstracted behind clean interfaces with registry-based factories. Swapping CogVideoX for Veo or Mapillary for Google Street View requires implementing a single interface method and adding one line to the registry — no pipeline changes needed.

**Deterministic and reproducible.** Every run produces a structured artifact directory with a conditioning bundle, keyframes, depth maps, evaluation metrics, and the rendered output. The same input always produces the same directory layout, making runs auditable and diffable.

**Dual validation.** Job definitions pass through both JSON Schema validation (structural correctness) and Pydantic model validation (type safety and business rules), ensuring malformed inputs are caught early with clear error messages.

**Observable by default.** Structured logging via structlog is wired into every component — orchestrator, providers, services, backends, and API middleware. Every pipeline stage emits structured events with timing, making debugging and monitoring straightforward from day one.

**Fail gracefully.** A custom exception hierarchy (`GeoVeoError` family) with per-stage error handling ensures that failures are caught, logged, and reported with full context. Partial artifacts are preserved on failure, and evaluation never crashes the pipeline.

---

## License

Private repository. All rights reserved.
