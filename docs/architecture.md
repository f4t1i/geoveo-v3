# Architecture

GeoVeo v3 adds:
- FastAPI
- environment-driven configuration
- provider stubs
- job validation
- deterministic run artifacts

Flow:
1. validate job
2. plan route
3. fetch imagery
4. build conditioning bundle
5. render with backend
6. evaluate output
7. persist artifacts
