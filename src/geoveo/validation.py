import json
from pathlib import Path
from jsonschema import validate
from geoveo.models import GeoVeoJob

SCHEMA_DIR = Path(__file__).parent / "schemas"

def load_json(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_job_file(path: str | Path) -> GeoVeoJob:
    raw = load_json(path)
    with open(SCHEMA_DIR / "job.schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)
    validate(instance=raw, schema=schema)
    return GeoVeoJob.model_validate(raw)
