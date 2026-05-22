from pydantic import BaseModel


class Body(BaseModel):
    body_id: str
    name: str
    system_id: str
    gravity_g: float
    atm_pressure_bar: float | None = None
    mean_temp_k: float | None = None
    hydrosphere_pct: float | None = None
    volatile_type: str | None = None


class System(BaseModel):
    system_id: str
    name: str
    body_ids: list[str]
