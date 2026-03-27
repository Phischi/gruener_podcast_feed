from __future__ import annotations

from pathlib import Path
from collections import Counter

try:
    from pydub import AudioSegment
except ModuleNotFoundError:  # pragma: no cover - optional during bootstrap
    AudioSegment = None  # type: ignore[assignment]

from .config import AudioConfig
from .models import DialogueTurn
from .speech import SpeechClient


def render_dialogue_to_mp3(
    speech_client: SpeechClient,
    dialogue: list[DialogueTurn],
    output_path: Path,
    config: AudioConfig,
) -> Path:
    if AudioSegment is None:
        raise RuntimeError("The 'pydub' package is required for audio rendering")

    normalized_dialogue, speaker_voices = _prepare_multi_speaker_dialogue(dialogue, config)
    wav_path = output_path.with_suffix(".wav")
    speech_client.synthesize_dialogue(
        dialogue=normalized_dialogue,
        voices=speaker_voices,
        model=config.tts_model,
        output_path=wav_path,
    )
    combined_audio = AudioSegment.from_file(wav_path, format="wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined_audio.export(output_path, format="mp3")
    return output_path


def _prepare_multi_speaker_dialogue(
    dialogue: list[DialogueTurn],
    config: AudioConfig,
) -> tuple[list[tuple[str, str]], dict[str, str]]:
    speaker_counts = Counter(turn.speaker for turn in dialogue if turn.speaker != "Narrator")
    primary_speakers = [speaker for speaker, _count in speaker_counts.most_common(2)]
    if not primary_speakers:
        primary_speakers = ["Pia", "Nico"]
    elif len(primary_speakers) == 1:
        fallback = "Nico" if primary_speakers[0] == "Pia" else "Pia"
        primary_speakers.append(fallback)

    normalized_dialogue: list[tuple[str, str]] = []
    last_non_narrator = primary_speakers[0]

    for turn in dialogue:
        speaker = turn.speaker
        if speaker == "Narrator" or speaker not in primary_speakers:
            speaker = last_non_narrator
        else:
            last_non_narrator = speaker
        normalized_dialogue.append((speaker, turn.text))

    speaker_voices = {
        speaker: config.voices.get(speaker, config.voices["Narrator"])
        for speaker in primary_speakers
    }
    return normalized_dialogue, speaker_voices
