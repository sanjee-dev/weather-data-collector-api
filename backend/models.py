"""Pydantic models: they describe and *validate* all data that moves around."""

import datetime as dt
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator

MAX_CITIES = 10
MIN_DAYS = 1
MAX_DAYS = 14

# A city name from the user: no surrounding spaces, 1-100 characters.
CityName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class City(BaseModel):
    name: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    country: str = Field(min_length=1)


class DailyForecast(BaseModel):
    date: dt.date
    # Open-Meteo can send null for a value it does not have, so these may be None.
    temp_max: float | None = None
    temp_min: float | None = None
    precipitation: float | None = Field(default=None, ge=0)


class CollectRequest(BaseModel):
    """Body of POST /collect: at most 10 cities and 1-14 days."""

    cities: list[CityName] = Field(min_length=1, max_length=MAX_CITIES)
    days: int = Field(default=7, ge=MIN_DAYS, le=MAX_DAYS)

    @field_validator("cities")
    @classmethod
    def remove_duplicates(cls, cities: list[str]) -> list[str]:
        """'colombo' and 'Colombo ' are the same city: keep the first one only."""
        seen: set[str] = set()
        unique: list[str] = []
        for name in cities:
            key = name.casefold()
            if key not in seen:
                seen.add(key)
                unique.append(name)
        return unique


# --- Internal results of a collection run -----------------------------------


class CityForecast(BaseModel):
    city: City
    forecasts: list[DailyForecast]


class CityFailure(BaseModel):
    city: str
    reason: str


# --- API response models ------------------------------------------------------


class CollectedCity(BaseModel):
    city: str
    country: str
    latitude: float
    longitude: float
    records_saved: int
    forecasts: list[DailyForecast]


class CollectResponse(BaseModel):
    requested: int
    succeeded: int
    failed: int
    total_records_saved: int
    successes: list[CollectedCity]
    failures: list[CityFailure]


class StoredForecast(BaseModel):
    """One row read back from the Supabase `forecasts` table."""

    city: str
    country: str
    date: dt.date
    temp_max: float | None = None
    temp_min: float | None = None
    precipitation: float | None = None
    created_at: dt.datetime | None = None


class ForecastsResponse(BaseModel):
    city: str
    country: str
    count: int
    forecasts: list[StoredForecast]


class CitySummary(BaseModel):
    city: str
    country: str
    records: int
    first_date: dt.date
    last_date: dt.date


class StatsResponse(BaseModel):
    total_records: int
    total_cities: int
    cities: list[CitySummary]
