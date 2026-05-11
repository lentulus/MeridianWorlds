"""Routes for ship position data (sourced from world.db)."""

from fastapi import APIRouter

router = APIRouter(prefix="/ships", tags=["ships"])


# GET /ships            — current positions of all ships
# GET /ships/{id}       — position and detail for one ship
# WS  /ships/live       — WebSocket stream for real-time position updates
