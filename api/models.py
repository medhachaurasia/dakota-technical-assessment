from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


class EnrichmentResponse(BaseModel):
    date: str
    region: str
    temperature_c: float
    demand_index: float
    grid_stress_level: str
    renewable_share_pct: float