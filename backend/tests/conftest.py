import os
from unittest.mock import MagicMock

# Must run before `main` is imported: no log file while testing.
os.environ["LOG_FILE"] = ""

import pytest  # noqa: E402

import db  # noqa: E402

# Keep the real function: one test checks its missing-credentials behaviour.
REAL_GET_CLIENT = db.get_client


@pytest.fixture(autouse=True)
def fake_supabase(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace Supabase with a mock in EVERY test, so no test can touch a real database."""
    client = MagicMock(name="supabase_client")
    monkeypatch.setattr(db, "get_client", lambda: client)
    return client
