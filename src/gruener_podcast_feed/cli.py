from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from .config import load_config
from .pipeline import (
    build_episode,
    fetch_newsletter_from_imap,
    load_newsletter_from_file,
    publish_assets,
    publish_feed,
    publish_global_feed,
)
from .publisher import publish_feed_asset, sync_to_gcs


def _default_run_id() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gruenpod", description="Gruener podcast pipeline")
    parser.add_argument("--env-file", default=None, help="Optional path to a .env file")

    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch-email", help="Fetch the latest matching newsletter via IMAP")
    fetch_parser.add_argument("--run-id", default=_default_run_id())

    eml_parser = subparsers.add_parser("build-from-eml", help="Build episode artifacts from a local .eml file")
    eml_parser.add_argument("eml_path")
    eml_parser.add_argument("--run-id", default=_default_run_id())

    run_parser = subparsers.add_parser("run", help="Fetch newsletter, build episode, and emit feed artifacts")
    run_parser.add_argument("--run-id", default=_default_run_id())

    subparsers.add_parser("publish-feed", help="Generate an aggregate RSS feed from all built episodes")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = load_config(args.env_file)

    if args.command == "fetch-email":
        newsletter, run_paths = fetch_newsletter_from_imap(config, args.run_id)
        print(f"Fetched newsletter '{newsletter.subject}' into {run_paths.root}")
        return

    if args.command == "build-from-eml":
        newsletter, run_paths = load_newsletter_from_file(config, args.run_id, Path(args.eml_path))
        episode = build_episode(config, newsletter, run_paths)
        publish_feed(config, episode, run_paths)
        published_episode, public_feed_path = publish_assets(config, episode, run_paths)
        sync_to_gcs(config)
        print(f"Built episode '{published_episode.title}' into {run_paths.root}; public feed at {public_feed_path}")
        return

    if args.command == "run":
        newsletter, run_paths = fetch_newsletter_from_imap(config, args.run_id)
        episode = build_episode(config, newsletter, run_paths)
        publish_feed(config, episode, run_paths)
        published_episode, public_feed_path = publish_assets(config, episode, run_paths)
        sync_to_gcs(config)
        print(f"Built and published episode '{published_episode.title}' into {run_paths.root}; public feed at {public_feed_path}")
        return

    if args.command == "publish-feed":
        output_path = publish_global_feed(config)
        public_feed_path = publish_feed_asset(config, output_path)
        sync_to_gcs(config)
        print(f"Published aggregate feed to {output_path}; public feed at {public_feed_path}")
        return

    raise SystemExit(f"Unsupported command: {args.command}")
