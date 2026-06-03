from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

PROMPT_DIR = Path(__file__).with_name("json")


@lru_cache(maxsize=None)
def load_prompt(prompt_id: str) -> dict[str, Any]:
    """Load a prompt JSON object by id or filename stem."""
    safe_id = prompt_id.removesuffix(".json")
    path = PROMPT_DIR / f"{safe_id}.json"
    if not path.exists():
        raise KeyError(f"Prompt JSON not found: {safe_id}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Prompt JSON must be an object: {path}")
    return data


def prompt_text(prompt_id: str) -> str:
    """Return the plain text body from a prompt JSON file."""
    data = load_prompt(prompt_id)
    value = data.get("text", data.get("template", ""))
    if not isinstance(value, str):
        raise ValueError(f"Prompt {prompt_id} must define string text or template")
    return value


def render_prompt(prompt_id: str, **values: object) -> str:
    """Render a prompt template using simple {{name}} replacement.

    This intentionally avoids Python format syntax so JSON examples containing braces can live
    safely inside prompt files. Missing placeholders are left untouched.
    """
    rendered = prompt_text(prompt_id)
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", str(value))
    return rendered
