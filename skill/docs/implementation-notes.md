# Implementation Notes

## Recommended runtime split
- Planner / orchestrator
- Routing adapter
- Imagery adapter
- Conditioning builder
- Backend adapter
- Evaluator

## Minimal Python module layout
```text
geoveo/
  app.py
  config.py
  planner.py
  routing.py
  imagery.py
  conditioning.py
  evaluator.py
  backends/
    __init__.py
    cogvideox_i2v.py
    veo_adapter.py
```

## Strong defaults
- JSON logs for each step
- idempotent output directories keyed by job ID
- environment variables for provider keys
- local cache for fetched imagery
- schema validation before execution

## Nice-to-have later
- dashboard
- side-by-side backend comparison
- map UI
- segment stitching
- prompt packs per weather / style
