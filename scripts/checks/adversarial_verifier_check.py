from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mnemosyne.problem_authoring import PROBLEM_TEMPLATE, parse_problem_collection, validate_problem_collection


@dataclass
class Case:
    name: str
    content: str
    should_pass: bool
    expected_warnings: tuple[str, ...] = ()
    expected_errors: tuple[str, ...] = ()


def main() -> int:
    cases = build_cases()
    failures = 0
    for case in cases:
        try:
            detail = run_case(case)
            print(f"PASS {case.name}: {detail}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {case.name}: {exc}")
    print(f"\nSummary: {len(cases) - failures}/{len(cases)} adversarial cases passed")
    return 1 if failures else 0


def run_case(case: Case) -> str:
    parse_warnings: list[str] = []
    try:
        problems = parse_problem_collection(case.content, warnings=parse_warnings)
    except ValueError as exc:
        assert not case.should_pass, f"unexpected parse failure: {exc}"
        joined = str(exc)
        for expected in case.expected_errors:
            assert expected in joined, f"missing parse error `{expected}` in {joined}"
        return "rejected at parse"

    validation = validate_problem_collection(problems)
    warnings = parse_warnings + validation["warnings"]
    errors = validation["errors"]
    if case.should_pass:
        assert validation["ok"], {"errors": errors, "warnings": warnings}
    else:
        assert not validation["ok"], "case unexpectedly passed"

    joined_warnings = "\n".join(warnings)
    joined_errors = "\n".join(errors)
    for expected in case.expected_warnings:
        assert expected in joined_warnings, f"missing warning `{expected}` in {joined_warnings}"
    for expected in case.expected_errors:
        assert expected in joined_errors, f"missing error `{expected}` in {joined_errors}"
    status = "accepted" if validation["ok"] else "rejected"
    return f"{status}, warnings={len(warnings)}, errors={len(errors)}"


def build_cases() -> list[Case]:
    return [
        Case(
            name="smart_quotes_and_fenced_json",
            content="```json\n" + json.dumps(valid_sum_problem()).replace('"', "“") + "\n```",
            should_pass=True,
            expected_warnings=("Converted smart double quotes",),
        ),
        Case(
            name="input_output_aliases",
            content=json.dumps(problem_with_input_output_aliases()),
            should_pass=True,
            expected_warnings=("Converted visible_tests[0].input to args", "Converted visible_tests[0].output to expected"),
        ),
        Case(
            name="single_arg_raw_args_list",
            content=json.dumps(problem_with_raw_single_arg_list()),
            should_pass=True,
            expected_warnings=("Wrapped visible_tests[0].args as one positional list argument",),
        ),
        Case(
            name="instruction_requirements_to_constraints",
            content=json.dumps(problem_with_instruction_requirements()),
            should_pass=True,
            expected_warnings=("Moved 2 instruction-like requirements to constraints",),
        ),
        Case(
            name="numpy_imports_and_allclose",
            content=json.dumps(problem_with_numpy_missing_imports()),
            should_pass=True,
            expected_warnings=("Inferred package requirement(s): numpy", "Added missing package import"),
        ),
        Case(
            name="group_anagrams_order_independent",
            content=json.dumps(problem_group_anagrams_order_variant()),
            should_pass=True,
            expected_warnings=("Inferred checker unordered_nested",),
        ),
        Case(
            name="ndarray_annotation_missing_runtime_contract_rejected",
            content=json.dumps(problem_with_ndarray_annotation_missing_runtime_contract()),
            should_pass=False,
            expected_errors=("arg_types[0] must declare the runtime conversion", "return_type must declare the runtime conversion"),
        ),
        Case(
            name="ndarray_annotation_mismatched_runtime_contract_rejected",
            content=json.dumps(problem_with_ndarray_annotation_mismatched_runtime_contract()),
            should_pass=False,
            expected_errors=("These runtime types do not match",),
        ),
        Case(
            name="empty_test_objects_rejected",
            content=json.dumps(problem_with_empty_tests()),
            should_pass=False,
            expected_errors=("visible_tests[0].args must be a list", "visible_tests[0].expected is required"),
        ),
        Case(
            name="bad_expected_corrected",
            content=json.dumps(problem_with_bad_expected()),
            should_pass=True,
            expected_warnings=("Corrected expected output from reference_solution",),
        ),
        Case(
            name="mismatched_function_name_rejected",
            content=json.dumps(problem_with_mismatched_function_name()),
            should_pass=False,
            expected_errors=("starter_code must define function `expected_name`",),
        ),
        Case(
            name="batch_mixed_repairs",
            content=json.dumps([problem_with_input_output_aliases("batch_aliases"), problem_group_anagrams_order_variant("batch_anagrams")]),
            should_pass=True,
            expected_warnings=("Converted visible_tests[0].input to args", "Inferred checker unordered_nested"),
        ),
    ]


