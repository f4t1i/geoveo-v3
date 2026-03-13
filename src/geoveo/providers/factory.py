"""Provider factories that resolve configuration strings to concrete instances.

Each factory reads the provider name from the application settings and returns
the matching implementation.  Unknown names raise ``ValueError`` with a
helpful message listing the supported options.
"""

from geoveo.providers.base import BaseRoutingProvider, BaseImageryProvider, BaseDepthProvider
from geoveo.providers.stubs import StubRoutingProvider, StubImageryProvider, StubDepthProvider

# ---------------------------------------------------------------------------
# Registry maps — extend these when adding real provider implementations
# ---------------------------------------------------------------------------

_ROUTING_PROVIDERS: dict[str, type[BaseRoutingProvider]] = {
    "osrm_stub": StubRoutingProvider,
    "stub": StubRoutingProvider,
}

_IMAGERY_PROVIDERS: dict[str, type[BaseImageryProvider]] = {
    "mapillary_stub": StubImageryProvider,
    "streetview_stub": StubImageryProvider,
    "stub": StubImageryProvider,
}

_DEPTH_PROVIDERS: dict[str, type[BaseDepthProvider]] = {
    "zoedepth_stub": StubDepthProvider,
    "stub": StubDepthProvider,
}


def get_routing_provider(name: str | None = None) -> BaseRoutingProvider:
    """Resolve a routing provider by name, falling back to settings."""
    if name is None:
        from geoveo.config import settings
        name = settings.routing_provider
    normalized = name.lower()
    if normalized not in _ROUTING_PROVIDERS:
        supported = ", ".join(sorted(_ROUTING_PROVIDERS))
        raise ValueError(f"Unsupported routing provider: {name!r}. Supported: {supported}")
    return _ROUTING_PROVIDERS[normalized]()


def get_imagery_provider(name: str | None = None) -> BaseImageryProvider:
    """Resolve an imagery provider by name, falling back to settings."""
    if name is None:
        from geoveo.config import settings
        name = settings.imagery_provider
    normalized = name.lower()
    if normalized not in _IMAGERY_PROVIDERS:
        supported = ", ".join(sorted(_IMAGERY_PROVIDERS))
        raise ValueError(f"Unsupported imagery provider: {name!r}. Supported: {supported}")
    return _IMAGERY_PROVIDERS[normalized]()


def get_depth_provider(name: str | None = None) -> BaseDepthProvider:
    """Resolve a depth provider by name, falling back to settings."""
    if name is None:
        from geoveo.config import settings
        name = settings.depth_provider
    normalized = name.lower()
    if normalized not in _DEPTH_PROVIDERS:
        supported = ", ".join(sorted(_DEPTH_PROVIDERS))
        raise ValueError(f"Unsupported depth provider: {name!r}. Supported: {supported}")
    return _DEPTH_PROVIDERS[normalized]()
