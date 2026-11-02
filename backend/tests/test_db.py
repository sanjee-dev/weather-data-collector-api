import logging
from unittest.mock import MagicMock

import pytest

import db
from exceptions import DatabaseError
from models import City, DailyForecast

CITY = City(name="Colombo", latitude=6.93, longitude=79.85, country="Sri Lanka")
DAYS = [
    DailyForecast(date="2026-11-01", temp_max=31, temp_min=24, precipitation=0.0),
    DailyForecast(date="2026-11-02", temp_max=32, temp_min=25, precipitation=2.5),
]


def test_save_uses_upsert_with_city_date_conflict(fake_supabase: MagicMock):
    saved = db.save_forecasts(CITY, DAYS)

    fake_supabase.table.assert_called_once_with("forecasts")
    upsert = fake_supabase.table.return_value.upsert
    upsert.assert_called_once()
    rows = upsert.call_args.args[0]
    assert upsert.call_args.kwargs == {"on_conflict": "city,date"}
    assert saved == 2 and len(rows) == 2
    assert rows[0] == {
        "city": "Colombo",
        "country": "Sri Lanka",
        "date": "2026-11-01",
        "temp_max": 31,
        "temp_min": 24,
        "precipitation": 0.0,
    }
    upsert.return_value.execute.assert_called_once()


def test_save_removes_duplicate_dates_in_one_batch(fake_supabase: MagicMock):
    db.save_forecasts(CITY, DAYS + [DAYS[0]])
    rows = fake_supabase.table.return_value.upsert.call_args.args[0]
    assert len(rows) == 2


def test_save_database_failure_becomes_database_error(fake_supabase: MagicMock):
    fake_supabase.table.return_value.upsert.return_value.execute.side_effect = RuntimeError("boom")
    with pytest.raises(DatabaseError) as info:
        db.save_forecasts(CITY, DAYS)
    assert "boom" not in str(info.value)  # internal details are not leaked


def test_save_database_error_is_logged_with_secrets_redacted(
    fake_supabase: MagicMock, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    url = "https://private-project.supabase.co"
    key = "sb_secret_test-key-value"
    monkeypatch.setenv("SUPABASE_URL", url)
    monkeypatch.setenv("SUPABASE_KEY", key)
    fake_supabase.table.return_value.upsert.return_value.execute.side_effect = RuntimeError(
        f"HTTP 401 permission denied for {url}; key={key}; Authorization: Bearer test-token"
    )

    with caplog.at_level(logging.ERROR, logger="db"):
        with pytest.raises(DatabaseError):
            db.save_forecasts(CITY, DAYS)

    assert "HTTP 401 permission denied" in caplog.text
    assert "[REDACTED]" in caplog.text
    assert "Bearer [REDACTED]" in caplog.text
    assert url not in caplog.text
    assert key not in caplog.text
    assert "test-token" not in caplog.text


def test_get_forecasts_sorted_by_date_and_parsed(fake_supabase: MagicMock):
    chain = fake_supabase.table.return_value.select.return_value.ilike.return_value.order
    chain.return_value.execute.return_value.data = [
        {
            "city": "Colombo",
            "country": "Sri Lanka",
            "date": "2026-11-01",
            "temp_max": 31,
            "temp_min": 24,
            "precipitation": 0,
            "created_at": "2026-11-02T04:00:00+00:00",
        },
    ]
    rows = db.get_forecasts("Colombo")
    assert rows[0].city == "Colombo" and rows[0].date.isoformat() == "2026-11-01"
    chain.assert_called_once_with("date")  # .order("date")


def test_get_forecasts_escapes_like_wildcards(fake_supabase: MagicMock):
    db.get_forecasts("50%_off")
    ilike = fake_supabase.table.return_value.select.return_value.ilike
    ilike.assert_called_once_with("city", "50\\%\\_off")


def test_get_forecasts_empty(fake_supabase: MagicMock):
    chain = fake_supabase.table.return_value.select.return_value.ilike.return_value.order
    chain.return_value.execute.return_value.data = []
    assert db.get_forecasts("Nowhere") == []


def test_get_forecasts_database_failure(fake_supabase: MagicMock):
    fake_supabase.table.side_effect = RuntimeError("connection lost")
    with pytest.raises(DatabaseError):
        db.get_forecasts("Colombo")


def test_get_stats_groups_by_city(fake_supabase: MagicMock):
    stats_query = fake_supabase.table.return_value.select.return_value.limit.return_value
    stats_query.execute.return_value.data = [
        {"city": "Colombo", "country": "Sri Lanka", "date": "2026-11-01"},
        {"city": "Colombo", "country": "Sri Lanka", "date": "2026-11-03"},
        {"city": "London", "country": "United Kingdom", "date": "2026-11-01"},
    ]
    stats = db.get_stats()
    assert stats.total_records == 3 and stats.total_cities == 2
    assert stats.cities[0].city == "Colombo" and stats.cities[0].records == 2
    assert stats.cities[0].last_date.isoformat() == "2026-11-03"


def test_missing_credentials_raise_clear_error(monkeypatch: pytest.MonkeyPatch):
    from tests.conftest import REAL_GET_CLIENT

    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_KEY", "")
    REAL_GET_CLIENT.cache_clear()
    with pytest.raises(DatabaseError, match="not configured"):
        REAL_GET_CLIENT()
