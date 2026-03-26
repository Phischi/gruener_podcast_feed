from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .utils import ensure_dir


@dataclass(slots=True)
class RunPaths:
    root: Path
    raw_email_path: Path
    newsletter_json_path: Path
    script_text_path: Path
    episode_json_path: Path
    events_json_path: Path
    events_ics_path: Path
    audio_dir: Path
    final_audio_path: Path
    feed_xml_path: Path


def build_run_paths(runs_dir: Path, run_id: str) -> RunPaths:
    root = ensure_dir(runs_dir / run_id)
    feed_dir = ensure_dir(root / "feed")
    audio_dir = ensure_dir(root / "audio")
    return RunPaths(
        root=root,
        raw_email_path=root / "raw_email.eml",
        newsletter_json_path=root / "newsletter.json",
        script_text_path=root / "script.txt",
        episode_json_path=root / "episode.json",
        events_json_path=root / "events.json",
        events_ics_path=root / "events.ics",
        audio_dir=audio_dir,
        final_audio_path=audio_dir / "episode.mp3",
        feed_xml_path=feed_dir / "feed.xml",
    )
