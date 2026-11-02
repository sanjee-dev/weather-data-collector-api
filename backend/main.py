"""FastAPI app: /health, /collect and /forecasts/{city} (plus a small /stats helper)."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import db
from config import get_settings
from exceptions import DatabaseError
from forecast_service import collect_forecasts
from logging_config import setup_logging
from models import (
    CityFailure,
    CityForecast,
    CollectedCity,
    CollectRequest,
    CollectResponse,
    ForecastsResponse,
    StatsResponse,
)
from weather_client import WeatherClient

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Weather Data Collector API started")
    yield
    logger.info("Weather Data Collector API stopped")


app = FastAPI(
    title="Weather Data Collector API",
    description="Collects weather forecasts from Open-Meteo and stores them in Supabase.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    # Full details go to the log; the client only gets a generic message.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def _save_city(item: CityForecast) -> CollectedCity | CityFailure:
    """Save one city. The Supabase client is blocking, so it runs in a worker thread."""
    try:
        saved = await asyncio.to_thread(db.save_forecasts, item.city, item.forecasts)
    except DatabaseError as exc:
        logger.error("Could not save %s: %s", item.city.name, exc)
        return CityFailure(
            city=item.city.name, reason="Forecast was downloaded but could not be saved"
        )
    return CollectedCity(
        city=item.city.name,
        country=item.city.country,
        latitude=item.city.latitude,
        longitude=item.city.longitude,
        records_saved=saved,
        forecasts=item.forecasts,
    )


@app.post("/collect", response_model=CollectResponse)
async def collect(request: CollectRequest) -> CollectResponse:
    logger.info("Collect request: %d cities, %d days", len(request.cities), request.days)
    async with WeatherClient() as client:
        outcome = await collect_forecasts(request.cities, request.days, client)

    saved = await asyncio.gather(*(_save_city(item) for item in outcome.successes))
    successes = [s for s in saved if isinstance(s, CollectedCity)]
    failures = outcome.failures + [s for s in saved if isinstance(s, CityFailure)]

    logger.info("Collect finished: %d succeeded, %d failed", len(successes), len(failures))
    return CollectResponse(
        requested=len(request.cities),
        succeeded=len(successes),
        failed=len(failures),
        total_records_saved=sum(s.records_saved for s in successes),
        successes=successes,
        failures=failures,
    )


@app.get("/forecasts/{city}", response_model=ForecastsResponse)
async def read_forecasts(city: str) -> ForecastsResponse:
    try:
        rows = await asyncio.to_thread(db.get_forecasts, city)
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc
    if not rows:
        raise HTTPException(status_code=404, detail=f"No saved forecasts for {city!r}")
    return ForecastsResponse(
        city=rows[0].city, country=rows[0].country, count=len(rows), forecasts=rows
    )


@app.get("/stats", response_model=StatsResponse)
async def stats() -> StatsResponse:
    """Extra endpoint (not in the task PDF) used by the dashboard overview."""
    try:
        return await asyncio.to_thread(db.get_stats)
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc
