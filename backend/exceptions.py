"""Custom exceptions for the Weather Data Collector.

Using our own exception classes (instead of the plain `Exception`) lets the rest
of the code catch exactly the problems it knows how to handle.
"""


class WeatherError(Exception):
    """Base class for every error raised by this project."""


class CityNotFoundError(WeatherError):
    """The geocoding API has no match for the requested city name."""

    def __init__(self, city: str) -> None:
        self.city = city
        super().__init__(f"City not found: {city!r}")


class APIError(WeatherError):
    """The weather API could not be reached or answered with an error.

    `retryable` tells the retry logic whether trying again could help
    (timeouts, network errors and HTTP 5xx) or not (HTTP 4xx).
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        retryable: bool = False,
    ) -> None:
        self.status_code = status_code
        self.retryable = retryable
        super().__init__(message)


class InvalidResponseError(WeatherError):
    """The weather API answered, but the data was not in the expected format."""


class DatabaseError(WeatherError):
    """Something went wrong while talking to Supabase."""
