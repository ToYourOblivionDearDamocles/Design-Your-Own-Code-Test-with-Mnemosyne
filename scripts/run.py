from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = ROOT / ".venv"


def venv_python() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Mnemosyne local web app.")
    parser.add_argument("port", nargs="?", default="8000", help="Port to bind on 127.0.0.1. Default: 8000")
    args = parser.parse_args()

    python_bin = venv_python()
    if not python_bin.exists():
        print("Mnemosyne virtualenv is missing.", file=sys.stderr)
        print("Run: python scripts/setup.py", file=sys.stderr)
        return 1

    command = [
        str(python_bin),
        "-m",
        "uvicorn",
        "mnemosyne.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(args.port),
    ]
    print(f"Open http://127.0.0.1:{args.port}")
    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
