"""Async client for the free Open-Meteo APIs (geocoding + daily forecast).

Retry rules (from the task):
  * Retry up to 3 times on timeouts, network errors and HTTP 5xx.
  * Wait longer each time: 1s, 2s, 4s (exponential backoff).
  * Never retry on HTTP 4xx or when the city is not found.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import Any

import httpx

from exceptions import APIError, CityNotFoundError, InvalidResponseError
from models import City, DailyForecast

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DAILY_FIELDS = "temperature_2m_max,temperature_2m_min,precipitation_sum"

REQUEST_TIMEOUT_SECONDS = 10.0
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 1.0  # waits: 1s, 2s, 4s

SleepFunc = Callable[[float], Awaitable[None]]


class WeatherClient:
    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        *,
        max_retries: int = MAX_RETRIES,
        backoff_base: float = BACKOFF_BASE_SECONDS,
        sleep: SleepFunc = asyncio.sleep,
    ) -> None:
        # Every request gets a timeout (requirement). Tests can pass their own
        # `sleep` function so they do not really wait 1 + 2 + 4 seconds.
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=httpx.Timeout(REQUEST_TIMEOUT_SECONDS))
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._sleep = sleep

    async def __aenter__(self) -> "WeatherClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    # --- public methods -------------------------------------------------------

    async def geocode(self, city_name: str) -> City:
        """Find a city's coordinates. Raises CityNotFoundError if there is no match."""
        name = city_name.strip()
        if not name:
            raise CityNotFoundError(city_name)

        data = await self._get_json(
            GEOCODING_URL, {"name": name, "count": 1, "language": "en", "format": "json"}
        )
        results = data.get("results") if isinstance(data, dict) else None
        if not results:
            # Open-Meteo answers 200 OK *without* a "results" key for unknown cities.
            raise CityNotFoundError(name)

        try:
            first = results[0]
            return City(
                name=first["name"],
                latitude=first["latitude"],
                longitude=first["longitude"],
                country=first.get("country") or first.get("country_code") or "Unknown",
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidResponseError("Geocoding response had an unexpected format") from exc

    async def get_forecast(self, city: City, days: int) -> list[DailyForecast]:
        """Download `days` daily forecasts for a city and validate them."""
        data = await self._get_json(
            FORECAST_URL,
            {
                "latitude": city.latitude,
                "longitude": city.longitude,
                "daily": DAILY_FIELDS,
                "timezone": "auto",
                "forecast_days": days,
            },
        )
        try:
            daily = data["daily"]
            dates = daily["time"]
            maxima = daily["temperature_2m_max"]
            minima = daily["temperature_2m_min"]
            rain = daily["precipitation_sum"]
            if not (len(dates) == len(maxima) == len(minima) == len(rain)):
                raise ValueError("daily lists have different lengths")
            forecasts = [
                DailyForecast(date=d, temp_max=hi, temp_min=lo, precipitation=p)
                for d, hi, lo, p in zip(dates, maxima, minima, rain, strict=True)
            ]
        except (KeyError, TypeError, ValueError) as exc:
            # pydantic's ValidationError is a ValueError subclass.
            raise InvalidResponseError("Forecast response had an unexpected format") from exc

        if not forecasts:
            raise InvalidResponseError("Forecast response contained no days")
        return forecasts

    # --- retry logic ----------------------------------------------------------

    async def _get_json(self, url: str, params: dict[str, Any]) -> Any:
        """GET a URL and return its JSON, retrying only the failures that deserve it."""
        attempt = 0
        while True:
            error = await self._try_once(url, params)
            if isinstance(error, APIError):
                if not error.retryable or attempt >= self._max_retries:
                    if error.retryable:
                        logger.error("Giving up after %d retries: %s", self._max_retries, error)
                    raise error
                delay = self._backoff_base * (2**attempt)
                attempt += 1
                logger.warning(
                    "Retry %d/%d in %.0fs after error: %s", attempt, self._max_retries, delay, error
                )
                await self._sleep(delay)
                continue
            return error

    async def _try_once(self, url: str, params: dict[str, Any]) -> Any:
        """Make ONE request. Returns the JSON data, or an APIError (not raised)."""
        try:
            response = await self._client.get(url, params=params)
        except httpx.TimeoutException:
            return APIError("The weather service timed out", retryable=True)
        except httpx.TransportError as exc:  # connection refused, DNS failure, ...
            return APIError(f"Network error: {type(exc).__name__}", retryable=True)

        status = response.status_code
        if status >= 500:
            return APIError(
                f"Weather service returned HTTP {status}", status_code=status, retryable=True
            )
        if status >= 400 or not response.is_success:
            # 4xx = our request is wrong, so asking again would not help.
            return APIError(
                f"Weather service rejected the request (HTTP {status})",
                status_code=status,
                retryable=False,
            )
        try:
            return response.json()
        except ValueError as exc:
            raise InvalidResponseError("Weather service did not return valid JSON") from exc
