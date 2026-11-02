"""Fetch the forecasts of many cities at the same time, without one failure
stopping the others."""

import asyncio
import logging
from typing import Protocol

from exceptions import APIError, CityNotFoundError, InvalidResponseError, WeatherError
from models import City, CityFailure, CityForecast, DailyForecast

logger = logging.getLogger(__name__)

MAX_CONCURRENCY = 5


class WeatherSource(Protocol):
    """Anything that can geocode and forecast (the real WeatherClient, or a fake in tests)."""

    async def geocode(self, city_name: str) -> City: ...

    async def get_forecast(self, city: City, days: int) -> list[DailyForecast]: ...


class CollectionOutcome:
    def __init__(self, successes: list[CityForecast], failures: list[CityFailure]) -> None:
        self.successes = successes
        self.failures = failures


def _friendly_reason(exc: Exception) -> str:
    """A short reason that is safe to show to API users (no stack traces)."""
    if isinstance(exc, CityNotFoundError):
        return "City not found"
    if isinstance(exc, APIError):
        return f"Weather service error: {exc}"
    if isinstance(exc, InvalidResponseError):
        return "Weather service returned data in an unexpected format"
    if isinstance(exc, WeatherError):
        return str(exc)
    return "Unexpected internal error"


async def _collect_one(
    name: str, days: int, source: WeatherSource, semaphore: asyncio.Semaphore
) -> CityForecast | CityFailure:
    # The semaphore lets only MAX_CONCURRENCY cities run at once. Each city
    # makes its requests one after the other, so at most 5 requests are in flight.
    async with semaphore:
        try:
            city = await source.geocode(name)
            forecasts = await source.get_forecast(city, days)
            logger.info("Collected %d days for %s (%s)", len(forecasts), city.name, city.country)
            return CityForecast(city=city, forecasts=forecasts)
        except Exception as exc:  # noqa: BLE001 - one city must never crash the whole request
            if isinstance(exc, WeatherError):
                logger.error("Failed to collect %r: %s", name, exc)
            else:
                logger.exception("Unexpected error while collecting %r", name)
            return CityFailure(city=name, reason=_friendly_reason(exc))


async def collect_forecasts(
    cities: list[str],
    days: int,
    source: WeatherSource,
    max_concurrency: int = MAX_CONCURRENCY,
) -> CollectionOutcome:
    """Fetch all cities concurrently; return successes and failures separately."""
    semaphore = asyncio.Semaphore(max_concurrency)
    results = await asyncio.gather(*(_collect_one(c, days, source, semaphore) for c in cities))

    successes: list[CityForecast] = []
    failures: list[CityFailure] = []
    for result in results:
        if isinstance(result, CityForecast):
            successes.append(result)
        else:
            failures.append(result)
    return CollectionOutcome(successes, failures)
