from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mnemosyne import problem_authoring
from mnemosyne.api import routes as api_routes
from mnemosyne.api.schemas import SaveProblemRequest
from mnemosyne.storage import problems as problem_store
from mnemosyne.runtime.judge import judge_code
from mnemosyne.problem_authoring import format_problem_json, validate_problem_spec

CHECKS_RUN = 0
FAILURES: list[str] = []


def check(name: str, condition: bool, detail: Any = "") -> None:
    global CHECKS_RUN
    CHECKS_RUN += 1
    if condition:
        print(f"PASS {CHECKS_RUN:03d} {name}")
        return
    message = f"FAIL {CHECKS_RUN:03d} {name}"
    if detail:
        message += f": {detail}"
    print(message)
    FAILURES.append(message)


def make_problem(idx: int) -> dict[str, Any]:
    variant = idx % 4
    fn = f"managed_flow_{idx}"
    base = {
        "id": fn,
        "title": f"Managed Flow Problem {idx}",
        "difficulty": ["easy", "medium", "hard", "easy"][variant],
        "entry_kind": "function",
        "function_name": fn,
        "tags": ["python", "manage-flow", f"variant-{variant}"],
        "requirements": [],
        "constraints": ["This temporary problem is generated for Manage flow regression testing."],
        "checker": {"type": "exact"},
        "timeout_seconds": 3,
        "theory": f"## Theory\n\nTemporary theory block for problem `{idx}`.",
        "examples": [{"name": "Worked example", "body": f"Run the function once and compare the returned value for `{idx}`."}],
        "solution_explanation": "Use the direct transformation described in the statement.",
        "complexity": {"time": "O(n)", "space": "O(1)"},
        "hidden_tests": [],
    }
    if variant == 0:
        base.update({
            "statement": f"# Add Offset\n\nReturn `x + {idx}`.\n\n## Input / Output\n\n- `x`: `int`\n- Return: `int`",
            "starter_code": f"def {fn}(x: int) -> int:\n    pass\n",
            "reference_solution": f"def {fn}(x: int) -> int:\n    return x + {idx}\n",
            "visible_tests": [
                {"name": "positive", "args": [2], "expected": 2 + idx},
                {"name": "negative", "args": [-3], "expected": -3 + idx},
            ],
        })
    elif variant == 1:
        base.update({
            "statement": f"# Sum With Offset\n\nReturn `sum(nums) + {idx}`.\n\n## Input / Output\n\n- `nums`: `list[int]`\n- Return: `int`",
            "starter_code": f"def {fn}(nums: list[int]) -> int:\n    pass\n",
            "reference_solution": f"def {fn}(nums: list[int]) -> int:\n    return sum(nums) + {idx}\n",
            "visible_tests": [
                {"name": "small list", "args": [[1, 2, 3]], "expected": 6 + idx},
                {"name": "empty list", "args": [[]], "expected": idx},
            ],
        })
    elif variant == 2:
        base.update({
            "statement": "# Reverse Text\n\nReturn the reversed text plus a suffix marker.\n\n## Input / Output\n\n- `text`: `str`\n- Return: `str`",
            "starter_code": f"def {fn}(text: str) -> str:\n    pass\n",
            "reference_solution": f"def {fn}(text: str) -> str:\n    return text[::-1] + '-{idx}'\n",
            "visible_tests": [
                {"name": "abc", "args": ["abc"], "expected": f"cba-{idx}"},
                {"name": "single", "args": ["z"], "expected": f"z-{idx}"},
            ],
        })
    else:
        base.update({
            "statement": "# Count Items\n\nReturn a frequency dictionary.\n\n## Input / Output\n\n- `items`: `list[str]`\n- Return: `dict[str, int]`",
            "starter_code": f"def {fn}(items: list[str]) -> dict[str, int]:\n    pass\n",
            "reference_solution": f"def {fn}(items: list[str]) -> dict[str, int]:\n    counts = {{}}\n    for item in items:\n        counts[item] = counts.get(item, 0) + 1\n    return counts\n",
            "visible_tests": [
                {"name": "duplicates", "args": [["a", "b", "a"]], "expected": {"a": 2, "b": 1}},
                {"name": "empty", "args": [[]], "expected": {}},
            ],
        })
    return base


