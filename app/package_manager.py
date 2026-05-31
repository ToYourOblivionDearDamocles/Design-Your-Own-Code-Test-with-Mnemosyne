from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path
from typing import Any, Literal

from app.dependencies import check_requirements
from app.problem_store import get_problem

ROOT_DIR = Path(__file__).resolve().parents[1]
BASE_REQUIREMENTS = ROOT_DIR / "requirements.txt"
ML_REQUIREMENTS = ROOT_DIR / "requirements-ml.txt"
InstallScope = Literal["current_problem", "optional_ml"]


def runtime_status(problem_id: str | None = None) -> dict[str, Any]:
    current_problem = None
    current_problem_status = check_requirements([])
    if problem_id:
        problem = get_problem(problem_id)
        current_problem = {
            "id": problem["id"],
            "title": problem.get("title", problem["id"]),
        }
        current_problem_status = check_requirements(problem.get("requirements", []))

    optional_ml_status = check_requirements(_read_requirement_specs(ML_REQUIREMENTS))

    return {
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
            "in_virtualenv": sys.prefix != getattr(sys, "base_prefix", sys.prefix),
        },
        "groups": {
            "base": {
                "label": "Base app",
                **check_requirements(_read_requirement_specs(BASE_REQUIREMENTS)),
            },
            "current_problem": {
                "label": "Current problem",
                "problem": current_problem,
                **current_problem_status,
            },
            "optional_ml": {
                "label": "Optional ML stack",
                **optional_ml_status,
            },
        },
    }


def install_requirements(scope: InstallScope, problem_id: str | None = None) -> dict[str, Any]:
    before = runtime_status(problem_id)
    group = before["groups"][scope]
    specs = [req["pip"] for req in group["missing"] if req.get("pip")]

    if not specs:
        return {
            "ok": True,
            "scope": scope,
            "installed": [],
            "message": "Nothing to install.",
            "stdout": "",
            "stderr": "",
            "status": before,
        }

    completed = subprocess.run(
        [sys.executable, "-m", "pip", "install", *specs],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    importlib.invalidate_caches()
    after = runtime_status(problem_id)

    return {
        "ok": completed.returncode == 0,
        "scope": scope,
        "installed": specs,
        "message": "Install finished." if completed.returncode == 0 else "Install failed.",
        "returncode": completed.returncode,
        "stdout": _tail(completed.stdout),
        "stderr": _tail(completed.stderr),
        "status": after,
    }


def install_dependency_requirements(raw_requirements: list[Any], scope: str = "draft_problem") -> dict[str, Any]:
    before = check_requirements(raw_requirements)
    specs = [req["pip"] for req in before["missing"] if req.get("pip")]

    if not specs:
        return {
            "ok": True,
            "scope": scope,
            "installed": [],
            "message": "Nothing to install.",
            "stdout": "",
            "stderr": "",
            "dependency_status": before,
        }

    completed = subprocess.run(
        [sys.executable, "-m", "pip", "install", *specs],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    importlib.invalidate_caches()
    after = check_requirements(raw_requirements)

    return {
        "ok": completed.returncode == 0,
        "scope": scope,
        "installed": specs,
        "message": "Install finished." if completed.returncode == 0 else "Install failed.",
        "returncode": completed.returncode,
        "stdout": _tail(completed.stdout),
        "stderr": _tail(completed.stderr),
        "dependency_status": after,
    }


def _read_requirement_specs(path: Path) -> list[str]:
    if not path.exists():
        return []

    specs: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-"):
            continue
        if " #" in line:
            line = line.split(" #", 1)[0].strip()
        specs.append(line)
    return specs


def _tail(text: str, limit: int = 12000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]
