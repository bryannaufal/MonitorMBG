"""General-purpose helper functions."""

from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


def sanitize_text(text: str) -> str:
    """Basic text sanitization: strip whitespace and normalize."""
    return " ".join(text.strip().split())


def truncate(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def safe_json_parse(raw: str) -> dict[str, Any] | None:
    """Attempt to parse a JSON string, returning None on failure."""
    import json
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
