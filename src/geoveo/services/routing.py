"""Legacy routing service — kept for backward compatibility.

The routing logic has been moved to the provider abstraction layer at
``geoveo.providers``.  This module re-exports the stub provider under
the old ``RoutingService`` name so existing imports continue to work.
"""

from geoveo.providers.stubs import StubRoutingProvider as RoutingService

__all__ = ["RoutingService"]
