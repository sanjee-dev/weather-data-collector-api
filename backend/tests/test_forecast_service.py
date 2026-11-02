import asyncio

import pytest

from exceptions import APIError, CityNotFoundError
from forecast_service import collect_forecasts
from models import City, DailyForecast


def make_forecast() -> list[DailyForecast]:
    return [DailyForecast(date="2026-11-01", temp_max=30, temp_min=24, precipitation=0)]


class FakeSource:
    """A fake weather source that tracks how many cities are being handled at once."""

    def __init__(self, bad: dict[str, Exception] | None = None, delay: float = 0.01) -> None:
        self.bad = bad or {}
        self.delay = delay
        self.in_flight = 0
        self.max_in_flight = 0
        self.geocoded: list[str] = []

    async def geocode(self, city_name: str) -> City:
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            await asyncio.sleep(self.delay)
            self.geocoded.append(city_name)
            if city_name in self.bad:
                raise self.bad[city_name]
            return City(name=city_name, latitude=1, longitude=2, country="Testland")
        finally:
            self.in_flight -= 1

    async def get_forecast(self, city: City, days: int) -> list[DailyForecast]:
        return make_forecast()


async def test_all_cities_succeed():
    outcome = await collect_forecasts(["A", "B", "C"], 1, FakeSource())
    assert [s.city.name for s in outcome.successes] == ["A", "B", "C"]
    assert outcome.failures == []


async def test_one_failure_does_not_stop_the_others():
    source = FakeSource(bad={"Xyzabc": CityNotFoundError("Xyzabc")})
    outcome = await collect_forecasts(["Colombo", "Xyzabc", "London"], 1, source)
    assert [s.city.name for s in outcome.successes] == ["Colombo", "London"]
    assert len(outcome.failures) == 1
    assert outcome.failures[0].city == "Xyzabc" and outcome.failures[0].reason == "City not found"


async def test_api_error_reason_is_reported_without_internals():
    source = FakeSource(bad={"A": APIError("Weather service returned HTTP 500", retryable=True)})
    outcome = await collect_forecasts(["A"], 1, source)
    assert "HTTP 500" in outcome.failures[0].reason


async def test_unexpected_exception_is_contained_and_hidden():
    source = FakeSource(bad={"A": RuntimeError("secret internal detail")})
    outcome = await collect_forecasts(["A", "B"], 1, source)
    assert [s.city.name for s in outcome.successes] == ["B"]
    assert outcome.failures[0].reason == "Unexpected internal error"
    assert "secret" not in outcome.failures[0].reason


async def test_failures_are_logged_as_errors(caplog):
    await collect_forecasts(["A"], 1, FakeSource(bad={"A": CityNotFoundError("A")}))
    assert any(r.levelname == "ERROR" for r in caplog.records)


async def test_cities_are_processed_concurrently():
    source = FakeSource(delay=0.05)
    loop = asyncio.get_running_loop()
    start = loop.time()
    await collect_forecasts([f"C{i}" for i in range(5)], 1, source)
    # 5 cities x 0.05s one-by-one would be 0.25s; concurrently it is about 0.05s.
    assert loop.time() - start < 0.2
    assert source.max_in_flight == 5


async def test_concurrency_is_limited_to_five():
    source = FakeSource(delay=0.02)
    outcome = await collect_forecasts([f"C{i}" for i in range(10)], 1, source)
    assert len(outcome.successes) == 10
    assert source.max_in_flight == 5


@pytest.mark.parametrize("limit", [1, 2])
async def test_custom_concurrency_limit(limit):
    source = FakeSource(delay=0.01)
    await collect_forecasts([f"C{i}" for i in range(6)], 1, source, max_concurrency=limit)
    assert source.max_in_flight == limit
