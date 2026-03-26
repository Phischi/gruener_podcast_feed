# Operations Guide

## Secure Email Integration

Use a dedicated mailbox or alias for newsletter ingestion instead of your personal inbox. The pipeline only needs read access to one mailbox, so keep the blast radius small.

Recommended setup:

1. Create a dedicated mailbox such as `podcast-newsletter@...` or a filtered folder in your mail provider.
2. Enable IMAP access only for that account or mailbox.
3. If your provider supports it, create an app password instead of reusing your normal login password.
4. Store credentials in environment variables or an n8n credential, not in notebooks or committed files.
5. Restrict the pipeline to a dedicated mailbox like `INBOX/Podcast` and a sender filter.
6. Rotate the app password if the automation host changes or you suspect exposure.

Suggested environment variables:

```env
NEWSLETTER_IMAP_HOST=imap.example.com
NEWSLETTER_IMAP_PORT=993
NEWSLETTER_IMAP_USERNAME=podcast-newsletter@example.com
NEWSLETTER_IMAP_PASSWORD=app-password-here
NEWSLETTER_IMAP_MAILBOX=INBOX/Podcast
NEWSLETTER_FROM_FILTER=newsletter@example.com
NEWSLETTER_SUBJECT_PREFIX=[gn]
```

If you host this on a server:

- keep the `.env` outside the web root
- limit filesystem permissions to the service user
- do not log raw credentials
- prefer secrets injection from the process manager or container runtime

## RSS / Podcast Feed Integration

The code now emits RSS XML from episode artifacts. To make that accessible to podcast apps, you need public hosting for two things:

- the RSS file itself
- the MP3 file referenced by each `<enclosure>`

Recommended layout:

- `https://podcast.example.com/feed.xml`
- `https://podcast.example.com/audio/<episode>.mp3`
- `https://podcast.example.com/episodes/<episode>.html` optional landing pages

Practical setup options:

1. Static hosting on S3 + CloudFront, R2, Netlify, or a small VPS.
2. A web server such as Nginx serving the `runs/` export directory.
3. An object storage bucket for audio and feed assets, with the pipeline uploading artifacts after each run.

The current implementation already supports a simple local publishing model:

- rendered episode audio is copied to `PUBLIC_OUTPUT_DIR/<PUBLIC_AUDIO_PATH>/<episode>.mp3`
- the aggregate feed is copied to `PUBLIC_OUTPUT_DIR/feed.xml`

That makes it easy to put Nginx, Caddy, or a static file host in front of one directory first, then replace that with S3 or R2 later.

For a real podcast feed:

- set `PODCAST_BASE_URL`, `PODCAST_SITE_URL`, and `PODCAST_FEED_URL` to public HTTPS URLs
- upload the generated MP3 to your public storage
- write the public file URL back into `episode.json` as `audio_url`
- rerun `gruenpod publish-feed`

The current RSS writer is a clean base, but for broad podcast app compatibility you will likely want to add iTunes namespace tags next:

- `itunes:author`
- `itunes:summary`
- `itunes:owner`
- `itunes:explicit`
- `itunes:image`
- `itunes:category`

## n8n Integration

The cleanest production model is to let n8n orchestrate the pipeline, while the Python app does the real work.

Recommended n8n flow:

1. `Schedule Trigger`
   Run every morning or shortly after the newsletter is expected.

2. `Execute Command`
   Run:

   ```bash
   cd /path/to/gruener_podcast_feed
   . .venv/bin/activate
   gruenpod run --env-file /secure/path/gruenpod.env
   ```

3. `Execute Command` or `Code`
   If you outgrow the local `PUBLIC_OUTPUT_DIR` publishing model, upload the generated MP3 and feed artifacts to your hosting target.

4. `Execute Command`
   Regenerate the aggregate feed if the upload step changes `audio_url` values or rewrites episode metadata:

   ```bash
   cd /path/to/gruener_podcast_feed
   . .venv/bin/activate
   gruenpod publish-feed --env-file /secure/path/gruenpod.env
   ```

5. `IF`
   Check command exit codes and branch on failure.

6. `Email` / `Slack` / `Telegram`
   Send success or failure notifications with the run id and output path.

Recommended secret handling in n8n:

- store IMAP and OpenAI credentials in n8n credentials or environment-backed secrets
- mount the `.env` file from a protected location if you prefer file-based config
- do not hard-code secrets in node parameters

## Suggested Deployment Pattern

For a small reliable setup:

1. Host the repo on a Linux VM or container host.
2. Create a Python virtual environment and install the package with `pip install -e .`.
3. Store the runtime `.env` in a protected directory such as `/etc/gruenpod/gruenpod.env`.
4. Let n8n call the CLI on schedule.
5. Upload MP3 and feed artifacts to public object storage.
6. Expose `feed.xml` via HTTPS and submit it to podcast directories.

## What Still Needs To Be Added

- production audio rendering module
- object storage upload step beyond local directory publishing
- feed enrichment with podcast-specific XML tags
- tests for IMAP parsing, event extraction, and RSS generation
