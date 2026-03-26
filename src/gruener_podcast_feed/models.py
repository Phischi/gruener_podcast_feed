from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Newsletter:
    subject: str
    sender: str
    received_at: str
    body_text: str
    message_id: str | None = None
    source_path: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class DialogueTurn:
    speaker: str
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class Event:
    title: str
    start_at: str | None = None
    end_at: str | None = None
    location: str | None = None
    description: str | None = None
    url: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class Episode:
    slug: str
    title: str
    summary: str
    newsletter_subject: str
    newsletter_sender: str
    generated_at: str
    script_text: str
    dialogue: list[DialogueTurn] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    audio_file: str | None = None
    audio_url: str | None = None
    rss_item_url: str | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["dialogue"] = [turn.to_dict() for turn in self.dialogue]
        data["events"] = [event.to_dict() for event in self.events]
        return data


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
