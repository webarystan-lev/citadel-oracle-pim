"""Shared date handling for PIM records and the calendar."""

from datetime import date, datetime, timezone
from typing import Any, Dict, Optional


def parse_record_date(value: Any) -> Optional[date]:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 100_000_000_000:
            timestamp /= 1000
        try:
            return datetime.fromtimestamp(timestamp, tz=timezone.utc).date()
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str) and value.strip():
        try:
            return date.fromisoformat(value.strip()[:10])
        except ValueError:
            return None
    return None


def record_matches_date(record_type: str, record: Dict[str, Any], selected_date: date) -> bool:
    """Match explicit timeline dates, then the record's natural/creation date."""
    start = parse_record_date(record.get("startDate"))
    end = parse_record_date(record.get("endDate"))

    if start is not None or end is not None:
        if (start is None or selected_date >= start) and (end is None or selected_date <= end):
            return True

    natural_date = (
        parse_record_date(record.get("date"))
        if record_type == "journal"
        else parse_record_date(record.get("createdAt"))
    )
    return natural_date == selected_date
