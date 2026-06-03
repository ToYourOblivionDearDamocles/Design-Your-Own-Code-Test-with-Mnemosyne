from __future__ import annotations

import importlib.metadata
import importlib.util
import re
import shlex
from typing import Any


def normalize_requirement(raw: Any) -> dict[str, Any]:
    """Normalize a problem requirement into a small JSON-safe record."""
    if isinstance(raw, str):
        package = _package_name_from_spec(raw)
        return {
            "package": package,
            "pip": raw,
            "import_name": package.replace("-", "_"),
            "optional": False,
        }

    if isinstance(raw, dict):
        pip_spec = str(raw.get("pip") or raw.get("requirement") or raw.get("package") or "").strip()
        package = str(raw.get("package") or _package_name_from_spec(pip_spec)).strip()
        import_name = str(raw.get("import_name") or package.replace("-", "_")).strip()
        return {
            "package": package,
            "pip": pip_spec or package,
            "import_name": import_name,
            "optional": bool(raw.get("optional", False)),
            "notes": raw.get("notes", ""),
        }

    return {
        "package": str(raw),
        "pip": str(raw),
        "import_name": str(raw).replace("-", "_"),
        "optional": False,
    }


def problem_requirements(problem: dict[str, Any]) -> list[dict[str, Any]]:
    return [normalize_requirement(item) for item in problem.get("requirements", [])]


def check_problem_requirements(problem: dict[str, Any]) -> dict[str, Any]:
    return check_requirements(problem.get("requirements", []))


def check_requirements(raw_requirements: list[Any]) -> dict[str, Any]:
    requirements = []
    missing = []

    for req in [normalize_requirement(item) for item in raw_requirements]:
        import_name = req["import_name"]
        found = importlib.util.find_spec(import_name) is not None
        installed_version = _installed_version(req["package"]) if found else None
        item = {
            **req,
            "installed": found,
            "installed_version": installed_version,
        }
        requirements.append(item)
        if not found and not req.get("optional"):
            missing.append(item)

    return {
        "ok": not missing,
        "requirements": requirements,
        "missing": missing,
        "install_command": build_install_command(missing),
    }


def build_install_command(requirements: list[dict[str, Any]]) -> str:
    specs = [str(req.get("pip") or req.get("package")).strip() for req in requirements]
    specs = [spec for spec in specs if spec]
    if not specs:
        return ""
    return ".venv/bin/pip install " + " ".join(shlex.quote(spec) for spec in specs)


def _package_name_from_spec(spec: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9_.-]+)", spec)
    return match.group(1) if match else spec.strip()


def _installed_version(package: str) -> str | None:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None
