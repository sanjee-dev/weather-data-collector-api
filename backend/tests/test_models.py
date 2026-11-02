import pytest
from pydantic import ValidationError

from models import City, CollectRequest, DailyForecast


def test_city_valid():
    city = City(name="Colombo", latitude=6.93, longitude=79.85, country="Sri Lanka")
    assert city.name == "Colombo"


@pytest.mark.parametrize(
    "changes",
    [{"latitude": 91}, {"latitude": -91}, {"longitude": 181}, {"name": ""}, {"country": ""}],
)
def test_city_invalid(changes):
    data = {"name": "X", "latitude": 1.0, "longitude": 1.0, "country": "Y"} | changes
    with pytest.raises(ValidationError):
        City(**data)


def test_daily_forecast_valid_and_date_parsing():
    f = DailyForecast(date="2026-11-02", temp_max=30.1, temp_min=24.0, precipitation=1.2)
    assert f.date.year == 2026


def test_daily_forecast_invalid_date_and_negative_rain():
    with pytest.raises(ValidationError):
        DailyForecast(date="not-a-date", temp_max=1, temp_min=0, precipitation=0)
    with pytest.raises(ValidationError):
        DailyForecast(date="2026-11-02", temp_max=1, temp_min=0, precipitation=-3)


def test_collect_request_defaults_and_trimming():
    req = CollectRequest(cities=["  Colombo  "])
    assert req.cities == ["Colombo"] and req.days == 7


def test_collect_request_removes_duplicates():
    assert CollectRequest(cities=["Colombo", "colombo", "London"]).cities == ["Colombo", "London"]


@pytest.mark.parametrize(
    "body",
    [
        {"cities": []},
        {"cities": [f"City{i}" for i in range(11)]},
        {"cities": ["A"], "days": 0},
        {"cities": ["A"], "days": 15},
        {"cities": ["   "]},
        {"days": 5},
    ],
)
def test_collect_request_invalid(body):
    with pytest.raises(ValidationError):
        CollectRequest(**body)


def test_collect_request_limits_are_inclusive():
    assert len(CollectRequest(cities=[f"C{i}" for i in range(10)], days=14).cities) == 10
    assert CollectRequest(cities=["A"], days=1).days == 1
