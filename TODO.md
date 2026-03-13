# GeoVeo v3 — Improvement Roadmap

## 1. Provider Abstraction: Factory Pattern for Routing, Imagery, and Depth Services
- [x] 1.1 Create abstract base classes: `BaseRoutingProvider`, `BaseImageryProvider`, `BaseDepthProvider`
- [x] 1.2 Refactor `RoutingService` to use a provider factory that resolves from `settings.routing_provider`
- [x] 1.3 Refactor `ImageryService` to use a provider factory that resolves from `settings.imagery_provider`
- [x] 1.4 Create `DepthService` with provider factory resolving from `settings.depth_provider`
- [x] 1.5 Wire provider factories into the `Orchestrator` via config-driven injection
- [x] 1.6 Update `ConditioningService` to accept depth data from the new `DepthService`

## 2. Structured Logging Across the Entire Pipeline
- [x] 2.1 Add `structlog` dependency to `pyproject.toml`
- [x] 2.2 Create `src/geoveo/logging.py` with a centralized logger configuration bound to `settings.geoveo_log_level`
- [x] 2.3 Add structured log calls to `Orchestrator.plan()` and `Orchestrator.run()` (start, step completion, timing)
- [x] 2.4 Add structured log calls to all services (routing, imagery, conditioning, depth, evaluation)
- [x] 2.5 Add structured log calls to all video backends (render start, render complete, errors)
- [x] 2.6 Add request logging middleware to the FastAPI application

## 3. Real Evaluation Metrics Instead of Static Values
- [x] 3.1 Implement file-based evaluation: video file size, frame count estimation, artifact completeness check
- [x] 3.2 Implement route fidelity metric: compare planned waypoints against conditioning bundle waypoints
- [x] 3.3 Implement temporal consistency metric: analyze conditioning bundle frame sequence for heading continuity
- [x] 3.4 Implement prompt alignment metric: keyword extraction from prompt matched against job metadata
- [x] 3.5 Return a structured `EvaluationReport` model instead of a plain dict

## 4. Async Support for FastAPI Endpoints
- [x] 4.1 Convert all FastAPI route handlers to `async def`
- [x] 4.2 Wrap synchronous orchestrator calls with `asyncio.to_thread()` for non-blocking execution
- [x] 4.3 Add a `/jobs/status/{job_id}` endpoint stub for future async job tracking
- [x] 4.4 Add proper async exception handling and HTTP error responses

## 5. Error Handling and Failure Recovery
- [ ] 5.1 Create custom exception hierarchy: `GeoVeoError`, `ValidationError`, `ProviderError`, `BackendError`
- [ ] 5.2 Add try/except blocks to `Orchestrator.run()` with partial artifact preservation on failure
- [ ] 5.3 Implement `status: "partial"` in `RunResult` for runs that fail mid-pipeline
- [ ] 5.4 Add FastAPI exception handlers that return structured JSON error responses
- [ ] 5.5 Add CLI error handling with user-friendly error messages via Typer

## 6. Expand Test Suite for All New Components
- [ ] 6.1 Add tests for provider factories (routing, imagery, depth) with stub and unknown provider cases
- [ ] 6.2 Add tests for structured logging output (verify log entries are emitted)
- [ ] 6.3 Add tests for evaluation metrics (route fidelity, temporal consistency, prompt alignment)
- [ ] 6.4 Add tests for error handling (provider failures, invalid backends, partial runs)
- [ ] 6.5 Add async API tests using `httpx.AsyncClient` with FastAPI `TestClient`
- [ ] 6.6 Add integration test: full pipeline run with all stubs, verifying complete artifact layout

## 7. Update README with All Changes
- [ ] 7.1 Document provider abstraction and how to add custom providers
- [ ] 7.2 Document logging configuration and log output format
- [ ] 7.3 Document evaluation metrics and their meaning
- [ ] 7.4 Document async API behavior and job status endpoint
- [ ] 7.5 Document error handling, custom exceptions, and failure modes
- [ ] 7.6 Update tech stack table with new dependencies
