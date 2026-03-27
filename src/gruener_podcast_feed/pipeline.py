from __future__ import annotations

from pathlib import Path
import json
import sys

from .audio import render_dialogue_to_mp3
from .config import AppConfig
from .event_extractor import extract_events
from .feed.rss_writer import write_feed
from .ical_writer import write_ical
from .imap_client import fetch_latest_matching_newsletter
from .llm import LLMClient
from .models import Episode, Newsletter, now_iso
from .newsletter import load_newsletter_from_eml
from .paths import RunPaths, build_run_paths
from .publisher import publish_audio_asset, publish_feed_asset
from .script_generator import generate_script, parse_dialogue
from .speech import GoogleTextToSpeechClient
from .utils import slugify, write_json


def _build_llm(config: AppConfig) -> LLMClient | None:
    if not config.openai_api_key:
        return None
    return LLMClient(config.openai_api_key)


def _build_speech_client(config: AppConfig) -> GoogleTextToSpeechClient | None:
    if not config.gemini_api_key:
        return None
    try:
        return GoogleTextToSpeechClient(config.gemini_api_key)
    except RuntimeError as exc:
        print(f"Warning: audio rendering disabled, continuing without TTS: {exc}", file=sys.stderr)
        return None


def fetch_newsletter_from_imap(config: AppConfig, run_id: str) -> tuple[Newsletter, RunPaths]:
    run_paths = build_run_paths(config.runs_dir, run_id)
    newsletter, raw_email = fetch_latest_matching_newsletter(config.imap)
    run_paths.raw_email_path.write_bytes(raw_email)
    write_json(run_paths.newsletter_json_path, newsletter.to_dict())
    return newsletter, run_paths


def load_newsletter_from_file(config: AppConfig, run_id: str, eml_path: Path) -> tuple[Newsletter, RunPaths]:
    run_paths = build_run_paths(config.runs_dir, run_id)
    raw_email = eml_path.read_bytes()
    run_paths.raw_email_path.write_bytes(raw_email)
    newsletter = load_newsletter_from_eml(eml_path)
    write_json(run_paths.newsletter_json_path, newsletter.to_dict())
    return newsletter, run_paths


def build_episode(config: AppConfig, newsletter: Newsletter, run_paths: RunPaths) -> Episode:
    llm = _build_llm(config)
    speech_client = _build_speech_client(config)
    script_text = generate_script(newsletter, llm=llm)
    dialogue = parse_dialogue(script_text)
    events = extract_events(script_text, llm=llm)

    summary = " ".join(segment.text for segment in dialogue[:3])[:400].strip()
    episode = Episode(
        slug=slugify(newsletter.subject),
        title=f"{config.podcast.name}: {newsletter.subject}",
        summary=summary,
        newsletter_subject=newsletter.subject,
        newsletter_sender=newsletter.sender,
        generated_at=now_iso(),
        script_text=script_text,
        dialogue=dialogue,
        events=events,
    )

    if speech_client is not None and dialogue:
        render_dialogue_to_mp3(
            speech_client=speech_client,
            dialogue=dialogue,
            output_path=run_paths.final_audio_path,
            config=config.audio,
        )
        episode.audio_file = str(run_paths.final_audio_path)

    run_paths.script_text_path.write_text(script_text + "\n", encoding="utf-8")
    write_json(run_paths.events_json_path, {"events": [event.to_dict() for event in events]})
    write_json(run_paths.episode_json_path, episode.to_dict())
    write_ical(events, run_paths.events_ics_path)
    return episode


def publish_feed(config: AppConfig, episode: Episode, run_paths: RunPaths) -> None:
    write_feed(config.podcast, [episode], run_paths.feed_xml_path)


def publish_global_feed(config: AppConfig) -> Path:
    episodes: list[Episode] = []
    if not config.runs_dir.exists():
        raise FileNotFoundError(f"Runs directory does not exist: {config.runs_dir}")

    for episode_json_path in sorted(config.runs_dir.glob("*/episode.json"), reverse=True):
        payload = json.loads(episode_json_path.read_text(encoding="utf-8"))
        episodes.append(
            Episode(
                slug=payload["slug"],
                title=payload["title"],
                summary=payload["summary"],
                newsletter_subject=payload["newsletter_subject"],
                newsletter_sender=payload["newsletter_sender"],
                generated_at=payload["generated_at"],
                script_text=payload["script_text"],
                dialogue=[],
                events=[],
                audio_file=payload.get("audio_file"),
                audio_url=payload.get("audio_url"),
                rss_item_url=payload.get("rss_item_url"),
            )
        )

    output_path = config.runs_dir / "feed.xml"
    write_feed(config.podcast, episodes, output_path)
    return output_path


def publish_assets(config: AppConfig, episode: Episode, run_paths: RunPaths) -> tuple[Episode, Path]:
    published_episode = publish_audio_asset(config, episode, run_paths)
    write_feed(config.podcast, [published_episode], run_paths.feed_xml_path)
    feed_path = publish_global_feed(config)
    public_feed_path = publish_feed_asset(config, feed_path)
    return published_episode, public_feed_path
