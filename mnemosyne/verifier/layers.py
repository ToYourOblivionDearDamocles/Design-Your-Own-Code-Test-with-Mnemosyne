from __future__ import annotations

from typing import Any

VERIFIER_LAYER_META: tuple[dict[str, str], ...] = (
    {"id": "json", "name": "JSON", "description": "The submitted text parses as JSON."},
    {"id": "schema", "name": "Schema", "description": "Required machine-readable fields and types are present."},
    {"id": "content", "name": "Content", "description": "Problem, Theory, Example, Solution, complexity, tests, and tags are coherent."},
    {"id": "code", "name": "Code", "description": "Starter/reference code and explicit tests are internally consistent."},
)

def _empty_verifier_layers() -> list[dict[str, Any]]:
    return [
        {
            "id": meta["id"],
            "name": meta["name"],
            "description": meta["description"],
            "status": "pending",
            "errors": [],
            "warnings": [],
        }
        for meta in VERIFIER_LAYER_META
    ]


def _layer_by_id(layers: list[dict[str, Any]], layer_id: str) -> dict[str, Any]:
    for layer in layers:
        if layer.get("id") == layer_id:
            return layer
    fallback = {"id": layer_id, "name": layer_id, "description": "", "status": "pending", "errors": [], "warnings": []}
    layers.append(fallback)
    return fallback


def _add_layer_issue(layers: list[dict[str, Any]], layer_id: str, kind: str, message: str) -> None:
    bucket = _layer_by_id(layers, layer_id).setdefault(kind, [])
    if message not in bucket:
        bucket.append(message)


def _merge_verifier_layers(target: list[dict[str, Any]], source: list[dict[str, Any]], prefix: str = "") -> None:
    for layer in source:
        layer_id = str(layer.get("id") or "schema")
        for kind in ("errors", "warnings"):
            for message in layer.get(kind, []) or []:
                text = f"{prefix}: {message}" if prefix else str(message)
                _add_layer_issue(target, layer_id, kind, text)


def _finalize_verifier_layers(layers: list[dict[str, Any]]) -> None:
    first_failed_index: int | None = None
    for idx, layer in enumerate(layers):
        if layer.get("errors"):
            layer["status"] = "failed"
            if first_failed_index is None:
                first_failed_index = idx
        elif layer.get("warnings"):
            layer["status"] = "warning"
        else:
            layer["status"] = "passed"

    if first_failed_index is None:
        return

    # Later layers that have no direct evidence should not be shown as passed.
    # For example, invalid JSON means Schema/Content/Code were never meaningfully
    # checked. Mark those layers as blocked so the UI points the user to the
    # earliest layer that must be repaired first.
    for layer in layers[first_failed_index + 1:]:
        if layer.get("status") == "passed" and not layer.get("errors") and not layer.get("warnings"):
            layer["status"] = "blocked"
            layer["description"] = "Fix the previous failed layer before this layer can be checked."


def build_verifier_layers(
    errors: list[str] | tuple[str, ...] | None = None,
    warnings: list[str] | tuple[str, ...] | None = None,
    *,
    failed_layer: str | None = None,
) -> list[dict[str, Any]]:
    layers = _empty_verifier_layers()
    for message in errors or []:
        _add_layer_issue(layers, failed_layer or _classify_verifier_issue(str(message)), "errors", str(message))
    for message in warnings or []:
        _add_layer_issue(layers, _classify_verifier_issue(str(message)), "warnings", str(message))
    _finalize_verifier_layers(layers)
    return layers


def _classify_verifier_issue(message: str) -> str:
    text = message.lower()
    if "json" in text or "expecting" in text or "delimiter" in text or "decode" in text:
        return "json"
    if "inline math" in text or "display math" in text or "latex" in text:
        return "content"
    content_markers = (
        "statement",
        "input / output",
        "input/output",
        "return value",
        "theory",
        "examples",
        "worked example",
        "tags",
        "complexity",
        "explicit test",
    )
    if any(marker in text for marker in content_markers):
        return "content"
    code_markers = (
        "reference_solution",
        "starter_code",
        "function_name",
        "define function",
        "type-annotate",
        "return type annotation",
        "raises an error",
        "verification failed",
        "output mismatch",
        "expected output",
        "auto-filled",
        "corrected expected",
        "dependencies are missing",
        "package import",
        "judge",
    )
    if any(marker in text for marker in code_markers):
        return "code"
    return "schema"
