from __future__ import annotations

import json
import shutil
from pathlib import Path
from .config import AppConfig
from .pipeline import publish_global_feed
from .publisher import publish_feed_asset


def delete_episode_interactive(config: AppConfig) -> None:
    # 1. Gather all episodes
    episodes_meta = []
    for episode_json in config.runs_dir.glob("*/episode.json"):
        try:
            with open(episode_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                episodes_meta.append({
                    "path": episode_json.parent,
                    "title": data.get("title", "Unknown"),
                    "date": data.get("generated_at", "Unknown"),
                    "audio": data.get("audio_file")
                })
        except Exception:
            continue

    # Sort by date descending
    episodes_meta.sort(key=lambda x: x["date"], reverse=True)
    
    if not episodes_meta:
        print("No episodes found to delete.")
        return

    # 2. Show last 10
    print("\nLast 10 episodes:")
    to_show = episodes_meta[:10]
    for i, meta in enumerate(to_show):
        print(f"[{i}] {meta['date']} - {meta['title']}")

    # 3. Ask for ID
    try:
        choice = input("\nEnter the ID to delete (or press Enter to cancel): ").strip()
        if not choice:
            print("Cancelled.")
            return
        idx = int(choice)
        if idx < 0 or idx >= len(to_show):
            print("Invalid ID.")
            return
    except ValueError:
        print("Invalid input.")
        return

    target = to_show[idx]
    
    # 4. Perform Archiving
    archive_runs_dir = config.runs_dir / "archive"
    archive_runs_dir.mkdir(exist_ok=True)
    
    archive_public_dir = config.audio.public_output_dir / "archive"
    archive_public_dir.mkdir(exist_ok=True)

    print(f"Deleting: {target['title']}...")

    # Move public audio if it exists
    if target["audio"]:
        audio_path = Path(target["audio"])
        if audio_path.exists():
            shutil.move(str(audio_path), archive_public_dir / audio_path.name)
            print(f"  Moved audio to {archive_public_dir}")

    # Move run directory
    shutil.move(str(target["path"]), archive_runs_dir / target["path"].name)
    print(f"  Moved run directory to {archive_runs_dir}")

    # 5. Regenerate feed
    print("Regenerating feed...")
    feed_path = publish_global_feed(config)
    publish_feed_asset(config, feed_path)
    print("Done. Feed updated.")
