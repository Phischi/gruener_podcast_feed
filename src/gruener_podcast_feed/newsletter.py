from __future__ import annotations

from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path
import re

from .models import Newsletter


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def text(self) -> str:
        return " ".join(self._parts)


def strip_html(value: str) -> str:
    parser = _HTMLStripper()
    parser.feed(value)
    return normalize_whitespace(parser.text())


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_body_text(message: EmailMessage) -> str:
    if message.is_multipart():
        plain_parts: list[str] = []
        html_parts: list[str] = []
        for part in message.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get_content_disposition() == "attachment":
                continue
            content_type = part.get_content_type()
            payload = part.get_content()
            if not isinstance(payload, str):
                continue
            if content_type == "text/plain":
                plain_parts.append(normalize_whitespace(payload))
            elif content_type == "text/html":
                html_parts.append(strip_html(payload))
        if plain_parts:
            return normalize_whitespace(" ".join(plain_parts))
        return normalize_whitespace(" ".join(html_parts))

    payload = message.get_content()
    if not isinstance(payload, str):
        return ""
    if message.get_content_type() == "text/html":
        return strip_html(payload)
    return normalize_whitespace(payload)


def newsletter_from_message(message: EmailMessage, source_path: Path | None = None) -> Newsletter:
    return Newsletter(
        subject=message.get("Subject", "").strip(),
        sender=message.get("From", "").strip(),
        received_at=message.get("Date", "").strip(),
        body_text=extract_body_text(message),
        message_id=message.get("Message-ID"),
        source_path=str(source_path) if source_path else None,
    )


def load_newsletter_from_eml(path: Path) -> Newsletter:
    message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    return newsletter_from_message(message, source_path=path)
