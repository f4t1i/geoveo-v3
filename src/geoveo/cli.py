"""Typer CLI entry point for GeoVeo.

Initializes structured logging on startup and exposes the three core
commands: validate, plan, and run.
"""

from pathlib import Path

import typer

from geoveo.config import settings
from geoveo.logging import configure_logging, get_logger
from geoveo.orchestrator import Orchestrator
from geoveo.validation import validate_job_file

configure_logging(settings.geoveo_log_level)
log = get_logger(__name__)

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def validate(job_file: str) -> None:
    """Validate a job JSON file against the schema and print the parsed model."""
    log.info("cli.validate", job_file=job_file)
    job = validate_job_file(job_file)
    typer.echo(job.model_dump_json(indent=2))


@app.command()
def plan(job_file: str, out: str = "runs/default") -> None:
    """Run the planning phase and write artifacts to the output directory."""
    log.info("cli.plan", job_file=job_file, out=out)
    job = validate_job_file(job_file)
    planned = Orchestrator().plan(job, out)
    typer.echo(planned.model_dump_json(indent=2))
    Path(out, "planned_job.json").write_text(planned.model_dump_json(indent=2), encoding="utf-8")


@app.command()
def run(job_file: str, out: str = "runs/default") -> None:
    """Execute the full pipeline and write all artifacts including the video."""
    log.info("cli.run", job_file=job_file, out=out)
    job = validate_job_file(job_file)
    result = Orchestrator().run(job, out)
    typer.echo(result.model_dump_json(indent=2))
    Path(out, "run_result.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")


if __name__ == "__main__":
    app()
