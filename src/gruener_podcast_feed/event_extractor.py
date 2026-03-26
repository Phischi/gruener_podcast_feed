from __future__ import annotations

import sys

from .llm import LLMClient
from .models import Event


def extract_events(source_text: str, llm: LLMClient | None = None) -> list[Event]:
    if llm is not None:
        try:
            return llm.extract_events(source_text)
        except Exception as exc:
            print(f"Warning: event extraction failed, continuing without events: {exc}", file=sys.stderr)
            return []
    return []
