"""Routes for star system data (sourced from starfield.db via meridian)."""

from fastapi import APIRouter
from meridian.models import System

router = APIRouter(prefix="/systems", tags=["systems"])


# GET /systems          — list all systems (for placing stars in 3D space)
# GET /systems/{id}     — detail for one system
