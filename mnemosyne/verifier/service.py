from __future__ import annotations

from typing import Any

from mnemosyne.runtime.judge import judge_code
from mnemosyne.problem_authoring import (
    AUTHORING_API_SCHEMA,
    build_verifier_layers,
    parse_problem_collection,
    validate_problem_collection,
    validate_problem_spec,
)
from mnemosyne.verifier.repair_hints import build_repair_hint_report


def authoring_schema() -> dict[str, Any]:
    """Return the public problem JSON schema used by verifier clients."""
    return AUTHORING_API_SCHEMA


def with_repair_hints(result: dict[str, Any]) -> dict[str, Any]:
    """Attach model-readable repair hints to a failed verifier result."""
    if result.get("ok"):
        return result
    report = build_repair_hint_report(result.get("errors", []), result.get("warnings", []))
    return {
        **result,
        "repair_report": report,
        "repair_hints": report["hints"],
    }


def error_result(
    error: Exception,
    parse_warnings: list[str] | None = None,
    *,
    failed_layer: str = "json",
    **extra: object,
) -> dict[str, Any]:
    errors = [str(error)]
    warnings = parse_warnings or []
    return with_repair_hints(
        {
            "ok": False,
            "errors": errors,
            "warnings": warnings,
            "layers": build_verifier_layers(errors, warnings, failed_layer=failed_layer),
            "problem": None,
            "problems": [],
            **extra,
        }
    )


def parse_error_result(error: Exception, parse_warnings: list[str] | None = None, **extra: object) -> dict[str, Any]:
    return error_result(error, parse_warnings, failed_layer="json", **extra)


def validate_content(content: str, *, verify_reference: bool = True) -> dict[str, Any]:
    """Parse and validate one or many problem JSON objects from raw text."""
    parse_warnings: list[str] = []
    try:
        problems = parse_problem_collection(content, warnings=parse_warnings)
    except ValueError as exc:
        return parse_error_result(exc, parse_warnings)

    validation = validate_problem_collection(problems, verify_reference=verify_reference)
    validation["warnings"] = parse_warnings + validation["warnings"]
    return with_repair_hints(validation)


def run_reference_content(content: str) -> dict[str, Any]:
    """Run the reference solution for exactly one parsed problem."""
    parse_warnings: list[str] = []
    try:
        problems = parse_problem_collection(content, warnings=parse_warnings)
    except ValueError as exc:
        return parse_error_result(exc, parse_warnings)

    if len(problems) != 1:
        return with_repair_hints(
            {
                "ok": False,
                "errors": ["Run reference expects exactly one problem."],
                "warnings": parse_warnings,
                "layers": build_verifier_layers(["Run reference expects exactly one problem."], parse_warnings, failed_layer="schema"),
                "problem": None,
                "problems": problems,
            }
        )

    validation = validate_problem_spec(problems[0], verify_reference=False)
    validation["warnings"] = parse_warnings + validation["warnings"]
    if not validation["ok"]:
        return with_repair_hints({**validation, "result": None})

    problem = validation["problem"]
    result = judge_code(problem, problem.get("reference_solution", ""), "submit").as_dict()
    return {
        "ok": result["status"] == "Accepted",
        "errors": [] if result["status"] == "Accepted" else [result.get("error") or result["status"]],
        "warnings": validation["warnings"],
        "problem": problem,
        "problems": [problem],
        "result": result,
        "layers": build_verifier_layers(
            [] if result["status"] == "Accepted" else [result.get("error") or result["status"]],
            validation["warnings"],
            failed_layer="code",
        ),
    }


def repair_hints(errors: list[str], warnings: list[str] | None = None) -> dict[str, Any]:
    return build_repair_hint_report(errors, warnings or [])