def valid_sum_problem(problem_id: str = "adv_sum_values") -> dict[str, Any]:
    problem = copy.deepcopy(PROBLEM_TEMPLATE)
    problem["id"] = problem_id
    problem["title"] = "Sum Values"
    problem["function_name"] = "sum_values"
    problem["tags"] = ["python", "array"]
    problem["statement"] = (
        "Return the sum of `nums`.\n\n"
        "## Input / Output\n\n"
        "- `nums`: `list[int]`, the numbers to add.\n"
        "- Return: `int`, the sum of all values."
    )
    problem["starter_code"] = "def sum_values(nums: list[int]) -> int:\n    pass\n"
    problem["reference_solution"] = "def sum_values(nums):\n    return sum(nums)\n"
    problem["visible_tests"] = [{"name": "basic", "args": [[1, 2, 3]], "expected": 6}]
    problem["hidden_tests"] = [{"name": "empty", "args": [[]], "expected": 0}]
    return problem

def problem_with_input_output_aliases(problem_id: str = "adv_input_output_aliases") -> dict[str, Any]:
    problem = valid_sum_problem(problem_id)
    problem["visible_tests"] = [{"name": "alias", "input": [1, 2, 3], "output": 6}]
    problem["hidden_tests"] = [{"name": "hidden alias", "inputs": [], "result": 0}]
    return problem


def problem_with_raw_single_arg_list(problem_id: str = "adv_raw_args_list") -> dict[str, Any]:
    problem = valid_sum_problem(problem_id)
    problem["visible_tests"] = [{"name": "raw", "args": [1, 2, 3], "expected": 6}]
    return problem


def problem_with_instruction_requirements(problem_id: str = "adv_instruction_requirements") -> dict[str, Any]:
    problem = valid_sum_problem(problem_id)
    problem["requirements"] = ["Do not modify the input list.", "Return 0 for an empty list."]
    problem["constraints"] = []
    return problem


def problem_with_numpy_missing_imports(problem_id: str = "adv_numpy_missing_imports") -> dict[str, Any]:
    problem = valid_sum_problem(problem_id)
    problem["title"] = "Scale Vector"
    problem["function_name"] = "scale_vector"
    problem["tags"] = ["python", "numpy"]
    problem["requirements"] = []
    problem["statement"] = (
        "Return vector `x` multiplied by scalar `a`.\n\n"
        "## Input / Output\n\n"
        "- `x`: `list[float]`, the input vector.\n"
        "- `a`: `float`, the scale factor.\n"
        "- Return: `list[float]`, the scaled values."
    )
    problem["starter_code"] = "def scale_vector(x: list[float], a: float) -> list[float]:\n    pass\n"
    problem["reference_solution"] = "def scale_vector(x, a):\n    return np.asarray(x, dtype=float) * a\n"
    problem["visible_tests"] = [{"name": "basic", "args": [[1, 2], 2], "expected": [2.0, 4.0]}]
    problem["hidden_tests"] = [{"name": "half", "args": [[-1, 4], 0.5], "expected": [-0.5, 2.0]}]
    return problem

