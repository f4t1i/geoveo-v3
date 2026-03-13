import json
from pathlib import Path
import typer
from geoveo.orchestrator import Orchestrator
from geoveo.validation import validate_job_file

app = typer.Typer(add_completion=False, no_args_is_help=True)

@app.command()
def validate(job_file: str) -> None:
    job = validate_job_file(job_file)
    typer.echo(job.model_dump_json(indent=2))

@app.command()
def plan(job_file: str, out: str = "runs/default") -> None:
    job = validate_job_file(job_file)
    planned = Orchestrator().plan(job, out)
    typer.echo(planned.model_dump_json(indent=2))
    Path(out, "planned_job.json").write_text(planned.model_dump_json(indent=2), encoding="utf-8")

@app.command()
def run(job_file: str, out: str = "runs/default") -> None:
    job = validate_job_file(job_file)
    result = Orchestrator().run(job, out)
    typer.echo(result.model_dump_json(indent=2))
    Path(out, "run_result.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")

if __name__ == "__main__":
    app()
