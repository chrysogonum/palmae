"""Palmae API — FastAPI application entry point."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .config import settings
from .db import engine
from .routes import router

app = FastAPI(title="Palmae API", version="0.1.0")
app.include_router(router)

# Vite dev server + (later) the deployed frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "palmae-api"}


@app.get("/health/db")
def health_db() -> dict:
    """Confirm the database is reachable and PostGIS is installed."""
    if engine is None:
        return {"database": "unconfigured", "hint": "set DATABASE_URL in api/.env"}
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        try:
            postgis = conn.execute(text("SELECT PostGIS_Version()")).scalar()
        except Exception:
            postgis = None
    return {
        "database": "reachable",
        "postgis": postgis or "NOT INSTALLED — enable the postgis extension in Supabase",
        "configured": bool(settings.database_url),
    }
