from __future__ import annotations

from datetime import datetime
import json
import re

try:
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover - optional during bootstrap
    OpenAI = None  # type: ignore[assignment]

from .models import Event, Newsletter
from .prompts import EVENTS_SYSTEM_PROMPT, SCRIPT_SYSTEM_PROMPT


class LLMClient:
    def __init__(self, api_key: str) -> None:
        if OpenAI is None:
            raise RuntimeError("The 'openai' package is required for LLM-backed generation")
        self._client = OpenAI(api_key=api_key)

    def generate_script(self, newsletter: Newsletter, model: str = "gpt-4o-mini") -> str:
        prompt_input = _build_script_input(newsletter)
        follow_up = ""
        script = ""
        for _ in range(2):
            response = self._client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": [{"type": "input_text", "text": SCRIPT_SYSTEM_PROMPT}]},
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt_input + follow_up}],
                    },
                ],
            )
            script = response.output_text.strip()
            if "[Datum]" not in script and "[aktuelles Datum]" not in script:
                return script
            follow_up = (
                "\n\nDein letzter Entwurf enthielt Platzhalter wie [Datum] oder [aktuelles Datum]. "
                "Ersetze solche Platzhalter durch konkrete Daten aus dem Newsletter oder nenne kein Datum, "
                "wenn keins im Newsletter steht."
            )
        return script

    def extract_events(self, source_text: str, model: str = "gpt-4o-mini") -> list[Event]:
        response = self._client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": EVENTS_SYSTEM_PROMPT}]},
                {"role": "user", "content": [{"type": "input_text", "text": source_text}]},
            ],
        )
        payload = json.loads(_extract_json_object(response.output_text))
        return [Event(**item) for item in payload.get("events", [])]

def _extract_json_object(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        raise ValueError("Event extraction returned an empty response")

    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, flags=re.DOTALL)
    if fence_match:
        return fence_match.group(1)

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end >= start:
        return stripped[start : end + 1]

    raise ValueError("Event extraction response did not contain a JSON object")


def _build_script_input(newsletter: Newsletter) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return (
        f"Heutiges Datum: {today}\n"
        f"Newsletter-Betreff: {newsletter.subject}\n"
        f"Newsletter-Absender: {newsletter.sender}\n"
        f"Newsletter-Eingangsdatum: {newsletter.received_at}\n\n"
        "Newsletter-Inhalt:\n"
        f"{newsletter.body_text}"
    )
