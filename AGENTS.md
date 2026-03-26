# Repository Guidelines

## Project Structure & Module Organization
Core application code lives in `src/gruener_podcast_feed/`. Use `cli.py` for command entry points, `pipeline.py` for orchestration, and focused modules such as `imap_client.py`, `newsletter.py`, `script_generator.py`, and `feed/rss_writer.py` for domain logic. Runtime artifacts are written under `runs/<run-id>/` and public outputs under `public/`. Legacy notebooks remain at the repository root, and `email-connector/` contains an older Go-based IMAP helper that is not the primary path forward. Operational notes live in `docs/`.

## Build, Test, and Development Commands
Create an isolated environment and install the package in editable mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Useful CLI commands:

```bash
gruenpod fetch-email --env-file .env
gruenpod build-from-eml sample.eml --env-file .env
gruenpod run --env-file .env
gruenpod publish-feed --env-file .env
```

Use `go run main.go` inside `email-connector/` only when working on the legacy connector.

## Coding Style & Naming Conventions
Follow existing Python style: 4-space indentation, `snake_case` for functions and modules, `PascalCase` for dataclasses, and explicit type hints on public functions. Keep modules narrow and side effects close to the CLI or pipeline layer. Prefer standard library helpers before adding dependencies. There is no committed formatter or linter config yet, so match the surrounding code and keep imports grouped and readable.

## Testing Guidelines
Automated tests are not in place yet, so new contributions should add `pytest`-style tests under a new `tests/` package when practical. Name files `test_<module>.py` and cover deterministic paths first, especially parsing, feed generation, and config loading. For pipeline changes, include a manual verification note with the exact `gruenpod` command used.

## Commit & Pull Request Guidelines
Recent history uses short, imperative commit subjects such as `Add top-level project README` and `Merge email-connector to main`. Keep commit messages concise, present tense, and scoped to one change. Pull requests should include a short summary, any required `.env` or operational changes, linked issues if available, and sample output paths or screenshots when changing generated artifacts or feed content.

## Configuration & Security
Start from `.env.example`; never commit populated secrets or generated `runs/` data. Treat IMAP credentials, OpenAI keys, and published feed URLs as sensitive. When adjusting publishing or automation behavior, update `docs/operations.md` alongside the code.
