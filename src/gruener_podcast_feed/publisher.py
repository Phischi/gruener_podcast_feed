from __future__ import annotations

from pathlib import Path
import shutil
import sys

try:
    from google.cloud import storage
except ImportError:
    storage = None  # type: ignore

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


def sync_to_gcs(config: AppConfig) -> None:
    if not config.gcs_bucket_name:
        return

    if storage is None:
        print("Warning: GCS bucket configured but 'google-cloud-storage' not installed. Skipping upload.", file=sys.stderr)
        return

    print(f"Syncing assets to GCS bucket: {config.gcs_bucket_name}")
    client = storage.Client()
    bucket = client.bucket(config.gcs_bucket_name)

    base_dir = config.audio.public_output_dir
    if not base_dir.exists():
        print(f"Warning: Public output directory {base_dir} does not exist. Nothing to sync.", file=sys.stderr)
        return

    for file_path in base_dir.rglob("*"):
        if not file_path.is_file():
            continue

        relative_path = file_path.relative_to(base_dir)
        blob_path = str(relative_path).replace("\\", "/")
        blob = bucket.blob(blob_path)

        content_type = "application/octet-stream"
        if file_path.suffix == ".mp3":
            content_type = "audio/mpeg"
        elif file_path.suffix == ".xml":
            content_type = "application/rss+xml"
        elif file_path.suffix == ".json":
            content_type = "application/json"
        elif file_path.suffix == ".ics":
            content_type = "text/calendar"

        blob.cache_control = "public, max-age=3600"
        blob.upload_from_filename(str(file_path), content_type=content_type)
        print(f"  Uploaded: {blob_path} ({content_type})")
