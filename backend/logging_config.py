"""Logging setup: every message goes to the console and to a file (app.log)."""

import logging
import sys

from config import get_settings

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_configured = False


def setup_logging() -> None:
    """Configure the root logger once. Safe to call many times."""
    global _configured
    if _configured:
        return

    settings = get_settings()
    root = logging.getLogger()
    root.setLevel(settings.log_level)
    formatter = logging.Formatter(LOG_FORMAT)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    if settings.log_file:
        try:
            file_handler = logging.FileHandler(settings.log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except OSError as exc:
            # Serverless hosts (like Vercel) have a read-only disk, so a log
            # file is impossible there. We keep going with console logs only.
            root.warning("File logging disabled (%s): %s", settings.log_file, exc)

    # httpx logs every request URL at INFO level; keep our log readable.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    _configured = True
