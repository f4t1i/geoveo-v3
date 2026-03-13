from geoveo.models import GeoVeoJob
from geoveo.orchestrator import Orchestrator

def test_run(tmp_path) -> None:
    job = GeoVeoJob(prompt="demo", location="Hamburg")
    result = Orchestrator().run(job, str(tmp_path))
    assert result.status == "done"
