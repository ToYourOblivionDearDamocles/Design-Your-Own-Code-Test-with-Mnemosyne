from __future__ import annotations

import json
from typing import Any


def dumps_compact_json(value: Any, *, ensure_ascii: bool = False, indent: int = 2) -> str:
    """Pretty-print JSON while keeping short lists and test cases compact."""
    return _format_json(value, level=0, ensure_ascii=ensure_ascii, indent=indent)


def _format_json(value: Any, *, level: int, ensure_ascii: bool, indent: int) -> str:
    inline = _inline_json(value, ensure_ascii=ensure_ascii)
    if _should_inline_json(value, inline):
        return inline

    pad = " " * (indent * level)
    child_pad = " " * (indent * (level + 1))

    if isinstance(value, list):
        if not value:
            return "[]"
        items = [_format_json(item, level=level + 1, ensure_ascii=ensure_ascii, indent=indent) for item in value]
        return "[\n" + ",\n".join(child_pad + item for item in items) + f"\n{pad}]"

    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = []
        for key, item in value.items():
            rendered_key = json.dumps(str(key), ensure_ascii=ensure_ascii)
            rendered_value = _format_json(item, level=level + 1, ensure_ascii=ensure_ascii, indent=indent)
            lines.append(f"{child_pad}{rendered_key}: {rendered_value}")
        return "{\n" + ",\n".join(lines) + f"\n{pad}}}"

    return inline


def _inline_json(value: Any, *, ensure_ascii: bool) -> str:
    return json.dumps(value, ensure_ascii=ensure_ascii, default=str)


def _should_inline_json(value: Any, inline: str) -> bool:
    if not isinstance(value, (list, dict)):
        return True
    if "\n" in inline:
        return False
    if isinstance(value, list):
        return len(inline) <= 160 and _is_simple_json_list(value)
    if _is_test_case_like(value):
        return len(inline) <= 320
    return len(inline) <= 120 and _is_small_json_object(value)


def _is_simple_json_list(value: list[Any]) -> bool:
    if not value:
        return True
    return all(not isinstance(item, dict) or _is_test_case_like(item) for item in value)


def _is_small_json_object(value: dict[Any, Any]) -> bool:
    return all(not isinstance(item, (dict, list)) or len(_inline_json(item, ensure_ascii=False)) <= 80 for item in value.values())


def _is_test_case_like(value: dict[Any, Any]) -> bool:
    keys = {str(key) for key in value}
    return "name" in keys and ({"args", "expected"} <= keys or "code" in keys)
