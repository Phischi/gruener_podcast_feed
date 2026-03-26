# Rebuild Plan

## Goal

Replace the current prototype with one reproducible pipeline that can ingest a newsletter email, generate structured episode artifacts, publish an RSS feed, and later plug in audio rendering and automation cleanly.

## Implementation Phases

### Phase 1. Production Skeleton

- Create a Python package under `src/gruener_podcast_feed/`
- Add `pyproject.toml` and a CLI entry point
- Add `.env.example` for all operational settings
- Introduce deterministic run directories under `runs/<run-id>/`
- Define typed models for newsletters, dialogue turns, events, and episodes

Status: implemented

### Phase 2. Input Ingestion

- Replace the ad hoc Go-only IMAP workflow with a Python IMAP client
- Support both IMAP fetches and local `.eml` files for deterministic testing
- Store the raw email plus normalized newsletter JSON as first-class artifacts

Status: implemented

### Phase 3. Content Generation

- Generate a podcast script from the normalized newsletter body
- Parse the spoken script into structured dialogue turns
- Extract events into machine-readable event objects
- Persist `script.txt`, `episode.json`, `events.json`, and `events.ics`

Status: implemented with a fallback mode when `OPENAI_API_KEY` is missing

### Phase 4. Feed Publishing

- Write RSS XML from built episode artifacts
- Support both per-run feed output and one aggregate feed at `runs/feed.xml`
- Keep audio URL support in the episode model so the feed can later become a real podcast feed

Status: implemented

### Phase 5. Audio Rendering

- Replace notebook-based TTS generation with a package module
- Generate one audio segment per dialogue turn
- Stitch segments with configurable pauses
- Upload the finished MP3 and write the public `audio_url` back to `episode.json`

Status: implemented for OpenAI TTS plus local public directory publishing

### Phase 6. Automation And Operations

- Document secure IMAP access
- Document RSS hosting and public file layout
- Provide an n8n flow design for scheduled execution
- Add tests and CI once the audio stage is stable

Status: documented in `docs/operations.md`

## Exit Criteria For The Redesign

- One CLI command can build an episode from IMAP or a local `.eml`
- The pipeline writes traceable intermediate artifacts
- Event data is no longer hidden inside freeform prompt text only
- A valid `.ics` file is emitted
- A public RSS file can be regenerated from stored episode artifacts
