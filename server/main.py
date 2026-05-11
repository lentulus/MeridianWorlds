"""
Worlds visualization server.

Exposes star system and ship data over HTTP so the Three.js client
can request it. Run with: uvicorn server.main:app --reload
"""

from fastapi import FastAPI
from server.routes import systems, bodies, ships

app = FastAPI(title="Worlds Visualization Server")

app.include_router(systems.router)
app.include_router(bodies.router)
app.include_router(ships.router)
