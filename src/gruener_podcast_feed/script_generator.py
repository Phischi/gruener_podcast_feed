from __future__ import annotations

from email.utils import parsedate_to_datetime
import re

from .llm import LLMClient
from .models import DialogueTurn, Newsletter

SPEAKER_LINE_RE = re.compile(
    r"^(?:\*\*)?\s*(Pia(?:\s+Plastikfrei)?|Nico(?:\s+Nachhaltig)?|Narrator)\s*:\s*(?:\*\*)?\s*(.+)$",
    flags=re.IGNORECASE,
)


def generate_script(newsletter: Newsletter, llm: LLMClient | None = None) -> str:
    if llm is not None:
        return sanitize_script(llm.generate_script(newsletter))
    return sanitize_script(build_fallback_script(newsletter))


def build_fallback_script(newsletter: Newsletter) -> str:
    summary = newsletter.body_text[:1800].strip()
    spoken_date = _format_spoken_date(newsletter.received_at)
    return (
        f"Pia: Willkommen zu einer neuen Folge von GrünGeschnackt vom {spoken_date}.\n\n"
        f'Nico: Heute schauen wir auf den Newsletter "{newsletter.subject}".\n\n'
        f'Nico: Hier kommt die kompakte Zusammenfassung. {summary}\n\n'
        "Pia: Wir ordnen die wichtigsten Punkte, Termine und Mitmachmöglichkeiten für euch ein.\n\n"
        "Nico: Damit habt ihr eine belastbare Grundlage, bis die LLM-gestützte Skriptgenerierung aktiviert ist."
    )


def parse_dialogue(script_text: str) -> list[DialogueTurn]:
    dialogue: list[DialogueTurn] = []
    for raw_line in script_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if _is_heading(line):
            continue
        match = SPEAKER_LINE_RE.match(line)
        if match:
            speaker = _normalize_speaker(match.group(1))
            dialogue.append(DialogueTurn(speaker=speaker, text=match.group(2).strip()))
        else:
            dialogue.append(DialogueTurn(speaker="Narrator", text=line))
    return dialogue


def sanitize_script(script_text: str) -> str:
    cleaned_lines: list[str] = []
    for raw_line in script_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if _is_heading(line):
            continue
        match = SPEAKER_LINE_RE.match(line)
        if match:
            line = f"{_normalize_speaker(match.group(1))}: {match.group(2).strip()}"
        cleaned_lines.append(line)
    return "\n\n".join(cleaned_lines)


def _is_heading(line: str) -> bool:
    return bool(re.match(r"^#{1,6}\s+", line))


def _normalize_speaker(raw: str) -> str:
    normalized = raw.strip().lower()
    if normalized.startswith("pia"):
        return "Pia"
    if normalized.startswith("nico"):
        return "Nico"
    return "Narrator"


def _format_spoken_date(value: str) -> str:
    if not value:
        return "heute"
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError, OverflowError):
        return value
    return f"{parsed.day}.{parsed.month}.{parsed.year}"
