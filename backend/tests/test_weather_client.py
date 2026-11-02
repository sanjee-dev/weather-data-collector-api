import httpx
import pytest
import respx

from exceptions import APIError, CityNotFoundError, InvalidResponseError
from models import City
from tests.helpers import GEOCODE_OK, forecast_payload
from weather_client import FORECAST_URL, GEOCODING_URL, WeatherClient

CITY = City(name="Colombo", latitude=6.93, longitude=79.85, country="Sri Lanka")


class SleepRecorder:
    """Stands in for asyncio.sleep so tests run instantly and we can check the delays."""

    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


@pytest.fixture
def sleeper() -> SleepRecorder:
    return SleepRecorder()


@pytest.fixture
def client(sleeper: SleepRecorder) -> WeatherClient:
    return WeatherClient(sleep=sleeper)


@respx.mock
async def test_geocode_success(client):
    route = respx.get(GEOCODING_URL).mock(return_value=httpx.Response(200, json=GEOCODE_OK))
    city = await client.geocode("Colombo")
    assert (city.name, city.country, city.latitude) == ("Colombo", "Sri Lanka", 6.93)
    assert route.calls.last.request.url.params["name"] == "Colombo"


@respx.mock
async def test_geocode_city_not_found_does_not_retry(client, sleeper):
    route = respx.get(GEOCODING_URL).mock(
        return_value=httpx.Response(200, json={"generationtime_ms": 0.5})
    )
    with pytest.raises(CityNotFoundError):
        await client.geocode("Xyzabc")
    assert route.call_count == 1 and sleeper.delays == []


@pytest.mark.parametrize("name", ["", "   "])
async def test_geocode_empty_name(client, name):
    with pytest.raises(CityNotFoundError):
        await client.geocode(name)


@respx.mock
async def test_geocode_unexpected_format(client):
    respx.get(GEOCODING_URL).mock(
        return_value=httpx.Response(200, json={"results": [{"name": "X"}]})
    )
    with pytest.raises(InvalidResponseError):
        await client.geocode("X")


@respx.mock
async def test_invalid_json_is_not_retried(client, sleeper):
    route = respx.get(GEOCODING_URL).mock(return_value=httpx.Response(200, text="<html>oops"))
    with pytest.raises(InvalidResponseError):
        await client.geocode("Colombo")
    assert route.call_count == 1 and sleeper.delays == []


@respx.mock
async def test_forecast_success(client):
    route = respx.get(FORECAST_URL).mock(return_value=httpx.Response(200, json=forecast_payload(3)))
    forecasts = await client.get_forecast(CITY, 3)
    assert len(forecasts) == 3
    assert forecasts[0].temp_max == 31.0 and forecasts[2].precipitation == 1.0
    params = route.calls.last.request.url.params
    assert params["timezone"] == "auto" and params["forecast_days"] == "3"
    assert params["daily"] == "temperature_2m_max,temperature_2m_min,precipitation_sum"


@respx.mock
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"daily": {"time": ["2026-11-01"]}},
        {
            "daily": {
                "time": ["2026-11-01", "2026-11-02"],
                "temperature_2m_max": [1],
                "temperature_2m_min": [1],
                "precipitation_sum": [1],
            }
        },
        {
            "daily": {
                "time": ["bad-date"],
                "temperature_2m_max": [1],
                "temperature_2m_min": [0],
                "precipitation_sum": [0],
            }
        },
        {
            "daily": {
                "time": [],
                "temperature_2m_max": [],
                "temperature_2m_min": [],
                "precipitation_sum": [],
            }
        },
    ],
)
async def test_forecast_invalid_response(client, payload):
    respx.get(FORECAST_URL).mock(return_value=httpx.Response(200, json=payload))
    with pytest.raises(InvalidResponseError):
        await client.get_forecast(CITY, 1)


@respx.mock
async def test_forecast_accepts_null_values(client):
    payload = forecast_payload(1)
    payload["daily"]["precipitation_sum"] = [None]
    respx.get(FORECAST_URL).mock(return_value=httpx.Response(200, json=payload))
    assert (await client.get_forecast(CITY, 1))[0].precipitation is None


# --- retry behaviour ---------------------------------------------------------


@respx.mock
async def test_500_then_success_retries_once(client, sleeper):
    route = respx.get(GEOCODING_URL).mock(
        side_effect=[httpx.Response(500), httpx.Response(200, json=GEOCODE_OK)]
    )
    city = await client.geocode("Colombo")
    assert city.name == "Colombo"
    assert route.call_count == 2
    assert sleeper.delays == [1.0]


@respx.mock
async def test_500_every_time_gives_up_after_3_retries(client, sleeper):
    route = respx.get(GEOCODING_URL).mock(return_value=httpx.Response(500))
    with pytest.raises(APIError) as info:
        await client.geocode("Colombo")
    assert info.value.status_code == 500
    assert route.call_count == 4  # 1 first try + 3 retries
    assert sleeper.delays == [1.0, 2.0, 4.0]  # exponential backoff


@respx.mock
@pytest.mark.parametrize("status", [400, 404, 429])
async def test_4xx_is_not_retried(client, sleeper, status):
    route = respx.get(GEOCODING_URL).mock(return_value=httpx.Response(status))
    with pytest.raises(APIError) as info:
        await client.geocode("Colombo")
    assert info.value.status_code == status and not info.value.retryable
    assert route.call_count == 1 and sleeper.delays == []


@respx.mock
async def test_timeout_is_retried_then_succeeds(client, sleeper):
    route = respx.get(GEOCODING_URL).mock(
        side_effect=[httpx.ReadTimeout("slow"), httpx.Response(200, json=GEOCODE_OK)]
    )
    assert (await client.geocode("Colombo")).name == "Colombo"
    assert route.call_count == 2 and sleeper.delays == [1.0]


@respx.mock
async def test_network_error_retried_until_exhausted(client, sleeper):
    route = respx.get(FORECAST_URL).mock(side_effect=httpx.ConnectError("no network"))
    with pytest.raises(APIError, match="Network error"):
        await client.get_forecast(CITY, 2)
    assert route.call_count == 4 and sleeper.delays == [1.0, 2.0, 4.0]


@respx.mock
async def test_retries_are_logged_as_warnings(client, caplog):
    respx.get(GEOCODING_URL).mock(return_value=httpx.Response(503))
    with pytest.raises(APIError):
        await client.geocode("Colombo")
    levels = [r.levelname for r in caplog.records]
    assert levels.count("WARNING") == 3 and "ERROR" in levels


def test_client_has_a_timeout_by_default():
    timeout = WeatherClient()._client.timeout
    assert timeout.read == 10.0 and timeout.connect == 10.0
