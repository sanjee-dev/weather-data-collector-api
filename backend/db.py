"""All Supabase access lives here. The secret key stays on the server only."""

import logging
import re
from collections import defaultdict
from functools import lru_cache
from typing import Any

from supabase import Client, create_client

from config import get_settings
from exceptions import DatabaseError
from models import City, CitySummary, DailyForecast, StatsResponse, StoredForecast

logger = logging.getLogger(__name__)

TABLE = "forecasts"
CONFLICT_COLUMNS = "city,date"


@lru_cache(maxsize=1)
def get_client() -> Client:
    """Create the Supabase client ONCE and reuse it (lru_cache remembers the result)."""
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise DatabaseError("Database is not configured (SUPABASE_URL / SUPABASE_KEY missing)")
    return create_client(settings.supabase_url, settings.supabase_key)


def _safe_error_detail(exc: Exception) -> str:
    """Keep useful database error details while redacting credentials and tokens."""
    detail = str(exc)
    settings = get_settings()
    for secret in (settings.supabase_url, settings.supabase_key):
        if secret:
            detail = detail.replace(secret, "[REDACTED]")
    detail = re.sub(r"(?i)\bBearer\s+[^\s,;\"']+", "Bearer [REDACTED]", detail)
    detail = re.sub(r"\b(?:eyJ[A-Za-z0-9_-]*\.){2}[A-Za-z0-9_-]+\b", "[REDACTED JWT]", detail)
    detail = re.sub(r"\bsb_(?:secret|publishable)_[A-Za-z0-9_-]+\b", "[REDACTED]", detail)
    return detail[:1000]


def save_forecasts(city: City, forecasts: list[DailyForecast]) -> int:
    """Upsert forecasts. Calling this twice for the same city and dates updates the
    existing rows instead of creating duplicates. Returns the number of rows sent."""
    # If a date appears twice in one batch Postgres refuses the upsert, so keep the last.
    by_date = {f.date: f for f in forecasts}
    rows = [
        {
            "city": city.name,
            "country": city.country,
            "date": f.date.isoformat(),
            "temp_max": f.temp_max,
            "temp_min": f.temp_min,
            "precipitation": f.precipitation,
        }
        for f in by_date.values()
    ]
    try:
        get_client().table(TABLE).upsert(rows, on_conflict=CONFLICT_COLUMNS).execute()
    except DatabaseError:
        raise
    except Exception as exc:  # noqa: BLE001 - the supabase library can raise many types
        logger.error(
            "Database error while saving forecasts for %s (%s): %s",
            city.name,
            type(exc).__name__,
            _safe_error_detail(exc),
        )
        raise DatabaseError("Could not save forecasts to the database") from exc
    logger.info("Saved %d forecast rows for %s", len(rows), city.name)
    return len(rows)


def _escape_like(text: str) -> str:
    """Make %, _ and \\ in user input match literally inside an ILIKE pattern."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def get_forecasts(city_name: str) -> list[StoredForecast]:
    """Read the saved forecasts of one city (case-insensitive), sorted by date."""
    try:
        response = (
            get_client()
            .table(TABLE)
            .select("city,country,date,temp_max,temp_min,precipitation,created_at")
            .ilike("city", _escape_like(city_name.strip()))
            .order("date")
            .execute()
        )
        rows: list[dict[str, Any]] = response.data or []
        return [StoredForecast(**row) for row in rows]
    except DatabaseError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("Database error while reading forecasts for %r: %s", city_name, exc)
        raise DatabaseError("Could not read forecasts from the database") from exc


def get_stats() -> StatsResponse:
    """Summary of everything saved (used by the dashboard overview)."""
    try:
        response = get_client().table(TABLE).select("city,country,date").limit(10000).execute()
        rows: list[dict[str, Any]] = response.data or []
    except DatabaseError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("Database error while reading stats: %s", exc)
        raise DatabaseError("Could not read statistics from the database") from exc

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["city"]].append(row)

    cities = [
        CitySummary(
            city=name,
            country=items[0]["country"],
            records=len(items),
            first_date=min(i["date"] for i in items),
            last_date=max(i["date"] for i in items),
        )
        for name, items in sorted(grouped.items())
    ]
    return StatsResponse(total_records=len(rows), total_cities=len(cities), cities=cities)
