# GeoVeo v3

**Geo-conditioned video orchestration engine** that transforms a natural-language scene description and a real-world location into a fully structured video generation pipeline — from route planning through street-level imagery acquisition, depth conditioning, and multi-backend video rendering.

---

## Overview

GeoVeo takes a simple input like *"Drive along the Alster, sunny day, cinematic"* together with a geographic location and automatically executes a seven-stage pipeline:

1. **Validate** the job definition against a strict JSON Schema
2. **Plan a route** by generating GPS waypoints along the described path
3. **Fetch street-level imagery** for each waypoint (Mapillary, Google Street View, or stub)
4. **Build a conditioning bundle** combining imagery, depth maps, camera path, and metadata
5. **Render video** through a pluggable backend (CogVideoX, AnimateDiff, Google Veo)
6. **Evaluate** the output for temporal consistency and route fidelity
7. **Persist** all artifacts in a deterministic, reproducible directory layout

The entire system is designed to be **backend-agnostic** and **production-shaped**: every external provider is abstracted behind a clean interface, and the scaffold ships with safe deterministic stubs so the full pipeline runs end-to-end without any API keys or network dependencies.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        GeoVeo CLI / API                     │
│                  (Typer CLI  ·  FastAPI REST)                │
├─────────────────────────────────────────────────────────────┤
│                        Orchestrator                         │
│         plan() → validate → route → imagery → bundle        │
│         run()  → plan() → render → evaluate → persist       │
├──────────┬──────────┬──────────────┬────────────────────────┤
│ Routing  │ Imagery  │ Conditioning │     Evaluation         │
│ Service  │ Service  │   Service    │      Service           │
├──────────┴──────────┴──────────────┴────────────────────────┤
│                     Video Backends                          │
│        CogVideoX  ·  AnimateDiff  ·  Google Veo            │
├─────────────────────────────────────────────────────────────┤
│              Config (.env)  ·  JSON Schemas                 │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Path | Responsibility |
|---|---|---|
| **Orchestrator** | `src/geoveo/orchestrator.py` | Central pipeline controller — chains all services and backends into `plan()` and `run()` workflows |
| **Models** | `src/geoveo/models.py` | Pydantic data models: `GeoVeoJob`, `RoutePoint`, `PlannedJob`, `RunResult` |
| **Validation** | `src/geoveo/validation.py` | Dual validation layer — JSON Schema (draft 2020-12) + Pydantic model parsing |
| **Config** | `src/geoveo/config.py` | Environment-driven settings via `pydantic-settings` with `.env` file support |
| **CLI** | `src/geoveo/cli.py` | Typer-based command-line interface with `validate`, `plan`, and `run` commands |
| **API** | `src/geoveo/api/` | FastAPI application with health check and job endpoints |

### Services

| Service | Path | Function |
|---|---|---|
| **RoutingService** | `src/geoveo/services/routing.py` | Generates a sequence of GPS waypoints with heading data from a job definition |
| **ImageryService** | `src/geoveo/services/imagery.py` | Fetches or generates street-level keyframe images for each waypoint |
| **ConditioningService** | `src/geoveo/services/conditioning.py` | Assembles the conditioning bundle (route + imagery + depth paths + metadata) |
| **EvaluationService** | `src/geoveo/services/evaluation.py` | Scores rendered output for temporal consistency and route fidelity |

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

# 5. Plan a route (generates waypoints, imagery, conditioning bundle)
geoveo plan examples/alster_job.json --out runs/alster

# 6. Execute a full pipeline run
geoveo run examples/alster_job.json --out runs/alster

# 7. Start the REST API server
uvicorn geoveo.api.main:app --reload
```

---

## CLI Reference

GeoVeo provides three commands through the `geoveo` entry point:

### `geoveo validate <job_file>`

Validates a job JSON file against the schema and Pydantic model. Prints the parsed job on success, exits with an error on validation failure.

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

Runs the planning phase: route generation, imagery fetching, and conditioning bundle assembly. Writes all artifacts to the output directory and saves `planned_job.json`.

### `geoveo run <job_file> --out <directory>`

Executes the full pipeline: planning + video rendering + evaluation. Writes all artifacts including the rendered video and `run_result.json` to the output directory.

```bash
$ geoveo run examples/alster_job.json --out runs/alster
{
  "job_id": "job_36b5acc9",
  "status": "done",
  "output_video": "runs/alster/video_cogvideox_stub.mp4",
  "metadata": {
    "planned_route_id": "route_36b5acc9",
    "evaluation": {
      "video_exists": true,
      "temporal_consistency_score": 0.72,
      "route_fidelity_score": 0.81
    }
  }
}
```

---

## REST API

Start the server with `uvicorn geoveo.api.main:app --reload` (default: `http://localhost:8000`).

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |
| `POST` | `/jobs/validate` | Validates a job payload and returns the parsed model |
| `POST` | `/jobs/plan` | Executes the planning phase and returns route, keyframes, and bundle path |
| `POST` | `/jobs/run` | Executes the full pipeline and returns job result with evaluation metrics |

### Example Request

