"""Shared sample data for the tests."""

GEOCODE_OK = {
    "results": [{"name": "Colombo", "latitude": 6.93, "longitude": 79.85, "country": "Sri Lanka"}]
}


def forecast_payload(days: int = 3) -> dict:
    return {
        "daily": {
            "time": [f"2026-11-{d:02d}" for d in range(1, days + 1)],
            "temperature_2m_max": [31.0 + d for d in range(days)],
            "temperature_2m_min": [24.0 + d for d in range(days)],
            "precipitation_sum": [0.5 * d for d in range(days)],
        }
    }