def mutate_like_manage(problem: dict[str, Any], idx: int) -> dict[str, Any]:
    edited = dict(problem)
    edited["statement"] = problem["statement"] + f"\n\nManaged edit marker `{idx}`."
    edited["theory"] = f"## Managed Theory\n\nThe Manage editor updated theory for `{idx}`."
    edited["examples"] = [{"name": "Managed walkthrough", "body": f"Step through temporary case `{idx}`."}]
    edited["solution_explanation"] = f"Managed solution explanation for `{idx}`."
    edited["complexity"] = {"time": f"O(n + {idx})", "space": "O(1)"}
    edited["tags"] = list(dict.fromkeys([*problem.get("tags", []), "managed-edited"]))
    edited.setdefault("visible_tests", []).append(problem["visible_tests"][0] | {"name": "managed copied case"})
    return edited


def main_check() -> int:
    original_store_dir = problem_store.PROBLEMS_DIR
    original_author_dir = problem_authoring.PROBLEMS_DIR
    temp_root = Path(tempfile.mkdtemp(prefix="mnemosyne_manage_flow_", dir="/private/tmp"))
    try:
        problem_store.PROBLEMS_DIR = temp_root
        problem_authoring.PROBLEMS_DIR = temp_root
        temp_root.mkdir(parents=True, exist_ok=True)

        for idx in range(40):
            spec = make_problem(idx)
            validation = validate_problem_spec(spec)
            check(f"problem {idx}: initial verifier accepts", validation["ok"], validation.get("errors"))
            problem_store.save_problem(validation["problem"])

            problem_id = spec["id"]
            raw = api_routes.api_get_problem_raw(problem_id)["problem"]
            check(f"problem {idx}: Manage raw includes reference solution", bool(raw.get("reference_solution")))
            check(f"problem {idx}: Manage raw includes complexity", raw.get("complexity", {}).get("time") == "O(n)")

            edited = mutate_like_manage(raw, idx)
            first_test = edited["visible_tests"][0]
            if isinstance(first_test.get("args"), list):
                if idx % 4 == 0:
                    first_test["args"] = [5]
                elif idx % 4 == 1:
                    first_test["args"] = [[4, 5]]
                elif idx % 4 == 2:
                    first_test["args"] = ["flow"]
                else:
                    first_test["args"] = [["x", "x", "y"]]
                first_test["expected"] = "stale-output"
            content = format_problem_json(edited)
            saved = api_routes.api_update_problem(problem_id, SaveProblemRequest(content=content))
            check(f"problem {idx}: Manage save succeeds", saved.get("ok") and saved.get("saved"), saved.get("errors"))
            saved_problem = saved.get("problem") or {}
            corrected_expected = saved_problem.get("visible_tests", [{}])[0].get("expected")
            check(f"problem {idx}: stale expected output is corrected", corrected_expected != "stale-output", corrected_expected)

            public = api_routes.api_get_problem(problem_id)
            check(f"problem {idx}: Practice sees edited statement", f"Managed edit marker `{idx}`" in public.get("statement", ""))
            check(f"problem {idx}: Practice sees edited theory", "Managed Theory" in public.get("theory", ""))
            check(f"problem {idx}: Practice sees edited examples", public.get("examples", [{}])[0].get("name") == "Managed walkthrough")
            check(f"problem {idx}: Practice public hides solution", "reference_solution" not in public and "solution_explanation" not in public)

            solution = api_routes.api_get_problem_solution(problem_id)
            check(f"problem {idx}: Solution API sees edited explanation", solution.get("explanation") == f"Managed solution explanation for `{idx}`.")
            check(f"problem {idx}: Solution API sees edited complexity", solution.get("complexity", {}).get("time") == f"O(n + {idx})")
            check(f"problem {idx}: Solution API sees reference code", f"def managed_flow_{idx}" in solution.get("solution", ""))

            accepted = judge_code(problem_store.get_problem(problem_id), solution["solution"], "submit").as_dict()
            check(f"problem {idx}: edited reference solution passes explicit tests", accepted.get("status") == "Accepted", accepted)

        check("40 temporary Manage flow problems exercised", CHECKS_RUN >= 40 * 11, CHECKS_RUN)
    finally:
        problem_store.PROBLEMS_DIR = original_store_dir
        problem_authoring.PROBLEMS_DIR = original_author_dir
        shutil.rmtree(temp_root, ignore_errors=True)

    print(f"\nSummary: {CHECKS_RUN - len(FAILURES)}/{CHECKS_RUN} Manage flow checks passed")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main_check())
