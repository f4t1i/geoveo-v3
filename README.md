# GeoVeo v3

Geo-conditioned video orchestration scaffold with:

- CLI
- FastAPI service
- `.env`-based configuration
- provider integration stubs
- JSON schema validation
- deterministic artifact layout

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
geoveo validate examples/alster_job.json
geoveo plan examples/alster_job.json --out runs/alster
geoveo run examples/alster_job.json --out runs/alster
uvicorn geoveo.api.main:app --reload
```

## API

- `GET /health`
- `POST /jobs/validate`
- `POST /jobs/plan`
- `POST /jobs/run`

## Notes

All external providers are implemented as safe stubs:
- routing provider
- imagery provider
- depth provider
- video backends

This keeps the scaffold production-shaped without embedding secrets or brittle external calls.
