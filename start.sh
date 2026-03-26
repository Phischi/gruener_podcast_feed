#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -x ".venv/bin/gruenpod" ]]; then
  echo "Missing .venv/bin/gruenpod. Create the virtualenv and run 'pip install -e .' first." >&2
  exit 1
fi

if [[ ! -f ".env" ]]; then
  echo "Missing .env. Copy .env.example to .env and fill in the required values first." >&2
  exit 1
fi

exec .venv/bin/gruenpod --env-file .env run "$@"
