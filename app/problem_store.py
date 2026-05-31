from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from app.json_format import dumps_compact_json

ROOT_DIR = Path(__file__).resolve().parents[1]
PROBLEMS_DIR = ROOT_DIR / "problems"


def _load_problem_file(problem_dir: Path) -> dict[str, Any]:
    path = problem_dir / "problem.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing problem.json in {problem_dir}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("slug", problem_dir.name)
    return data


def list_problems() -> list[dict[str, Any]]:
    problems: list[dict[str, Any]] = []
    for problem_dir in sorted(PROBLEMS_DIR.iterdir()):
        if not problem_dir.is_dir():
            continue
        try:
            p = _load_problem_file(problem_dir)
        except Exception:
            continue
        problems.append(
            {
                "id": p["id"],
                "slug": p.get("slug", problem_dir.name),
                "title": p["title"],
                "difficulty": p.get("difficulty", "unknown"),
                "tags": p.get("tags", []),
                "entry_kind": p.get("entry_kind", "function"),
            }
        )
    return problems


def list_tags() -> list[dict[str, Any]]:
    tag_map: dict[str, list[dict[str, Any]]] = {}
    for problem in list_problems():
        tags = problem.get("tags") or ["untagged"]
        for tag in tags:
            tag_map.setdefault(str(tag), []).append(problem)

    return [
        {
            "tag": tag,
            "count": len(problems),
            "problems": problems,
        }
        for tag, problems in sorted(tag_map.items(), key=lambda item: item[0].lower())
    ]


def get_problem(problem_id: str) -> dict[str, Any]:
    for problem_dir in PROBLEMS_DIR.iterdir():
        if not problem_dir.is_dir():
            continue
        p = _load_problem_file(problem_dir)
        if p.get("id") == problem_id or problem_dir.name == problem_id:
            return p
    raise KeyError(f"Problem not found: {problem_id}")


def get_problem_path(problem_id: str) -> Path:
    for problem_dir in PROBLEMS_DIR.iterdir():
        if not problem_dir.is_dir():
            continue
        try:
            p = _load_problem_file(problem_dir)
        except Exception:
            continue
        if p.get("id") == problem_id or problem_dir.name == problem_id:
            return problem_dir / "problem.json"
    raise KeyError(f"Problem not found: {problem_id}")


def save_problem(problem: dict[str, Any]) -> Path:
    problem_id = str(problem["id"])
    problem_dir = (PROBLEMS_DIR / problem_id).resolve()
    problems_root = PROBLEMS_DIR.resolve()
    if problems_root not in problem_dir.parents:
        raise ValueError("Resolved problem path is outside the problems directory.")
    problem_dir.mkdir(parents=True, exist_ok=True)
    path = problem_dir / "problem.json"
    data = dict(problem)
    data.pop("slug", None)
    path.write_text(dumps_compact_json(data, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def delete_problem(problem_id: str) -> Path:
    path = get_problem_path(problem_id)
    problem_dir = path.parent
    shutil.rmtree(problem_dir)
    return problem_dir


def append_test_case(problem_id: str, group: str, test_case: dict[str, Any]) -> dict[str, Any]:
    if group not in {"visible_tests", "hidden_tests"}:
        raise ValueError("group must be visible_tests or hidden_tests")
    problem = get_problem(problem_id)
    tests = problem.setdefault(group, [])
    if not isinstance(tests, list):
        raise ValueError(f"{group} must be a list")
    tests.append(test_case)
    return problem


def public_problem(problem: dict[str, Any]) -> dict[str, Any]:
    """Return the problem fields that are safe to show in the UI."""
    hidden = {
        "hidden_tests",
        "reference_solution",
        "solution",
        "solution_explanation",
        "complexity",
        "private_notes",
    }
    return {k: v for k, v in problem.items() if k not in hidden}


def problem_solution(problem: dict[str, Any]) -> dict[str, Any]:
    return {
        "problem_id": problem["id"],
        "problem_title": problem.get("title", problem["id"]),
        "solution": problem.get("solution") or problem.get("reference_solution") or "",
        "explanation": problem.get("solution_explanation", ""),
        "complexity": problem.get("complexity", {}),
    }
