from __future__ import annotations

from pathlib import Path
import shutil

from .config import AppConfig
from .models import Episode
from .paths import RunPaths
from .utils import ensure_dir, write_json


def publish_audio_asset(config: AppConfig, episode: Episode, run_paths: RunPaths) -> Episode:
    if not run_paths.final_audio_path.exists():
        return episode

    public_audio_dir = ensure_dir(config.audio.public_output_dir / config.audio.public_audio_path)
    public_audio_path = public_audio_dir / f"{episode.slug}.mp3"
    shutil.copy2(run_paths.final_audio_path, public_audio_path)

    episode.audio_file = str(public_audio_path)
    episode.audio_url = f"{config.podcast.base_url}/{config.audio.public_audio_path}/{episode.slug}.mp3"
    episode.rss_item_url = f"{config.podcast.base_url}/episodes/{episode.slug}.html"
    write_json(run_paths.episode_json_path, episode.to_dict())
    return episode


def publish_feed_asset(config: AppConfig, feed_path: Path) -> Path:
    config.audio.public_output_dir.mkdir(parents=True, exist_ok=True)
    public_feed_path = config.audio.public_output_dir / "feed.xml"
    shutil.copy2(feed_path, public_feed_path)
    return public_feed_path
