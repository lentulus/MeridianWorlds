"""
Meridian API boundary layer.

Each function defines the contract the worlds project needs. Implementations
are stubs until the Meridian API is finalised; callers receive typed Pydantic
models regardless of what Meridian returns underneath.

Expected Meridian response shape: JSON dict. Translation happens here, once,
at the boundary — the rest of the codebase works with Body/System objects.
"""

from .models import Body, System


def get_body(body_id: str) -> Body:
    """Return physical characteristics for a single body."""
    raise NotImplementedError("Meridian API not yet connected")


def get_system(system_id: str) -> System:
    """Return star system metadata including the ordered list of body_ids."""
    raise NotImplementedError("Meridian API not yet connected")


def list_bodies(system_id: str) -> list[Body]:
    """Return all bodies in a star system."""
    raise NotImplementedError("Meridian API not yet connected")
