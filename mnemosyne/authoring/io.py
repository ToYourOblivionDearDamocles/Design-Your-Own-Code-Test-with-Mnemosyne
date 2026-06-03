from __future__ import annotations

import json
import re
from typing import Any

from mnemosyne.runtime.json_format import dumps_compact_json

SMART_DOUBLE_QUOTES = str.maketrans({
    "“": '"',
    "”": '"',
    "„": '"',
    "‟": '"',
})
SMART_SINGLE_QUOTES = str.maketrans({
    "‘": "'",
    "’": "'",
    "‚": "'",
    "‛": "'",
})


def prepare_problem_content(content: str, warnings: list[str] | None = None) -> str:
    cleaned = content.strip().removeprefix("\ufeff").strip()
    if not cleaned:
        raise ValueError("Invalid JSON: content is empty.")

    fenced = re.match(r"^```(?:json|JSON)?\s*\n?(.*?)\n?```\s*$", cleaned, re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()
        _warn(warnings, "Removed markdown json code fence before parsing.")
    else:
        start, end = _json_bounds(cleaned)
        if start >= 0 and end > start and (start > 0 or end < len(cleaned) - 1):
            cleaned = cleaned[start : end + 1].strip()
            _warn(warnings, "Ignored text before or after the JSON object.")

    if any(ch in cleaned for ch in "“”„‟"):
        cleaned = cleaned.translate(SMART_DOUBLE_QUOTES)
        _warn(warnings, 'Converted smart double quotes to straight JSON quotes (").')
    if any(ch in cleaned for ch in "‘’‚‛"):
        cleaned = cleaned.translate(SMART_SINGLE_QUOTES)
        _warn(warnings, "Converted smart apostrophes to ASCII apostrophes inside JSON text.")

    return cleaned


def parse_problem_content(content: str, warnings: list[str] | None = None) -> dict[str, Any]:
    cleaned = prepare_problem_content(content, warnings)
    data = _loads_problem_json(cleaned)
    if not isinstance(data, dict):
        raise ValueError("Problem JSON must be an object.")
    return data


def parse_problem_collection(content: str, warnings: list[str] | None = None) -> list[dict[str, Any]]:
    cleaned = prepare_problem_content(content, warnings)
    data = _loads_problem_json(cleaned)
    if isinstance(data, dict) and isinstance(data.get("problems"), list):
        data = data["problems"]
        _warn(warnings, 'Read multiple problems from the top-level "problems" array.')
    elif isinstance(data, dict):
        return [data]
    if not isinstance(data, list):
        raise ValueError("Problem JSON must be one object, an array of objects, or an object with a problems array.")
    if not data:
        raise ValueError("Problem JSON array must contain at least one problem.")
    problems: list[dict[str, Any]] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Problem JSON array item {idx} must be an object.")
        problems.append(item)
    return problems


def _loads_problem_json(cleaned: str) -> Any:
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        hint = ""
        if "'" in cleaned:
            hint = " JSON syntax still requires straight double quotes for keys and string delimiters."
        raise ValueError(f"Invalid JSON: {e.msg} at line {e.lineno}, column {e.colno}.{hint}") from e


def _json_bounds(text: str) -> tuple[int, int]:
    candidates = []
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start >= 0 and end > start:
            candidates.append((start, end))
    if not candidates:
        return -1, -1
    return min(candidates, key=lambda item: item[0])


def _warn(warnings: list[str] | None, message: str) -> None:
    if warnings is not None and message not in warnings:
        warnings.append(message)


def format_problem_json(value: Any) -> str:
    return dumps_compact_json(value, ensure_ascii=False)

