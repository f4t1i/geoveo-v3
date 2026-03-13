"""Abstract base classes for all external provider integrations.

Each provider type defines a minimal contract that concrete implementations
must fulfill.  This keeps the orchestrator and services decoupled from any
specific vendor SDK or API surface.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from geoveo.models import GeoVeoJob, RoutePoint


class BaseRoutingProvider(ABC):
    """Resolve a job definition into an ordered sequence of route points."""

    @abstractmethod
    def plan_route(self, job: GeoVeoJob) -> list[RoutePoint]:
        """Return an ordered list of waypoints for the given job.

        Implementations may call external routing APIs (OSRM, Google Directions,
        Mapbox) or return deterministic stubs for development and testing.
        """

    @property
    def name(self) -> str:
        return self.__class__.__name__


class BaseImageryProvider(ABC):
    """Fetch street-level imagery for a sequence of route points."""

    @abstractmethod
    def fetch_keyframes(self, route: list[RoutePoint], out_dir: Path) -> list[str]:
        """Download or generate one keyframe image per route point.

        Returns a list of file paths (one per waypoint) written into *out_dir*.
        """

    @property
    def name(self) -> str:
        return self.__class__.__name__


class BaseDepthProvider(ABC):
    """Estimate depth maps for a set of keyframe images."""

    @abstractmethod
    def estimate_depth(self, keyframe_paths: list[str], out_dir: Path) -> list[str]:
        """Produce a depth map for each keyframe image.

        Returns a list of depth-map file paths written into *out_dir*.
        """

    @property
    def name(self) -> str:
        return self.__class__.__name__
