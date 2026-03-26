from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .models import Event


def _ical_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,").replace("\n", r"\n")


def _format_dt(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return dt.strftime("%Y%m%dT%H%M%SZ")


def write_ical(events: list[Event], path: Path, prodid: str = "-//Gruener Podcast Feed//EN") -> None:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{prodid}",
        "CALSCALE:GREGORIAN",
    ]

    for event in events:
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uuid4()}")
        lines.append(f"SUMMARY:{_ical_escape(event.title)}")
        if event.start_at and (formatted := _format_dt(event.start_at)):
            lines.append(f"DTSTART:{formatted}")
        if event.end_at and (formatted := _format_dt(event.end_at)):
            lines.append(f"DTEND:{formatted}")
        if event.location:
            lines.append(f"LOCATION:{_ical_escape(event.location)}")
        if event.description:
            lines.append(f"DESCRIPTION:{_ical_escape(event.description)}")
        if event.url:
            lines.append(f"URL:{_ical_escape(event.url)}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
