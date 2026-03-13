"""Centralized structured logging configuration for GeoVeo.

Call ``configure_logging()`` once at application startup (CLI entry or API
startup) to set up structlog with the configured log level.  All modules
should obtain their logger via ``get_logger(__name__)``.
"""

import logging
import sys

import structlog


def configure_logging(level: str = "INFO") -> None:
    """Set up structlog with console rendering bound to the given level.

    Parameters
    ----------
    level : str
        Python log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Standard library root logger — catches structlog output
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=numeric_level,
        force=True,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger for the given module name."""
    return structlog.get_logger(name)
