# Gruener Podcast Feed

This repository is an early-stage pipeline for turning a political newsletter into a spoken podcast episode.

The current setup focuses on a German-language format called `GrünGeschnackt`. It combines:

- a Go program that reads the latest tagged newsletter email from an IMAP inbox
- an OpenAI prompt that rewrites that newsletter into a podcast-style dialogue script
- Python notebooks that experiment with turning the script into speech with OpenAI TTS and Gemini TTS

The repository is closer to a proof of concept than a finished product, but the main building blocks are already here.

## What The Repository Does

The intended workflow is:

1. A newsletter arrives by email.
2. The Go email connector logs into an IMAP inbox and scans the latest messages.
3. It selects the first message whose subject starts with `[gn]`.
4. The email body is cleaned up, stripped of HTML, and truncated to fit model limits.
5. The cleaned newsletter text is sent to OpenAI with a system prompt tailored for the `GrünGeschnackt` podcast format.
6. The generated podcast script is written to `podcast_scripts/`.
7. The notebooks can then be used to synthesize spoken audio from the generated text.

## Repository Structure

- [email-connector/main.go](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/email-connector/main.go): IMAP ingestion and newsletter-to-script generation in Go
- [email-connector/system_prompt.txt](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/email-connector/system_prompt.txt): prompt that defines the podcast style, structure, and tone
- [email-connector/README.md](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/email-connector/README.md): older subproject README for the Go connector
- [gruen_geschnackt_poc.ipynb](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/gruen_geschnackt_poc.ipynb): prototype notebook for multi-speaker dialogue TTS and audio stitching
- [podcast_voice_generator.ipynb](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/podcast_voice_generator.ipynb): smaller notebook for text generation and single-speaker TTS experiments
- [requirements.txt](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/requirements.txt): Python dependencies used by the notebooks

## Current Components

### 1. Email Connector

The Go connector:

- loads credentials from a local `.env`
- connects to an IMAP server via TLS
- reads the `INBOX`
- fetches up to the last 100 messages
- finds the first email whose subject starts with `[gn]`
- extracts text from plain text or HTML email parts
- sends the cleaned content to OpenAI chat completions
- saves the generated script into `podcast_scripts/<sanitized-subject>.txt`

The current prompt instructs the model to:

- produce a dialogue between `Pia Plastikfrei` and `Nico Nachhaltig`
- structure the episode into political updates, events, and engagement opportunities
- keep the language friendly and easy to listen to
- include a machine-readable iCal overview of newsletter events in the shownotes

Important caveat:
The connector currently writes only a `.txt` script file. It does not yet create a real `.ics` file, even though the prompt asks for calendar output.

### 2. Notebook Prototypes

The notebooks cover the audio side of the pipeline:

- `podcast_voice_generator.ipynb` tests OpenAI chat generation and basic text-to-speech output
- `gruen_geschnackt_poc.ipynb` prototypes a two-speaker podcast, splitting the script into segments and assigning different voices to `Pia` and `Nico`

The multi-speaker notebook uses `pydub` to concatenate audio segments and export a final MP3. In practice, that means you also need FFmpeg tooling available on the machine. The checked notebook output shows failures caused by missing `ffprobe`, so audio assembly is not fully plug-and-play yet.

## Requirements

### Go

- Go 1.21+

### Python

Install the notebook dependencies from [requirements.txt](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/requirements.txt):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### External Services

- an IMAP-enabled email account
- an OpenAI API key for script generation and OpenAI TTS experiments
- optionally a Gemini API key for the Gemini TTS notebook cells
- FFmpeg tools, especially `ffprobe`, if you want `pydub` audio concatenation to work reliably

## Environment Variables

For the Go connector, create a `.env` file in the repository root or inside `email-connector/` depending on where you run it from:

```env
EMAIL_USER=your.email@example.com
EMAIL_PASSWORD=your_app_password
EMAIL_SERVER=imap.example.com:993
OPENAI_API_KEY=your_openai_api_key
```

For the notebooks, you may also need:

```env
GEMINI_API_TOKEN=your_gemini_api_key
```

## Running The Email Connector

From the connector directory:

```bash
cd email-connector
go mod download
go run main.go
```

If successful, the program will:

- connect to your mailbox
- process the latest matching newsletter mail
- write the generated podcast script to `email-connector/podcast_scripts/`

## Using The Notebooks

Open the notebooks in Jupyter and run the cells step by step.

Typical usage:

- generate or paste a script
- choose OpenAI or Gemini voices
- synthesize individual dialogue segments
- stitch them into one podcast MP3

The notebooks are exploratory and not yet packaged as a repeatable CLI workflow.

## Outputs

Current outputs in this repo are:

- generated podcast scripts in `podcast_scripts/`
- temporary and final audio files such as `*.mp3` and `*.wav`

These are already ignored by Git via [.gitignore](/media/philipp/installation/projects/ai_projects/gruener_podcast_feed/.gitignore).

## Project Status

This repository is best understood as a prototype for a newsletter-to-podcast pipeline. The core idea works in pieces, but there are still gaps before it becomes a clean end-to-end system:

- the Go connector and the audio generation live in separate workflows
- calendar extraction is requested in the prompt but not implemented as a standalone file output
- the notebooks contain hard-coded experimental content and manual steps
- audio post-processing still depends on local multimedia tooling

## Next Logical Improvements

- turn the notebooks into Python scripts or a small CLI pipeline
- generate a real `.ics` file instead of only asking the model to include calendar data in text
- make the email selection rule configurable instead of hard-coding the `[gn]` subject prefix
- add tests around email parsing and script generation
- document one fully reproducible end-to-end run
