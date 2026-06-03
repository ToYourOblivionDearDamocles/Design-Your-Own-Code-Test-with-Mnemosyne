#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${1:-8000}"
.venv/bin/python -m uvicorn mnemosyne.main:app --host 127.0.0.1 --port "$PORT"
