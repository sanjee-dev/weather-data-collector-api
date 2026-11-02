from unittest.mock import MagicMock

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from main import app
from tests.helpers import GEOCODE_OK, forecast_payload
from weather_client import FORECAST_URL, GEOCODING_URL

client = TestClient(app, raise_server_exceptions=False)


def upsert_mock(fake_supabase: MagicMock) -> MagicMock:
    return fake_supabase.table.return_value.upsert


def read_chain(fake_supabase: MagicMock) -> MagicMock:
    return fake_supabase.table.return_value.select.return_value.ilike.return_value.order


# --- /health -----------------------------------------------------------------


def test_health():
    response = client.get("/health")
    assert response.status_code == 200 and response.json() == {"status": "ok"}


# --- /collect validation -----------------------------------------------------


def test_collect_11_cities_returns_422():
    response = client.post("/collect", json={"cities": [f"City{i}" for i in range(11)], "days": 7})
    assert response.status_code == 422


@pytest.mark.parametrize(
    "body",
    [
        {"cities": ["Colombo"], "days": 0},
        {"cities": ["Colombo"], "days": 15},
        {"cities": []},
        {"cities": [""]},
        {"days": 7},
        {"cities": "Colombo"},
    ],
)
def test_collect_invalid_bodies_return_422(body):
    assert client.post("/collect", json=body).status_code == 422


def test_invalid_request_never_reaches_database(fake_supabase):
    client.post("/collect", json={"cities": [], "days": 7})
    upsert_mock(fake_supabase).assert_not_called()


# --- /collect behaviour -----------------------------------------------------


@respx.mock
def test_collect_success_saves_with_upsert(fake_supabase):
    respx.get(GEOCODING_URL).mock(return_value=httpx.Response(200, json=GEOCODE_OK))
    respx.get(FORECAST_URL).mock(return_value=httpx.Response(200, json=forecast_payload(3)))

    response = client.post("/collect", json={"cities": ["Colombo"], "days": 3})

    assert response.status_code == 200
    body = response.json()
    assert (body["requested"], body["succeeded"], body["failed"]) == (1, 1, 0)
    assert body["total_records_saved"] == 3
    assert body["successes"][0]["city"] == "Colombo"
    assert len(body["successes"][0]["forecasts"]) == 3
    upsert = upsert_mock(fake_supabase)
    upsert.assert_called_once()
    assert upsert.call_args.kwargs["on_conflict"] == "city,date"


@respx.mock
def test_collect_partial_failure_reports_reason(fake_supabase):
    def geocode(request: httpx.Request) -> httpx.Response:
        if request.url.params["name"] == "Xyzabc":
            return httpx.Response(200, json={"generationtime_ms": 1})
        return httpx.Response(200, json=GEOCODE_OK)

    respx.get(GEOCODING_URL).mock(side_effect=geocode)
    respx.get(FORECAST_URL).mock(return_value=httpx.Response(200, json=forecast_payload(2)))

    response = client.post("/collect", json={"cities": ["Colombo", "Xyzabc"], "days": 2})

    body = response.json()
    assert response.status_code == 200
    assert (body["succeeded"], body["failed"]) == (1, 1)
    assert body["failures"] == [{"city": "Xyzabc", "reason": "City not found"}]
    assert upsert_mock(fake_supabase).call_count == 1


@respx.mock
def test_collect_database_failure_is_reported_per_city(fake_supabase):
    respx.get(GEOCODING_URL).mock(return_value=httpx.Response(200, json=GEOCODE_OK))
    respx.get(FORECAST_URL).mock(return_value=httpx.Response(200, json=forecast_payload(2)))
    upsert_mock(fake_supabase).return_value.execute.side_effect = RuntimeError("db down")

    response = client.post("/collect", json={"cities": ["Colombo"], "days": 2})

    body = response.json()
    assert response.status_code == 200
    assert body["succeeded"] == 0 and body["failed"] == 1
    assert "db down" not in response.text  # no internal details for the client


# --- /forecasts/{city} --------------------------------------------------------


def test_forecasts_returns_404_when_no_data(fake_supabase):
    read_chain(fake_supabase).return_value.execute.return_value.data = []
    response = client.get("/forecasts/Nowhere")
    assert response.status_code == 404


def test_forecasts_returns_saved_rows_sorted(fake_supabase):
    read_chain(fake_supabase).return_value.execute.return_value.data = [
        {
            "city": "Colombo",
            "country": "Sri Lanka",
            "date": "2026-11-01",
            "temp_max": 31,
            "temp_min": 24,
            "precipitation": 0,
            "created_at": None,
        },
        {
            "city": "Colombo",
            "country": "Sri Lanka",
            "date": "2026-11-02",
            "temp_max": 32,
            "temp_min": 25,
            "precipitation": 1,
            "created_at": None,
        },
    ]
    response = client.get("/forecasts/colombo")
    body = response.json()
    assert response.status_code == 200
    assert body["city"] == "Colombo" and body["count"] == 2
    assert [f["date"] for f in body["forecasts"]] == ["2026-11-01", "2026-11-02"]
    read_chain(fake_supabase).assert_called_once_with("date")


def test_forecasts_database_error_returns_503(fake_supabase):
    fake_supabase.table.side_effect = RuntimeError("down")
    response = client.get("/forecasts/Colombo")
    assert response.status_code == 503
    assert "down" not in response.text


# --- /stats and CORS -----------------------------------------------------------


def test_stats(fake_supabase):
    stats_query = fake_supabase.table.return_value.select.return_value.limit.return_value
    stats_query.execute.return_value.data = [
        {"city": "Colombo", "country": "Sri Lanka", "date": "2026-11-01"},
    ]
    body = client.get("/stats").json()
    assert body["total_records"] == 1 and body["cities"][0]["city"] == "Colombo"


def test_cors_allows_the_local_frontend():
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_blocks_other_origins():
    response = client.get("/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in response.headers
