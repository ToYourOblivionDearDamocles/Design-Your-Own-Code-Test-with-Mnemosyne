#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements/base.txt -r requirements/ml.txt
echo "Mnemosyne is ready. Run: ./scripts/run.sh"