```bash
curl -X POST http://localhost:8000/jobs/run \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Fahre an der Alster entlang, sonniger Tag, cinematic",
    "location": "Hamburg Alster",
    "mode": "drive",
    "sampling_meters": 15,
    "imagery_source": "stub",
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
├── run_result.json             # Final result with evaluation metrics
└── video_cogvideox_stub.mp4    # Rendered video output
```

The **conditioning bundle** contains the full context needed for video rendering: route ID, per-frame GPS coordinates, heading, image paths, and depth map paths. This bundle serves as the contract between the planning phase and the video backend.

---

## Configuration

All configuration is managed through environment variables, loaded from a `.env` file via `pydantic-settings`.

| Variable | Default | Description |
|---|---|---|
| `GEOVEO_ENV` | `dev` | Environment identifier |
| `GEOVEO_LOG_LEVEL` | `INFO` | Logging verbosity |
| `GEOVEO_OUTPUT_ROOT` | `./runs` | Default output directory for artifacts |
| `ROUTING_PROVIDER` | `osrm_stub` | Routing engine provider |
| `IMAGERY_PROVIDER` | `mapillary_stub` | Street-level imagery provider |
| `DEPTH_PROVIDER` | `zoedepth_stub` | Depth estimation provider |
| `DEFAULT_VIDEO_BACKEND` | `cogvideox_stub` | Default video generation backend |
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

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=geoveo --cov-report=term-missing

# Lint and type check
ruff check src/ tests/
mypy src/
```

---

## Project Structure

```
geoveo-v3/
├── .env.example                          # Environment variable template
├── .gitignore                            # Git ignore rules
├── README.md                             # This file
├── pyproject.toml                        # Project metadata and dependencies
├── docs/
│   ├── api.md                            # API endpoint reference
│   └── architecture.md                   # Architecture overview
├── examples/
│   └── alster_job.json                   # Example job: Hamburg Alster drive
├── skill/                                # OpenClaw skill package
│   ├── SKILL.md                          # Skill definition and tool contracts
│   ├── README.md                         # Skill package documentation
│   ├── docs/                             # Runbook and implementation notes
│   ├── examples/                         # Request/response examples
│   ├── schemas/                          # Tool-specific JSON Schemas
│   ├── scripts/                          # Scaffold generator
│   └── templates/                        # Output templates
├── src/geoveo/
│   ├── __init__.py                       # Package version (0.3.0)
│   ├── cli.py                            # Typer CLI entry point
│   ├── config.py                         # Environment-driven settings
│   ├── models.py                         # Pydantic data models
│   ├── orchestrator.py                   # Central pipeline controller
│   ├── validation.py                     # JSON Schema + Pydantic validation
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                       # FastAPI application factory
│   │   └── routers/
│   │       ├── health.py                 # GET /health
│   │       └── jobs.py                   # POST /jobs/{validate,plan,run}
│   ├── backends/
│   │   ├── base.py                       # Abstract VideoBackend interface
│   │   ├── cogvideox.py                  # CogVideoX backend
│   │   ├── animatediff.py                # AnimateDiff backend
│   │   ├── veo.py                        # Google Veo backend
│   │   └── factory.py                    # Backend resolver
│   ├── schemas/
│   │   ├── job.schema.json               # Job definition schema (draft 2020-12)
│   │   └── conditioning_bundle.schema.json  # Conditioning bundle schema
│   └── services/
│       ├── routing.py                    # Route planning service
│       ├── imagery.py                    # Street-level imagery service
│       ├── conditioning.py               # Conditioning bundle builder
│       └── evaluation.py                 # Output quality evaluation
└── tests/
    ├── test_orchestrator.py              # End-to-end orchestrator test
    └── test_validation.py                # Job validation test
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| API Framework | FastAPI 0.115+ with Uvicorn |
| Data Validation | Pydantic 2.8+ and jsonschema 4.23+ |
| CLI | Typer 0.12+ |
| Configuration | pydantic-settings 2.4+ with python-dotenv |
| HTTP Client | httpx 0.27+ |
| Testing | pytest 8.2+ with pytest-cov |
| Linting | Ruff 0.6+ |
| Type Checking | mypy 1.11+ |

---

## Design Principles

**Production-shaped scaffold.** The codebase mirrors the structure and contracts of a production system while shipping with safe, deterministic stubs. This means the full pipeline — from job validation through video rendering and evaluation — runs reliably without any external dependencies, API keys, or network access.

**Backend-agnostic.** Video backends, imagery sources, depth estimators, and routing engines are all abstracted behind clean interfaces. Swapping CogVideoX for Veo or Mapillary for Google Street View requires implementing a single interface method — no pipeline changes needed.

**Deterministic and reproducible.** Every run produces a structured artifact directory with a conditioning bundle, keyframes, evaluation metrics, and the rendered output. The same input always produces the same directory layout, making runs auditable and diffable.

**Dual validation.** Job definitions pass through both JSON Schema validation (structural correctness) and Pydantic model validation (type safety and business rules), ensuring malformed inputs are caught early with clear error messages.

---

## License

Private repository. All rights reserved.
