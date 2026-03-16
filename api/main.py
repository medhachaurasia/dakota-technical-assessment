from fastapi import FastAPI, Query
from datetime import datetime

from api.models import HealthResponse, EnrichmentResponse
from api.fake_data import generate_enrichment

app = FastAPI(title="Dakota Analytics Fake Data Service")


@app.get("/health", response_model=HealthResponse)
def health():
    return {
        "status": "healthy",
        "service": "dakota-enrichment-api",
        "version": "1.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/enrichment", response_model=EnrichmentResponse)
def enrichment(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    region: str = Query(..., description="Region code")
):
    return generate_enrichment(date, region)