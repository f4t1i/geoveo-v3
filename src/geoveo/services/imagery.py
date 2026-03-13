"""Legacy imagery service — kept for backward compatibility.

The imagery logic has been moved to the provider abstraction layer at
``geoveo.providers``.  This module re-exports the stub provider under
the old ``ImageryService`` name so existing imports continue to work.
"""

from geoveo.providers.stubs import StubImageryProvider as ImageryService

__all__ = ["ImageryService"]
