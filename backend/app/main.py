"""Oasis API application entrypoint."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, SessionLocal, engine
from .seed_data import seed_species
from .routers import (
    alerts, audit, auth, climate, dashboard, diagnosis, differential, farms,
    fertigation, irrigation, sensors, soil_water, tasks, variety,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        seed_species(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Smart Desert Orchard Management Platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = "/api/v1"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(farms.router, prefix=api_prefix)
app.include_router(soil_water.router, prefix=api_prefix)
app.include_router(sensors.router, prefix=api_prefix)
app.include_router(climate.router, prefix=api_prefix)
app.include_router(irrigation.router, prefix=api_prefix)
app.include_router(diagnosis.router, prefix=api_prefix)
app.include_router(differential.router, prefix=api_prefix)
app.include_router(fertigation.router, prefix=api_prefix)
app.include_router(alerts.router, prefix=api_prefix)
app.include_router(tasks.router, prefix=api_prefix)
app.include_router(variety.router, prefix=api_prefix)
app.include_router(dashboard.router, prefix=api_prefix)
app.include_router(audit.router, prefix=api_prefix)


@app.get("/")
def root():
    return {"app": settings.app_name, "status": "ok", "docs": "/docs"}


# Serve the frontend SPA (dependency-free) at /app
_frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/app", StaticFiles(directory=str(_frontend_dir), html=True), name="app")
