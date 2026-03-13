"""Typer CLI entry point for GeoVeo.

Initializes structured logging on startup and exposes the three core
commands: validate, plan, and run.  All commands include error handling
with user-friendly messages.
"""

import sys
from pathlib import Path

import typer

from geoveo.config import settings
from geoveo.exceptions import BackendError, GeoVeoError, ProviderError
from geoveo.logging import configure_logging, get_logger
from geoveo.orchestrator import Orchestrator
from geoveo.validation import validate_job_file

configure_logging(settings.geoveo_log_level)
log = get_logger(__name__)

app = typer.Typer(add_completion=False, no_args_is_help=True)


def _handle_error(exc: Exception) -> None:
    """Print a user-friendly error message and exit."""
    if isinstance(exc, GeoVeoError):
        typer.secho(f"Error [{exc.code}]: {exc.message}", fg=typer.colors.RED, err=True)
        if exc.context:
            for key, value in exc.context.items():
                typer.secho(f"  {key}: {value}", fg=typer.colors.YELLOW, err=True)
    else:
        typer.secho(f"Unexpected error: {exc}", fg=typer.colors.RED, err=True)
    raise typer.Exit(code=1)


@app.command()
def validate(job_file: str) -> None:
    """Validate a job JSON file against the schema and print the parsed model."""
    log.info("cli.validate", job_file=job_file)
    try:
        job = validate_job_file(job_file)
        typer.echo(job.model_dump_json(indent=2))
    except FileNotFoundError:
        typer.secho(f"Error: Job file not found: {job_file}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        _handle_error(exc)


@app.command()
def plan(job_file: str, out: str = "runs/default") -> None:
    """Run the planning phase and write artifacts to the output directory."""
    log.info("cli.plan", job_file=job_file, out=out)
    try:
        job = validate_job_file(job_file)
        planned = Orchestrator().plan(job, out)
        typer.echo(planned.model_dump_json(indent=2))
        Path(out, "planned_job.json").write_text(
            planned.model_dump_json(indent=2), encoding="utf-8"
        )
    except FileNotFoundError:
        typer.secho(f"Error: Job file not found: {job_file}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        _handle_error(exc)


@app.command()
def run(job_file: str, out: str = "runs/default") -> None:
    """Execute the full pipeline and write all artifacts including the video."""
    log.info("cli.run", job_file=job_file, out=out)
    try:
        job = validate_job_file(job_file)
        result = Orchestrator().run(job, out)
        typer.echo(result.model_dump_json(indent=2))
    except FileNotFoundError:
        typer.secho(f"Error: Job file not found: {job_file}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        _handle_error(exc)


if __name__ == "__main__":
    app()
