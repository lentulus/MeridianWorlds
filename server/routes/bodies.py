"""Routes for planetary body data (sourced from starfield.db via meridian)."""

from fastapi import APIRouter
from meridian.models import Body

router = APIRouter(prefix="/bodies", tags=["bodies"])


# GET /bodies/{id}      — physical characteristics of one body
# GET /systems/{id}/bodies — all bodies in a system (see systems.py)
