"""Reads settings from environment variables (and from a local .env file)."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Loads the .env file located in the backend directory.
# Environment variables already containing non-empty values are preserved.
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")

# Remove only empty inherited variables so .env can supply their values.
for name in ("SUPABASE_URL", "SUPABASE_KEY"):
    if not os.getenv(name, "").strip():
        os.environ.pop(name, None)

load_dotenv(dotenv_path=dotenv_path)


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_key: str
    cors_origins: list[str]
    log_file: str
    log_level: str


def get_settings() -> Settings:
    """Read the settings fresh each time."""
    origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )

    return Settings(
        supabase_url=os.getenv("SUPABASE_URL", "").strip(),
        supabase_key=os.getenv("SUPABASE_KEY", "").strip(),
        cors_origins=[o.strip() for o in origins.split(",") if o.strip()],
        # An empty LOG_FILE turns file logging off (the console is always on).
        log_file=os.getenv("LOG_FILE", "app.log"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )