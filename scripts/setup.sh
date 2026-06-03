#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

choose_python() {
  if [ -n "${PYTHON:-}" ]; then
    command -v "$PYTHON"
    return
  fi

  for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      "$candidate" - <<'PY' && command -v "$candidate" && return
import sys
raise SystemExit(0 if (3, 10) <= sys.version_info[:2] < (3, 14) else 1)
PY
    fi
  done
}

PYTHON_BIN="$(choose_python || true)"

if [ -z "$PYTHON_BIN" ]; then
  cat >&2 <<'MSG'
Mnemosyne needs Python 3.10 through 3.13.

Python 3.14 is too new for some compiled dependencies right now.
Install Python 3.12 or 3.13, then rerun:

  PYTHON=python3.12 ./scripts/setup.sh
MSG
  exit 1
fi

if [ -x .venv/bin/python ] && ! .venv/bin/python - <<'PY'; then
import sys
raise SystemExit(0 if (3, 10) <= sys.version_info[:2] < (3, 14) else 1)
PY
  echo "Existing .venv uses an unsupported Python; recreating it."
  rm -rf .venv
fi

"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements/base.txt -r requirements/ml.txt
echo "Mnemosyne is ready. Run: ./scripts/run.sh"
