from __future__ import annotations

from pathlib import Path

try:
    from pydub import AudioSegment
except ModuleNotFoundError:  # pragma: no cover - optional during bootstrap
    AudioSegment = None  # type: ignore[assignment]

from .config import AudioConfig
from .llm import LLMClient
from .models import DialogueTurn


def render_dialogue_to_mp3(
    llm: LLMClient,
    dialogue: list[DialogueTurn],
    output_path: Path,
    temp_dir: Path,
    config: AudioConfig,
) -> Path:
    if AudioSegment is None:
        raise RuntimeError("The 'pydub' package is required for audio rendering")

    temp_dir.mkdir(parents=True, exist_ok=True)
    combined_audio = AudioSegment.empty()
    previous_speaker: str | None = None

    for index, turn in enumerate(dialogue):
        voice = config.voices.get(turn.speaker, config.voices["Narrator"])
        segment_path = temp_dir / f"segment_{index:03d}_{turn.speaker.lower()}.mp3"
        llm.synthesize_speech(
            text=turn.text,
            voice=voice,
            model=config.tts_model,
            output_path=segment_path,
        )
        segment = AudioSegment.from_file(segment_path, format="mp3")
        if len(combined_audio) > 0:
            pause_duration = (
                config.pause_same_speaker_ms
                if previous_speaker == turn.speaker
                else config.pause_different_speaker_ms
            )
            combined_audio += AudioSegment.silent(duration=pause_duration)
        combined_audio += segment
        previous_speaker = turn.speaker

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined_audio.export(output_path, format="mp3")
    return output_path