def problem_group_anagrams_order_variant(problem_id: str = "adv_group_anagrams") -> dict[str, Any]:
    problem = valid_sum_problem(problem_id)
    problem.pop("checker", None)
    problem["title"] = "Group Anagrams"
    problem["function_name"] = "group_anagrams"
    problem["tags"] = ["python", "hashmap", "anagram"]
    problem["statement"] = (
        "Group the words in `strs` by anagram class and return the groups. The group order does not matter.\n\n"
        "## Input / Output\n\n"
        "- `strs`: `list[str]`, the words to group.\n"
        "- Return: `list[list[str]]`, grouped anagrams."
    )
    problem["starter_code"] = "def group_anagrams(strs: list[str]) -> list[list[str]]:\n    pass\n"
    problem["reference_solution"] = (
        "def group_anagrams(strs):\n"
        "    groups = {}\n"
        "    for word in strs:\n"
        "        groups.setdefault(''.join(sorted(word)), []).append(word)\n"
        "    return list(groups.values())\n"
    )
    problem["visible_tests"] = [
        {
            "name": "basic",
            "args": [["eat", "tea", "tan", "ate", "nat", "bat"]],
            "expected": [["bat"], ["nat", "tan"], ["ate", "eat", "tea"]],
        }
    ]
    problem["hidden_tests"] = [
        {"name": "same", "args": [["listen", "silent", "enlist"]], "expected": [["enlist", "silent", "listen"]]},
    ]
    return problem

def problem_with_ndarray_annotation_missing_runtime_contract(problem_id: str = "adv_ndarray_missing_runtime_contract") -> dict[str, Any]:
    problem = valid_sum_problem(problem_id)
    problem["title"] = "Scale NumPy Vector"
    problem["function_name"] = "scale_vector"
    problem["tags"] = ["python", "numpy"]
    problem["requirements"] = [{"package": "numpy", "pip": "numpy>=2.0", "import_name": "numpy"}]
    problem["checker"] = {"type": "allclose", "atol": 1e-5, "rtol": 1e-5}
    problem["statement"] = (
        "Return vector $x$ multiplied by $2$.\n\n"
        "## Input / Output\n\n"
        "- `x`: `numpy.ndarray`, the input vector.\n"
        "- Return: `numpy.ndarray`, the scaled vector."
    )
    problem["starter_code"] = "import numpy as np\n\ndef scale_vector(x: np.ndarray) -> np.ndarray:\n    pass\n"
    problem["reference_solution"] = "import numpy as np\n\ndef scale_vector(x):\n    return np.asarray(x, dtype=float) * 2\n"
    problem["visible_tests"] = [{"name": "basic", "args": [[1, 2]], "expected": [2.0, 4.0]}]
    problem["hidden_tests"] = []
    problem.pop("arg_types", None)
    problem.pop("return_type", None)
    return problem


def problem_with_ndarray_annotation_mismatched_runtime_contract(problem_id: str = "adv_ndarray_mismatch_runtime_contract") -> dict[str, Any]:
    problem = problem_with_ndarray_annotation_missing_runtime_contract(problem_id)
    problem["arg_types"] = ["list"]
    problem["return_type"] = "list"
    return problem


def problem_with_empty_tests(problem_id: str = "adv_empty_tests") -> dict[str, Any]:
    problem = valid_sum_problem(problem_id)
    problem["visible_tests"] = [{}, {}]
    problem["hidden_tests"] = [{}]
    return problem


def problem_with_bad_expected(problem_id: str = "adv_bad_expected") -> dict[str, Any]:
    problem = valid_sum_problem(problem_id)
    problem["visible_tests"] = [{"name": "bad", "args": [[1, 2, 3]], "expected": 999}]
    return problem


def problem_with_mismatched_function_name(problem_id: str = "adv_mismatch_function") -> dict[str, Any]:
    problem = valid_sum_problem(problem_id)
    problem["function_name"] = "expected_name"
    problem["starter_code"] = "def wrong_name(nums: list[int]) -> int:\n    pass\n"
    problem["reference_solution"] = "def wrong_name(nums):\n    return sum(nums)\n"
    return problem


if __name__ == "__main__":
    raise SystemExit(main())
