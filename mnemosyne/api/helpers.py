from __future__ import annotations

from mnemosyne.verifier import service as verifier_service


def _with_repair_hints(result: dict) -> dict:
    return verifier_service.with_repair_hints(result)


def _error_result(
    error: Exception,
    parse_warnings: list[str] | None = None,
    *,
    failed_layer: str = "json",
    **extra: object,
) -> dict:
    return verifier_service.error_result(error, parse_warnings, failed_layer=failed_layer, **extra)


def _parse_error_result(error: Exception, parse_warnings: list[str] | None = None, **extra: object) -> dict:
    return verifier_service.parse_error_result(error, parse_warnings, **extra)


def collect_problem_requirements(problems: list[dict]) -> list[dict]:
    seen: set[tuple[str, str, str]] = set()
    requirements: list[dict] = []
    for problem in problems:
        for req in problem.get("requirements", []):
            if not isinstance(req, dict):
                continue
            key = (
                str(req.get("package") or ""),
                str(req.get("pip") or ""),
                str(req.get("import_name") or ""),
            )
            if key in seen:
                continue
            seen.add(key)
            requirements.append(req)
    return requirements
