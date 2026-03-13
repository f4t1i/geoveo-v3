from fastapi import FastAPI
from geoveo.api.routers.health import router as health_router
from geoveo.api.routers.jobs import router as jobs_router

app = FastAPI(title="GeoVeo API", version="0.3.0")
app.include_router(health_router)
app.include_router(jobs_router)
