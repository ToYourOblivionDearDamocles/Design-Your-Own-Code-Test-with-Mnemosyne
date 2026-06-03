from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = ROOT / ".venv"
MIN_VERSION = (3, 10)
MAX_EXCLUSIVE = (3, 14)


def run(command: list[str], *, cwd: Path = ROOT) -> None:
    print("+ " + " ".join(command))
    subprocess.check_call(command, cwd=cwd)


def parse_python_command(value: str) -> list[str]:
    if sys.platform == "win32" and value.startswith("py "):
        return value.split()
    return [value]


def python_version(command: list[str]) -> tuple[int, int, int] | None:
    code = "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}')"
    try:
        output = subprocess.check_output([*command, "-c", code], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    try:
        major, minor, micro = output.split(".")[:3]
        return int(major), int(minor), int(micro)
    except ValueError:
        return None


def supported(version: tuple[int, int, int] | None) -> bool:
    if version is None:
        return False
    return MIN_VERSION <= version[:2] < MAX_EXCLUSIVE


def candidate_commands() -> list[list[str]]:
    env_python = os.environ.get("PYTHON")
    if env_python:
        return [parse_python_command(env_python)]

    if sys.platform == "win32":
        return [
            ["py", "-3.13"],
            ["py", "-3.12"],
            ["py", "-3.11"],
            ["py", "-3.10"],
            ["python"],
        ]

    return [[name] for name in ("python3.13", "python3.12", "python3.11", "python3.10", "python3")]


def choose_python() -> list[str] | None:
    for command in candidate_commands():
        version = python_version(command)
        if supported(version):
            print(f"Using Python {'.'.join(map(str, version))}: {' '.join(command)}")
            return command
    return None


def venv_python() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def existing_venv_is_supported() -> bool:
    python_bin = venv_python()
    if not python_bin.exists():
        return True
    return supported(python_version([str(python_bin)]))


def remove_bad_venv() -> None:
    if VENV_DIR.exists() and not existing_venv_is_supported():
        print("Existing .venv uses an unsupported Python; recreating it.")
        shutil.rmtree(VENV_DIR)


def main() -> int:
    python = choose_python()
    if python is None:
        print("Mnemosyne needs Python 3.10 through 3.13.", file=sys.stderr)
        print("Python 3.14 is too new for some compiled dependencies right now.", file=sys.stderr)
        print("Install Python 3.12 or 3.13, then rerun:", file=sys.stderr)
        print("  python scripts/setup.py", file=sys.stderr)
        return 1

    remove_bad_venv()

    if not VENV_DIR.exists():
        run([*python, "-m", "venv", str(VENV_DIR)])

    python_bin = venv_python()
    run([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"])
    run([
        str(python_bin),
        "-m",
        "pip",
        "install",
        "-r",
        str(ROOT / "requirements" / "base.txt"),
        "-r",
        str(ROOT / "requirements" / "ml.txt"),
    ])

    print("Mnemosyne is ready. Run: python scripts/run.py")
    return 0
