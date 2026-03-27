from __future__ import annotations

import base64
from pathlib import Path
import wave

try:
    from google import genai
    from google.genai import types
except ModuleNotFoundError:  # pragma: no cover - optional during bootstrap
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]


class SpeechClient:
    def synthesize_dialogue(self, dialogue: list[tuple[str, str]], voices: dict[str, str], model: str, output_path: Path) -> bytes:
        raise NotImplementedError


class GoogleTextToSpeechClient(SpeechClient):
    def __init__(self, api_key: str) -> None:
        if genai is None or types is None:
            raise RuntimeError("The 'google-genai' package is required for Google AI Studio voice generation")
        self._client = genai.Client(api_key=api_key)

    def synthesize_dialogue(self, dialogue: list[tuple[str, str]], voices: dict[str, str], model: str, output_path: Path) -> bytes:
        speaker_voice_configs = [
            types.SpeakerVoiceConfig(
                speaker=speaker,
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                ),
            )
            for speaker, voice in voices.items()
        ]
        response = self._client.models.generate_content(
            model=model,
            contents=_build_multi_speaker_prompt(dialogue),
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                        speaker_voice_configs=speaker_voice_configs
                    )
                ),
            ),
        )
        audio_bytes = _extract_audio_bytes(response)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        _write_wave_file(output_path, audio_bytes)
        return audio_bytes


def _write_wave_file(path: Path, pcm_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2) -> None:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(sample_width)
        handle.setframerate(rate)
        handle.writeframes(pcm_data)


def _extract_audio_bytes(response: object) -> bytes:
    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        raise RuntimeError("Google AI Studio TTS returned no candidates")

    content = getattr(candidates[0], "content", None)
    parts = getattr(content, "parts", None) or []
    if not parts:
        raise RuntimeError("Google AI Studio TTS returned no audio parts")

    inline_data = getattr(parts[0], "inline_data", None)
    data = getattr(inline_data, "data", None)
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return base64.b64decode(data)
    raise RuntimeError("Google AI Studio TTS response did not contain inline audio data")


def _build_multi_speaker_prompt(dialogue: list[tuple[str, str]]) -> str:
    lines = ["TTS the following conversation exactly as written:"]
    lines.extend(f"{speaker}: {text}" for speaker, text in dialogue)
    return "\n".join(lines)
