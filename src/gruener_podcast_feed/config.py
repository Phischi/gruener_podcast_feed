from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional during bootstrap
    def load_dotenv(_env_file: str | None = None) -> bool:
        return False


@dataclass(slots=True)
class ImapConfig:
    host: str
    port: int
    username: str
    password: str
    mailbox: str = "INBOX"
    subject_prefix: str = "[gn]"
    from_filter: str | None = None
    lookback_limit: int = 100


@dataclass(slots=True)
class PodcastConfig:
    name: str
    base_url: str
    feed_url: str
    site_url: str
    language: str = "de-DE"
    author: str = "Grüne Hamburg"
    owner_email: str = ""
    description: str = ""
    image_url: str | None = None
    category: str = "News"
    explicit: bool = False


@dataclass(slots=True)
class AudioConfig:
    tts_model: str
    voices: dict[str, str]
    pause_different_speaker_ms: int
    pause_same_speaker_ms: int
    public_output_dir: Path
    public_audio_path: str


@dataclass(slots=True)
class AppConfig:
    openai_api_key: str | None
    runs_dir: Path
    imap: ImapConfig
    podcast: PodcastConfig
    audio: AudioConfig


def _required(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def load_config(env_file: str | None = None) -> AppConfig:
    load_dotenv(env_file)

    runs_dir = Path(os.getenv("RUNS_DIR", "runs")).resolve()

    imap = ImapConfig(
        host=_required("NEWSLETTER_IMAP_HOST", "imap.example.com"),
        port=int(os.getenv("NEWSLETTER_IMAP_PORT", "993")),
        username=_required("NEWSLETTER_IMAP_USERNAME", "placeholder@example.com"),
        password=_required("NEWSLETTER_IMAP_PASSWORD", "placeholder-password"),
        mailbox=os.getenv("NEWSLETTER_IMAP_MAILBOX", "INBOX"),
        subject_prefix=os.getenv("NEWSLETTER_SUBJECT_PREFIX", "[gn]"),
        from_filter=os.getenv("NEWSLETTER_FROM_FILTER") or None,
        lookback_limit=int(os.getenv("NEWSLETTER_LOOKBACK_LIMIT", "100")),
    )

    podcast = PodcastConfig(
        name=os.getenv("PODCAST_NAME", "GrünGeschnackt"),
        base_url=os.getenv("PODCAST_BASE_URL", "https://podcast.example.com").rstrip("/"),
        feed_url=os.getenv("PODCAST_FEED_URL", "https://podcast.example.com/feed.xml"),
        site_url=os.getenv("PODCAST_SITE_URL", "https://podcast.example.com"),
        language=os.getenv("PODCAST_LANGUAGE", "de-DE"),
        author=os.getenv("PODCAST_AUTHOR", "Grüne Hamburg"),
        owner_email=os.getenv("PODCAST_OWNER_EMAIL", ""),
        description=os.getenv("PODCAST_DESCRIPTION", "Podcast built from the latest newsletter."),
        image_url=os.getenv("PODCAST_IMAGE_URL") or None,
        category=os.getenv("PODCAST_CATEGORY", "News"),
        explicit=os.getenv("PODCAST_EXPLICIT", "false").lower() == "true",
    )

    audio = AudioConfig(
        tts_model=os.getenv("TTS_MODEL", "gpt-4o-mini-tts"),
        voices={
            "Pia": os.getenv("TTS_VOICE_PIA", "nova"),
            "Nico": os.getenv("TTS_VOICE_NICO", "verse"),
            "Narrator": os.getenv("TTS_VOICE_NARRATOR", "alloy"),
        },
        pause_different_speaker_ms=int(os.getenv("TTS_PAUSE_DIFFERENT_SPEAKER_MS", "450")),
        pause_same_speaker_ms=int(os.getenv("TTS_PAUSE_SAME_SPEAKER_MS", "200")),
        public_output_dir=Path(os.getenv("PUBLIC_OUTPUT_DIR", "public")).resolve(),
        public_audio_path=os.getenv("PUBLIC_AUDIO_PATH", "audio").strip("/"),
    )

    return AppConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        runs_dir=runs_dir,
        imap=imap,
        podcast=podcast,
        audio=audio,
    )
