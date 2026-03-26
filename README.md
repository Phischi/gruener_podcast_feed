# Gruener Podcast Feed

Gruener Podcast Feed turns the latest newsletter email into a local podcast episode and stores each processing step as a reproducible run artifact.

The supported workflow is:

1. Fetch the latest newsletter email from IMAP.
2. Normalize the email into a structured newsletter artifact.
3. Generate a spoken podcast script.
4. Extract events into machine-readable JSON and `.ics`.
5. Render audio.
6. Publish the finished files locally under `public/`.
7. Optionally regenerate an aggregate RSS feed from saved runs.

## Repository Layout

- `src/gruener_podcast_feed/`: package source code
- `docs/`: operational notes and redesign background
- `.env.example`: runtime configuration template
- `start.sh`: default entry point for the end-to-end run

Every run writes deterministic output under `runs/<run-id>/`:

- `raw_email.eml`
- `newsletter.json`
- `script.txt`
- `episode.json`
- `events.json`
- `events.ics`
- `audio/episode.mp3`
- `feed/feed.xml`

The latest playable MP3 is also copied to `public/audio/`, and the current feed to `public/feed.xml`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

You also need:

- `ffmpeg` and `ffprobe` available on `PATH`
- an IMAP mailbox for the newsletter
- an `OPENAI_API_KEY` if you want live script generation and TTS audio

Copy `.env.example` to `.env` and fill in the values you actually use. The minimum practical configuration is:

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

## Running The Pipeline

For the normal end-to-end run, use:

```bash
./start.sh
```

This script runs `.venv/bin/gruenpod --env-file .env run` and fails early if the virtual environment or `.env` file is missing.

Useful direct CLI commands:

- `gruenpod --env-file .env fetch-email`
- `gruenpod --env-file .env build-from-eml sample.eml`
- `gruenpod --env-file .env run`
- `gruenpod --env-file .env publish-feed`

If `OPENAI_API_KEY` is missing, the pipeline falls back to a minimal deterministic script mode instead of live LLM generation and skips TTS rendering.

## Outputs

After a successful run, the most useful files are:

- `runs/<run-id>/audio/episode.mp3`
- `runs/<run-id>/script.txt`
- `runs/<run-id>/events.ics`
- `public/audio/<episode-slug>.mp3`
- `public/feed.xml`

## Notes

- Operational guidance for IMAP, hosting, and automation lives in `docs/operations.md`.
- The redesign background and intended end state are documented in `docs/rebuild_plan.md`.
- The repository still lacks automated tests and richer podcast-specific XML metadata.
