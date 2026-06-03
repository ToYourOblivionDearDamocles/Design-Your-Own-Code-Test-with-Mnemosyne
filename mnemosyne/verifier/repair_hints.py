from __future__ import annotations

import json
from typing import Any


def build_repair_hint_report(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return repair_hint_report(errors, warnings)


def repair_hint_report(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    messages = [str(item) for item in (errors + warnings) if str(item).strip()]
    text = "\n".join(messages).lower()
    hints: list[dict[str, Any]] = []

    def add_hint(
        *,
        code: str,
        problem: str,
        action: str,
        example: Any | None = None,
        evidence_patterns: list[str] | None = None,
        severity: str = "error",
        extra: dict[str, Any] | None = None,
    ) -> None:
        if any(hint["code"] == code for hint in hints):
            return
        hint: dict[str, Any] = {
            "code": code,
            "severity": severity,
            "problem": problem,
            "action": action,
        }
        if example is not None:
            hint["example"] = example
        if extra:
            hint.update(extra)
        evidence = _repair_hint_evidence(messages, evidence_patterns or [code])
        if evidence:
            hint["evidence"] = evidence
        hints.append(hint)

    if "invalid json" in text or "jsondecode" in text or "expecting property name enclosed in double quotes" in text:
        add_hint(
            code="invalid_json",
            problem="The model did not return parseable JSON.",
            action="Return only strict JSON: double quotes, no markdown fences, no comments, no trailing commas, no smart quotes.",
            example={"problems": [{"id": "snake_case_id", "visible_tests": [{"name": "basic", "args": [[1, 2]], "expected": 3}]}]},
            evidence_patterns=["invalid json", "expecting property name", "jsondecode"],
        )

    if "timed out" in text or "timeout" in text:
        add_hint(
            code="llm_timeout",
            problem="The model request timed out before returning a draft.",
            action=(
                "Increase the API timeout, reduce the requested problem count, use a faster model, "
                "or split large PDF/image attachments into smaller source materials. For PDF/image inputs, "
                "generate one or two problems first, then expand from the validated drafts."
            ),
            example={"timeout_seconds": 180, "count": 1, "model": "gemini-2.5-flash"},
            evidence_patterns=["timed out", "timeout"],
        )

    if (
        ".args must be a list" in text
        or ".args must be a list of positional arguments" in text
        or ".expected is required" in text
        or "empty test" in text
        or "empty tests" in text
        or "must contain at least one" in text
    ):
        add_hint(
            code="function_test_shape",
            problem="One or more function tests are missing the required test shape.",
            action=(
                "Rewrite every function visible_tests item with exactly name, args, and expected. "
                "Do not use input/output/result fields and do not leave {} placeholders."
            ),
            example={"name": "basic", "args": [[1, 2, 3]], "expected": 6},
            evidence_patterns=[".args must be a list", ".expected is required", "empty test", "must contain at least one"],
        )

    if ("args has" in text and "expects 1 positional" in text) or "single-argument function receiving a list" in text:
        add_hint(
            code="single_argument_wrapping",
            problem="A single list/dict/string input was expanded as multiple positional arguments.",
            action="For def f(nums), wrap the whole input as one positional argument: args must be [[...]], not [...].",
            example={"name": "single_list", "args": [[1, 2, 3]], "expected": 6},
            evidence_patterns=["args has", "expects 1 positional", "single-argument"],
        )

    if "reference_solution output mismatch" in text:
        suggested_edits = _reference_mismatch_suggestions(messages)
        add_hint(
            code="expected_mismatch",
            problem="The reference_solution does not produce the declared expected output for at least one test.",
            action=(
                "Replace each failing test.expected with actual_from_reference when the reference solution is correct. "
                "If multiple valid orders are possible, use a checker that matches the semantics."
            ),
            example={"name": "basic", "args": [2], "expected": "actual_from_reference"},
            evidence_patterns=["reference_solution output mismatch", "expected", "actual"],
            extra={"suggested_edits": suggested_edits} if suggested_edits else None,
        )

    if (
        "reference_solution raises an error" in text
        and ("list' object has no attribute 'shape" in text or "list object has no attribute shape" in text)
    ):
        add_hint(
            code="json_list_array_conversion",
            problem="The function interface expects array/tensor behavior but the draft did not declare runtime conversion.",
            action=(
                "Prefer adding arg_types/return_type such as arg_types [\"numpy.ndarray\"] and return_type \"numpy.ndarray\" "
                "so the judge converts JSON test values before calling the function. For scipy sparse use arg_types [\"scipy.sparse.csr_matrix\"]; for complex use arg_types [\"complex\"]. Otherwise, convert every array-like input inside reference_solution before using .shape, .T, @, tensor methods, sparse methods, or DataFrame methods."
            ),
            example={
                "arg_types": ["numpy.ndarray"],
                "return_type": "numpy.ndarray",
                "starter_code": "import numpy as np\n\ndef cholesky_decomposition(A: np.ndarray) -> np.ndarray:\n    pass\n",
                "reference_solution": "import numpy as np\n\ndef cholesky_decomposition(A):\n    n = A.shape[0]\n    ...\n",
                "tests": {"args": [[[4.0, 2.0], [2.0, 3.0]]], "expected": "JSON-native nested list"},
            },
            evidence_patterns=["reference_solution raises an error", "object has no attribute 'shape", "object has no attribute shape"],
        )

    if "statement has long inline math" in text or "statement has inline math" in text or "use display math" in text and "inline math" in text:
        add_hint(
            code="display_math_preferred",
            problem="The Markdown statement uses long inline math that may be hard to read.",
            action=(
                "Move long equations, matrix formulas, losses, recurrences, and long expressions containing \\sum, \\frac, \\sqrt, or \\int "
                "into display math blocks using $$...$$. Short inline equations like $A = LU$ or $i = j$ are valid."
            ),
            example={"statement": "The update is\n\n$$\nL L^T = A\n$$\n\nwhere $A$ is positive definite."},
            evidence_patterns=["statement has long inline math", "statement has inline math", "use display math", "inline math"],
            severity="warning" if not errors else "error",
        )

    if "anagram" in text or "grouped unordered" in text or "unordered_nested" in text:
        add_hint(
            code="unordered_nested_checker",
            problem="The output is a nested collection where group order or item order should not matter.",
            action="Set checker to {\"type\":\"unordered_nested\"} and keep expected values as nested JSON arrays.",
            example={"checker": {"type": "unordered_nested"}},
            evidence_patterns=["anagram", "grouped unordered", "unordered_nested"],
        )

    if "allclose" in text or "float" in text or "numpy" in text or "tensor" in text:
        add_hint(
            code="numeric_tolerance_checker",
            problem="The problem may return floats, NumPy arrays, or tensors where exact equality is brittle.",
            action="Use checker {\"type\":\"allclose\",\"atol\":1e-5,\"rtol\":1e-5} for approximate numeric outputs.",
            example={"checker": {"type": "allclose", "atol": 1e-5, "rtol": 1e-5}},
            evidence_patterns=["allclose", "float", "numpy", "tensor"],
            severity="warning" if not errors else "error",
        )

    if "requirements[" in text or "looks like a problem instruction" in text or ("requirements" in text and "constraints" in text):
        add_hint(
            code="requirements_vs_constraints",
            problem="requirements contains problem instructions instead of package dependencies.",
            action=(
                "Move instructions such as algorithm rules into constraints. "
                "Keep requirements only for packages with package, pip, and import_name."
            ),
            example={
                "requirements": [{"package": "numpy", "pip": "numpy>=2.0", "import_name": "numpy"}],
                "constraints": ["Use batch gradient descent."],
            },
            evidence_patterns=["requirements[", "looks like a problem instruction", "constraints"],
        )

    if "must define function" in text or "function_name" in text and "define" in text:
        add_hint(
            code="function_name_mismatch",
            problem="The declared function_name does not match starter_code or reference_solution.",
            action="Make function_name, starter_code def name, and reference_solution def name exactly the same.",
            example={
                "function_name": "solve",
                "starter_code": "def solve(nums: list[int]) -> int:\n    pass\n",
                "reference_solution": "def solve(nums):\n    return sum(nums)\n",
            },
            evidence_patterns=["must define function", "function_name", "starter_code", "reference_solution"],
        )

    if "runtime conversion" in text or "runtime types do not match" in text or "visible function signature match" in text:
        add_hint(
            code="runtime_interface_contract",
            problem="The visible starter_code type hints and arg_types/return_type do not describe the same runtime interface.",
            action=(
                "If the starter signature uses np.ndarray, torch.Tensor, pd.DataFrame, scipy sparse matrices, complex, tuple, set, or object, "
                "declare matching arg_types/return_type. Keep tests JSON-serializable; the judge performs conversion before calling the function."
            ),
            example={
                "starter_code": "import numpy as np\n\ndef solve(A: np.ndarray) -> np.ndarray:\n    pass\n",
                "arg_types": ["numpy.ndarray"],
                "return_type": "numpy.ndarray",
                "visible_tests": [{"name": "basic", "args": [[[1, 0], [0, 1]]], "expected": [[1, 0], [0, 1]]}],
            },
            evidence_patterns=["runtime conversion", "runtime types do not match", "visible function signature match"],
        )

    if "must type-annotate parameter" in text or "must include a return type annotation" in text:
        add_hint(
            code="starter_signature_types",
            problem="The starter_code function signature does not fully describe the input/output types.",
            action=(
                "Add Python type hints to every starter_code parameter and add a return type annotation. "
                "Use clear interface types such as list[int], np.ndarray, torch.Tensor, pd.DataFrame, int, float, str, dict[str,int], tuple[int,int], or object. For non-JSON runtime objects, add arg_types/return_type."
            ),
            example={
                "starter_code": "def solve(nums: list[int], target: int) -> list[int]:\n    pass\n",
            },
            evidence_patterns=["must type-annotate parameter", "must include a return type annotation"],
        )

    if "no module named" in text or "missing dependencies" in text or "name 'np' is not defined" in text or "import_name" in text:
        add_hint(
            code="dependency_or_import_missing",
            problem="A required package or import is missing from the problem definition/code.",
            action=(
                "Add a package object to requirements and include the matching import in starter_code and reference_solution. "
                "Use JSON-serializable test values; set arg_types/return_type or convert to arrays/tensors inside the code."
            ),
            example={
                "requirements": [{"package": "numpy", "pip": "numpy>=2.0", "import_name": "numpy"}],
                "starter_code": "import numpy as np\n\ndef solve(x: list[float]) -> list[float]:\n    pass\n",
            },
            evidence_patterns=["no module named", "missing dependencies", "np is not defined", "import_name"],
        )

    if "problem(s), expected" in text or "returned" in text and "expected" in text and "problem" in text:
        add_hint(
            code="wrong_problem_count",
            problem="The model returned the wrong number of problems.",
            action="Return exactly the requested number of problem objects inside {\"problems\": [...]}.",
            example={"problems": ["exactly_one_problem_object_when_count_is_1"]},
            evidence_patterns=["problem(s), expected", "returned", "expected"],
        )

    if "edited problem id must stay" in text or "changed the problem id" in text:
        add_hint(
            code="problem_id_changed",
            problem="The edit changed the existing problem id.",
            action="Keep the original id when editing an existing problem; only modify requested fields.",
            evidence_patterns=["edited problem id", "changed the problem id"],
        )

    if "already exists" in text or "duplicate problem id" in text:
        add_hint(
            code="duplicate_problem_id",
            problem="The problem id conflicts with another problem.",
            action="Choose a unique snake_case id, or enable overwrite if you intentionally want to replace the existing problem.",
            evidence_patterns=["already exists", "duplicate problem id"],
        )

    if not hints:
        add_hint(
            code="generic_verifier_fix",
            problem="The draft failed deterministic validation.",
            action="Fix the listed verifier errors directly, preserve valid normalized fields, and return only the JSON envelope.",
            evidence_patterns=[],
        )

    return {
        "schema_version": 1,
        "summary": "Use these hints as the checklist for the next draft. Return only the repaired problem JSON.",
        "raw_error_count": len(errors),
        "raw_warning_count": len(warnings),
        "hints": hints,
    }


def _repair_hint_evidence(messages: list[str], patterns: list[str], limit: int = 3) -> list[str]:
    if not patterns:
        return messages[:limit]
    lowered_patterns = [pattern.lower() for pattern in patterns]
    evidence: list[str] = []
    for message in messages:
        lower_message = message.lower()
        if any(pattern in lower_message for pattern in lowered_patterns):
            evidence.append(message)
        if len(evidence) >= limit:
            break
    return evidence


def _reference_mismatch_suggestions(messages: list[str], limit: int = 8) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    marker = "reference_solution output mismatch on "
    for message in messages:
        if marker not in message:
            continue
        tail = message.split(marker, 1)[1]
        label, found, rest = tail.partition(": expected ")
        if not found:
            continue
        expected_text, found, actual_text = rest.rpartition(", actual ")
        if not found:
            continue
        actual_text = actual_text.rstrip(".")
        suggestion = {
            "test": label.strip(),
            "current_expected": _parse_hint_json_value(expected_text.strip()),
            "actual_from_reference": _parse_hint_json_value(actual_text.strip()),
            "action": "Set this test's expected field to actual_from_reference, unless the reference_solution is wrong.",
        }
        suggestions.append(suggestion)
        if len(suggestions) >= limit:
            break
    return suggestions


def _parse_hint_json_value(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


