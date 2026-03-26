# Gruener Podcast Feed

Gruener Podcast Feed turns the latest newsletter email into a local podcast episode with structured intermediate artifacts.

The default workflow is:

1. Fetch the latest newsletter email from IMAP.
2. Normalize the email into a structured newsletter artifact.
3. Generate a spoken podcast script.
4. Extract events into machine-readable JSON and `.ics`.
5. Render audio.
6. Publish a podcast feed over RSS.
7. Publish the finished files locally and optionally hand them off to automation.

## New Architecture

The Python package is organized around deterministic run artifacts under `runs/<run-id>/`.

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

## Starting The App

For the normal end-to-end run, use the repository script:

```bash
./start.sh
```

The script runs `.venv/bin/gruenpod --env-file .env run` and fails early if the virtual environment or `.env` file is missing.

## CLI Usage

Use the CLI directly when you want a narrower step:

Fetch the latest matching email only:

```bash
gruenpod --env-file .env fetch-email
```

Build an episode from a local `.eml` file:

```bash
gruenpod --env-file .env build-from-eml sample.eml
```

Run the end-to-end pipeline currently implemented:

```bash
gruenpod --env-file .env run
```

Regenerate the aggregate RSS feed from saved episode artifacts:

```bash
gruenpod --env-file .env publish-feed
```

If `OPENAI_API_KEY` is missing, the pipeline falls back to a minimal deterministic script mode instead of live LLM generation and skips TTS rendering.

## Secure Email, RSS, And n8n

Operational guidance now lives in [docs/operations.md](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/docs/operations.md), including:

- how to connect a dedicated IMAP mailbox securely
- how to host a public RSS feed and MP3 files
- how to call the CLI on a schedule from n8n

## Remaining Gaps

Still missing:

- object storage uploads beyond local public directory publishing
- richer podcast XML beyond the first iTunes tags
- automated tests
