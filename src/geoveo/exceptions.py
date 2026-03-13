"""Custom exception hierarchy for GeoVeo.

All GeoVeo exceptions inherit from ``GeoVeoError`` so callers can catch
the entire family with a single except clause.  Each subclass carries a
machine-readable ``code`` and optional ``context`` dict for structured
error reporting in logs and API responses.
"""

from typing import Any


class GeoVeoError(Exception):
    """Base exception for all GeoVeo errors."""

    code: str = "GEOVEO_ERROR"

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize the exception for JSON API responses."""
        return {
            "error": self.code,
            "message": self.message,
            "context": self.context,
        }


class JobValidationError(GeoVeoError):
    """Raised when a job definition fails schema or model validation."""

    code = "JOB_VALIDATION_ERROR"


class ProviderError(GeoVeoError):
    """Raised when an external provider (routing, imagery, depth) fails."""

    code = "PROVIDER_ERROR"

    def __init__(
        self, message: str, provider: str, context: dict[str, Any] | None = None
    ) -> None:
        ctx = {"provider": provider, **(context or {})}
        super().__init__(message, ctx)
        self.provider = provider


class BackendError(GeoVeoError):
    """Raised when a video generation backend fails."""

    code = "BACKEND_ERROR"

    def __init__(
        self, message: str, backend: str, context: dict[str, Any] | None = None
    ) -> None:
        ctx = {"backend": backend, **(context or {})}
        super().__init__(message, ctx)
        self.backend = backend


class PipelineError(GeoVeoError):
    """Raised when the orchestrator pipeline fails mid-execution.

    Carries a ``partial_artifacts`` dict describing what was produced
    before the failure, enabling partial recovery.
    """

    code = "PIPELINE_ERROR"

    def __init__(
        self,
        message: str,
        stage: str,
        partial_artifacts: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        ctx = {"stage": stage, **(context or {})}
        super().__init__(message, ctx)
        self.stage = stage
        self.partial_artifacts = partial_artifacts or {}
