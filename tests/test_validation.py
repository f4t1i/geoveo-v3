from pathlib import Path
from geoveo.validation import validate_job_file

def test_validate_job_file(tmp_path: Path) -> None:
    f = tmp_path / "job.json"
    f.write_text('{"prompt":"test","location":"Hamburg"}', encoding="utf-8")
    job = validate_job_file(f)
    assert job.location == "Hamburg"
