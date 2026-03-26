# Gruener Podcast Feed

This repository is being reworked from a notebook-heavy proof of concept into a reproducible newsletter-to-podcast pipeline.

The target workflow is:

1. Fetch the latest newsletter email from IMAP.
2. Normalize the email into a structured newsletter artifact.
3. Generate a spoken podcast script.
4. Extract events into machine-readable JSON and `.ics`.
5. Render audio.
6. Publish a podcast feed over RSS.
7. Trigger the flow automatically from n8n or another scheduler.

The new Python package and CLI are now in place for ingestion, artifact generation, calendar export, audio rendering, and RSS generation. The remaining work is mainly around hardened storage uploads, richer feed metadata, and tests.

## Current State

There are now two layers in the repository:

- legacy prototype assets:
  [gruen_geschnackt_poc.ipynb](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/gruen_geschnackt_poc.ipynb),
  [podcast_voice_generator.ipynb](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/podcast_voice_generator.ipynb),
  and the older Go connector under [email-connector/](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/email-connector)
- new production-oriented package:
  [src/gruener_podcast_feed/](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/src/gruener_podcast_feed)

The redesign plan is documented in [docs/rebuild_plan.md](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/docs/rebuild_plan.md).

## New Architecture

The new Python pipeline is organized around deterministic run artifacts under `runs/<run-id>/`.

Each run can produce:

- `raw_email.eml`
- `newsletter.json`
- `script.txt`
- `episode.json`
- `events.json`
- `events.ics`
- `audio/episode.mp3`
- `feed/feed.xml`

An aggregate RSS file can also be generated at `runs/feed.xml`, and a public copy can be published into `PUBLIC_OUTPUT_DIR`.

## Repository Structure

- [pyproject.toml](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/pyproject.toml): package metadata and CLI entry point
- [.env.example](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/.env.example): example runtime configuration
- [src/gruener_podcast_feed/cli.py](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/src/gruener_podcast_feed/cli.py): command-line entry point
- [src/gruener_podcast_feed/pipeline.py](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/src/gruener_podcast_feed/pipeline.py): orchestration for ingestion, episode building, and feed publishing
- [src/gruener_podcast_feed/imap_client.py](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/src/gruener_podcast_feed/imap_client.py): IMAP newsletter fetching
- [src/gruener_podcast_feed/newsletter.py](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/src/gruener_podcast_feed/newsletter.py): email parsing and normalization
- [src/gruener_podcast_feed/script_generator.py](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/src/gruener_podcast_feed/script_generator.py): script generation and dialogue parsing
- [src/gruener_podcast_feed/event_extractor.py](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/src/gruener_podcast_feed/event_extractor.py): event extraction entry point
- [src/gruener_podcast_feed/ical_writer.py](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/src/gruener_podcast_feed/ical_writer.py): calendar file generation
- [src/gruener_podcast_feed/feed/rss_writer.py](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/src/gruener_podcast_feed/feed/rss_writer.py): RSS feed generation
- [docs/operations.md](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/docs/operations.md): secure email, RSS hosting, and n8n integration guidance

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Optional legacy notebook dependencies still live in [requirements.txt](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/requirements.txt).

## Configuration

Copy [.env.example](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/.env.example) into a runtime `.env` file and fill in the values you actually use.

Minimum practical variables:

```env
OPENAI_API_KEY=...
NEWSLETTER_IMAP_HOST=imap.example.com
NEWSLETTER_IMAP_PORT=993
NEWSLETTER_IMAP_USERNAME=podcast-newsletter@example.com
NEWSLETTER_IMAP_PASSWORD=app-password
PODCAST_BASE_URL=https://podcast.example.com
PODCAST_FEED_URL=https://podcast.example.com/feed.xml
PODCAST_SITE_URL=https://podcast.example.com
```

## CLI Usage

Fetch the latest matching email only:

```bash
gruenpod fetch-email --env-file .env
```

Build an episode from a local `.eml` file:

```bash
gruenpod build-from-eml sample.eml --env-file .env
```

Run the end-to-end pipeline currently implemented:

```bash
gruenpod run --env-file .env
```

Regenerate the aggregate RSS feed from saved episode artifacts:

```bash
gruenpod publish-feed --env-file .env
```

If `OPENAI_API_KEY` is missing, the pipeline falls back to a minimal deterministic script mode instead of live LLM generation and skips TTS rendering.

## Secure Email, RSS, And n8n

Operational guidance now lives in [docs/operations.md](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/docs/operations.md), including:

- how to connect a dedicated IMAP mailbox securely
- how to host a public RSS feed and MP3 files
- how to call the CLI on a schedule from n8n

## Remaining Gaps

The redesign is started, not finished. Still missing:

- object storage uploads beyond local public directory publishing
- richer podcast XML beyond the first iTunes tags
- automated tests
- migration away from the old Go connector and notebooks once parity is reached
