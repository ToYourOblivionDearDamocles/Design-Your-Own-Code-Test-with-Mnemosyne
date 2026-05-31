from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app.database as database
import app.llm_authoring as llm_authoring
import app.problem_authoring as problem_authoring
import app.problem_store as problem_store
from app import main


Scenario = Callable[[], str]


def main_runner() -> int:
    with tempfile.TemporaryDirectory(prefix="mnemosyne_acceptance_") as tmp:
        temp_root = Path(tmp)
        configure_temp_app(temp_root)
        database.init_db()

        scenarios: list[tuple[str, Scenario]] = [
            ("01 create function problem, solve accepted, wrong answer saved", scenario_function_submission_history),
            ("02 create markdown/math problem and hide private fields", scenario_markdown_public_problem),
            ("03 create nested-list matrix problem and filter by tag", scenario_matrix_tag_filter),
            ("04 create unit_tests OOP problem and judge stateful behavior", scenario_unit_tests_oop),
            ("05 repair LLM numpy schema mistakes and judge allclose", scenario_numpy_auto_repair),
            ("06 accept fenced JSON with smart quotes and surrounding prose", scenario_fenced_smart_quotes),
            ("07 duplicate-create protection and overwrite", scenario_duplicate_overwrite),
            ("08 tag index shows problem counts across categories", scenario_tag_index_counts),
            ("09 edit/add testcase while preserving problem id", scenario_manage_problem_tests),
            ("10 delete problem and remove it from tag views", scenario_delete_problem),
            ("11 add tests across several problem types", scenario_add_tests_across_problem_types),
            ("12 create multiple problems from one JSON array", scenario_batch_create_problems),
            ("13 correct reference/expected mismatches", scenario_reference_expected_verification),
            ("14 LLM problem draft loop repairs verifier failures", scenario_llm_problem_draft_loop),
            ("15 LLM test draft computes expected outputs", scenario_llm_test_drafts),
            ("16 LLM count generates problems sequentially", scenario_llm_sequential_count),
            ("17 draft dependency install collects inferred packages", scenario_draft_dependency_install),
            ("18 LLM text attachments become source context", scenario_llm_text_attachments),
        ]

        failures = 0
        print(f"Temporary problem bank: {problem_store.PROBLEMS_DIR}")
        for title, fn in scenarios:
            try:
                detail = fn()
                print(f"PASS {title}: {detail}")
            except Exception as exc:  # noqa: BLE001 - acceptance report should keep going.
                failures += 1
                print(f"FAIL {title}: {exc}")

        return 1 if failures else 0


def configure_temp_app(temp_root: Path) -> None:
    problems_dir = temp_root / "problems"
    data_dir = temp_root / "data"
    problems_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    problem_store.PROBLEMS_DIR = problems_dir
    problem_authoring.PROBLEMS_DIR = problems_dir
    database.DATA_DIR = data_dir
    database.DB_PATH = data_dir / "mnemosyne.sqlite3"


def scenario_function_submission_history() -> str:
    problem = {
        "id": "acceptance_sum_even",
        "title": "Sum Even Numbers",
        "difficulty": "easy",
        "entry_kind": "function",
        "function_name": "sum_even",
        "tags": ["python", "array", "filtering"],
        "requirements": [],
        "constraints": ["Return 0 when no value is even."],
        "checker": {"type": "exact"},
        "timeout_seconds": 3,
        "statement": "# Sum Even Numbers\n\nReturn the sum of even integers in `nums`.",
        "starter_code": "def sum_even(nums: list[int]) -> int:\n    pass\n",
        "reference_solution": "def sum_even(nums):\n    return sum(x for x in nums if x % 2 == 0)\n",
        "solution_explanation": "Filter even values, then sum them.",
        "complexity": {"time": "O(n)", "space": "O(1)"},
        "visible_tests": [
            {"name": "mixed", "args": [[1, 2, 3, 4]], "expected": 6},
            {"name": "none", "args": [[1, 3, 5]], "expected": 0},
        ],
        "hidden_tests": [{"name": "negative", "args": [[-2, 7, 10]], "expected": 8}],
    }
    created = create(problem)
    assert created["created"], created

    accepted = main.api_submit(main.SubmitRequest(problem_id=problem["id"], code=problem["reference_solution"], mode="submit"))
    assert accepted["status"] == "Accepted", accepted

    wrong_code = "def sum_even(nums):\n    return sum(nums)\n"
    wrong = main.api_submit(main.SubmitRequest(problem_id=problem["id"], code=wrong_code, mode="run"))
    assert wrong["status"] == "Wrong Answer", wrong

    wrong_problems = main.api_wrong_problems()["wrong_problems"]
    row = find_by(wrong_problems, "problem_id", problem["id"])
    assert row["wrong_count"] == 1, wrong_problems
    assert row["latest_status"] == "Wrong Answer", row
    return "accepted submit, wrong run, wrong-problem history recorded"


def scenario_markdown_public_problem() -> str:
    problem = {
        "id": "acceptance_geometric_sum",
        "title": "Geometric Sum",
        "difficulty": "easy",
        "entry_kind": "function",
        "function_name": "geometric_sum",
        "tags": ["python", "math", "series"],
        "requirements": [],
        "constraints": ["Use exactly n terms."],
        "checker": {"type": "allclose", "atol": 1e-9, "rtol": 1e-9},
        "timeout_seconds": 3,
        "statement": "# Geometric Sum\n\nCompute\n\n$$\n\\sum_{i=0}^{n-1} ar^i\n$$",
        "starter_code": "def geometric_sum(a: float, r: float, n: int) -> float:\n    pass\n",
        "reference_solution": "def geometric_sum(a, r, n):\n    total = 0.0\n    term = float(a)\n    for _ in range(n):\n        total += term\n        term *= r\n    return total\n",
        "solution_explanation": "Accumulate each term iteratively.",
        "complexity": {"time": "O(n)", "space": "O(1)"},
        "visible_tests": [{"name": "three terms", "args": [2, 3, 3], "expected": 26.0}],
        "hidden_tests": [{"name": "fractional", "args": [1, 0.5, 4], "expected": 1.875}],
    }
    create(problem)
    public = main.api_get_problem(problem["id"])
    assert "$$" in public["statement"], public
    assert "hidden_tests" not in public, public
    assert "reference_solution" not in public, public
    solution = main.api_get_problem_solution(problem["id"])
    assert "reference_solution" not in solution, solution
    assert solution["solution"].startswith("def geometric_sum"), solution
    return "markdown math survives public API, private fields hidden"


def scenario_matrix_tag_filter() -> str:
    problem = {
        "id": "acceptance_matrix_transpose",
        "title": "Matrix Transpose",
        "difficulty": "easy",
        "entry_kind": "function",
        "function_name": "transpose",
        "tags": ["python", "matrix", "array"],
        "requirements": [],
        "constraints": ["Return a new matrix."],
        "checker": {"type": "exact"},
        "timeout_seconds": 3,
        "statement": "Return the transpose of a rectangular matrix.",
        "starter_code": "def transpose(matrix: list[list[int]]) -> list[list[int]]:\n    pass\n",
        "reference_solution": "def transpose(matrix):\n    return [list(row) for row in zip(*matrix)]\n",
        "solution_explanation": "Columns become rows.",
        "complexity": {"time": "O(mn)", "space": "O(mn)"},
        "visible_tests": [{"name": "2 by 3", "args": [[[1, 2, 3], [4, 5, 6]]], "expected": [[1, 4], [2, 5], [3, 6]]}],
        "hidden_tests": [{"name": "single row", "args": [[[7, 8]]], "expected": [[7], [8]]}],
    }
    create(problem)
    result = main.api_submit(main.SubmitRequest(problem_id=problem["id"], code=problem["reference_solution"], mode="submit"))
    assert result["status"] == "Accepted", result
    matrix_problems = main.api_list_problems(tag="matrix")["problems"]
    assert find_by(matrix_problems, "id", problem["id"]), matrix_problems
    return "nested-list judge path and tag filter"


def scenario_unit_tests_oop() -> str:
    problem = {
        "id": "acceptance_stack_class",
        "title": "Stack Class",
        "difficulty": "medium",
        "entry_kind": "unit_tests",
        "tags": ["python", "oop", "class", "state"],
        "requirements": [],
        "constraints": ["Each instance owns independent stack state."],
        "checker": {"type": "exact"},
        "timeout_seconds": 3,
        "statement": "Implement a `Stack` class with `push`, `pop`, and `peek`.",
        "starter_code": "class Stack:\n    pass\n",
        "reference_solution": "class Stack:\n    def __init__(self):\n        self.items = []\n    def push(self, value):\n        self.items.append(value)\n    def pop(self):\n        return self.items.pop()\n    def peek(self):\n        return self.items[-1]\n",
        "solution_explanation": "Use a list as backing storage.",
        "complexity": {"time": "O(1) per operation", "space": "O(n)"},
        "visible_tests": [
            {"name": "push peek", "code": "from user_solution import Stack\ns = Stack()\ns.push(3)\nassert s.peek() == 3"}
        ],
        "hidden_tests": [
            {"name": "separate instances", "code": "from user_solution import Stack\na = Stack(); b = Stack()\na.push(1); b.push(2)\nassert a.pop() == 1\nassert b.peek() == 2"}
        ],
    }
    result = main.api_authoring_validate(main.AuthorProblemRequest(content=json.dumps(problem)))
    assert result["ok"], result
    create(problem)
    accepted = main.api_submit(main.SubmitRequest(problem_id=problem["id"], code=problem["reference_solution"], mode="submit"))
    assert accepted["status"] == "Accepted", accepted
    wrong = main.api_submit(main.SubmitRequest(problem_id=problem["id"], code="class Stack:\n    pass\n", mode="run"))
    assert wrong["status"] == "Wrong Answer", wrong
    return "unit_tests creation works without function_name"


def scenario_numpy_auto_repair() -> str:
    problem = {
        "id": "acceptance_numpy_l2_normalize",
        "title": "L2 Normalize",
        "difficulty": "medium",
        "entry_kind": "function",
        "function_name": "l2_normalize",
        "tags": ["python", "numpy", "linear_algebra"],
        "requirements": [
            "Convert the input to a floating NumPy array.",
            "Return zeros when the norm is zero.",
        ],
        "timeout_seconds": 3,
        "statement": "Return `x / ||x||_2`.",
        "starter_code": "import numpy as np\n\ndef l2_normalize(x: list[float]) -> list[float]:\n    pass\n",
        "reference_solution": "import numpy as np\n\ndef l2_normalize(x):\n    x = np.asarray(x, dtype=float)\n    norm = np.linalg.norm(x)\n    if norm == 0:\n        return np.zeros_like(x)\n    return x / norm\n",
        "solution_explanation": "Divide by Euclidean norm unless it is zero.",
        "complexity": {"time": "O(n)", "space": "O(n)"},
        "visible_tests": [{"name": "3-4-5", "args": [[3, 4]], "expected": [0.6, 0.8]}],
        "hidden_tests": [{"name": "zero", "args": [[0, 0]], "expected": [0.0, 0.0]}],
    }
    validation = main.api_authoring_validate(main.AuthorProblemRequest(content=json.dumps(problem)))
    assert validation["ok"], validation
    fixed = validation["problem"]
    assert fixed["requirements"] == [{"package": "numpy", "pip": "numpy>=2.0", "import_name": "numpy"}], fixed
    assert fixed["checker"]["type"] == "allclose", fixed
    assert len(fixed["constraints"]) == 2, fixed
    create(fixed)
    accepted = main.api_submit(main.SubmitRequest(problem_id=problem["id"], code=fixed["reference_solution"], mode="submit"))
    assert accepted["status"] in {"Accepted", "Missing Dependencies"}, accepted
    return f"auto repair warnings={len(validation['warnings'])}, judge={accepted['status']}"


def scenario_fenced_smart_quotes() -> str:
    problem = {
        "id": "acceptance_smart_quote_json",
        "title": "Smart Quote JSON",
        "difficulty": "easy",
        "entry_kind": "function",
        "function_name": "double_value",
        "tags": ["python", "parsing"],
        "requirements": [],
        "constraints": [],
        "checker": {"type": "exact"},
        "timeout_seconds": 3,
        "statement": "Return `x * 2`.",
        "starter_code": "def double_value(x: int) -> int:\n    pass\n",
        "reference_solution": "def double_value(x):\n    return x * 2\n",
        "solution_explanation": "Multiply by two.",
        "complexity": {"time": "O(1)", "space": "O(1)"},
        "visible_tests": [{"name": "basic", "args": [4], "expected": 8}],
        "hidden_tests": [{"name": "negative", "args": [-3], "expected": -6}],
    }
    raw = json.dumps(problem, ensure_ascii=False).replace('"', "“")
    content = "Here is the JSON:\n```json\n" + raw + "\n```\nThanks."
    validation = main.api_authoring_validate(main.AuthorProblemRequest(content=content))
    assert validation["ok"], validation
    assert any("Converted smart double quotes" in warning for warning in validation["warnings"]), validation
    create(validation["problem"])
    return "smart quotes, fenced block, and prose repaired"


def scenario_duplicate_overwrite() -> str:
    first = problem_template("acceptance_duplicate", "Duplicate v1", "dup")
    second = problem_template("acceptance_duplicate", "Duplicate v2", "dup")
    created = create(first)
    assert created["created"], created
    duplicate = main.api_authoring_create_problem(main.AuthorProblemRequest(content=json.dumps(second), overwrite=False))
    assert not duplicate["created"], duplicate
    assert "already exists" in duplicate["errors"][0], duplicate
    overwritten = main.api_authoring_create_problem(main.AuthorProblemRequest(content=json.dumps(second), overwrite=True))
    assert overwritten["created"], overwritten
    raw = main.api_get_problem_raw("acceptance_duplicate")["problem"]
    assert raw["title"] == "Duplicate v2", raw
    return "duplicate blocked, overwrite replaces"


def scenario_tag_index_counts() -> str:
    tags = main.api_list_tags()["tags"]
    array = find_by(tags, "tag", "array")
    oop = find_by(tags, "tag", "oop")
    assert array["count"] >= 2, tags
    assert oop["count"] >= 1, tags
    by_oop = main.api_list_problems(tag="oop")["problems"]
    assert all("oop" in problem["tags"] for problem in by_oop), by_oop
    return f"array={array['count']}, oop={oop['count']}"


def scenario_manage_problem_tests() -> str:
    problem = problem_template("acceptance_manage_tests", "Manage Tests", "management")
    create(problem)
    generated = main.api_generate_problem_expected(
        "acceptance_manage_tests",
        main.GenerateExpectedRequest(args=[10]),
    )
    assert generated["ok"], generated
    assert generated["expected"] == 20, generated

    add = main.api_add_generated_problem_test(
        "acceptance_manage_tests",
        main.AddGeneratedTestCaseRequest(
            group="hidden_tests",
            name="large",
            args=[10],
        ),
    )
    assert add["saved"], add
    assert add["test_case"]["expected"] == 20, add
    raw = main.api_get_problem_raw("acceptance_manage_tests")["problem"]
    assert len(raw["hidden_tests"]) == 2, raw

    changed_id = copy.deepcopy(raw)
    changed_id["id"] = "should_not_be_allowed"
    rejected = main.api_update_problem("acceptance_manage_tests", main.SaveProblemRequest(content=json.dumps(changed_id)))
    assert not rejected["saved"], rejected

    raw["difficulty"] = "medium"
    saved = main.api_update_problem("acceptance_manage_tests", main.SaveProblemRequest(content=json.dumps(raw)))
    assert saved["saved"], saved
    assert main.api_get_problem_raw("acceptance_manage_tests")["problem"]["difficulty"] == "medium"
    return "generate expected, add testcase, reject id change, save normal edit"


def scenario_delete_problem() -> str:
    problem = problem_template("acceptance_delete_me", "Delete Me", "temporary")
    create(problem)
    before = main.api_list_problems(tag="temporary")["problems"]
    assert find_by(before, "id", problem["id"]), before
    deleted = main.api_delete_problem(problem["id"])
    assert deleted["deleted"], deleted
    after = main.api_list_problems(tag="temporary")["problems"]
    assert not find_by(after, "id", problem["id"]), after
    return "delete removes problem from catalog/tag view"


def scenario_add_tests_across_problem_types() -> str:
    added: list[str] = []

    one_arg = problem_template("acceptance_add_one_arg", "Add One Arg", "add-test")
    create(one_arg)
    add_generated("acceptance_add_one_arg", "visible_tests", "eleven", [11], 22)
    added.append("single-arg")

    multi_arg = {
        "id": "acceptance_add_multi_arg",
        "title": "Add Multi Arg",
        "difficulty": "easy",
        "entry_kind": "function",
        "function_name": "sum_squares",
        "tags": ["python", "math", "add-test"],
        "requirements": [],
        "constraints": [],
        "checker": {"type": "exact"},
        "timeout_seconds": 3,
        "statement": "Return `a*a + b*b`.",
        "starter_code": "def sum_squares(a: int, b: int) -> int:\n    pass\n",
        "reference_solution": "def sum_squares(a, b):\n    return a * a + b * b\n",
        "solution_explanation": "Square each input.",
        "complexity": {"time": "O(1)", "space": "O(1)"},
        "visible_tests": [{"name": "basic", "args": [3, 4], "expected": 25}],
        "hidden_tests": [{"name": "zero", "args": [0, 5], "expected": 25}],
    }
    create(multi_arg)
    add_generated("acceptance_add_multi_arg", "hidden_tests", "negative", [-2, 5], 29)
    bad = main.api_add_generated_problem_test(
        "acceptance_add_multi_arg",
        main.AddGeneratedTestCaseRequest(group="visible_tests", name="bad arity", args=[3]),
    )
    assert not bad["saved"], bad
    assert any("expects" in error for error in bad["errors"]), bad
    added.append("multi-arg")

    matrix = {
        "id": "acceptance_add_matrix",
        "title": "Add Matrix",
        "difficulty": "easy",
        "entry_kind": "function",
        "function_name": "row_sums",
        "tags": ["python", "matrix", "add-test"],
        "requirements": [],
        "constraints": [],
        "checker": {"type": "exact"},
        "timeout_seconds": 3,
        "statement": "Return the sum of each matrix row.",
        "starter_code": "def row_sums(matrix: list[list[int]]) -> list[int]:\n    pass\n",
        "reference_solution": "def row_sums(matrix):\n    return [sum(row) for row in matrix]\n",
        "solution_explanation": "Sum each row.",
        "complexity": {"time": "O(mn)", "space": "O(m)"},
        "visible_tests": [{"name": "basic", "args": [[[1, 2], [3, 4]]], "expected": [3, 7]}],
        "hidden_tests": [],
    }
    create(matrix)
    add_generated("acceptance_add_matrix", "hidden_tests", "three rows", [[[1, 1], [2, 3], [4, 5]]], [2, 5, 9])
    added.append("matrix")

    floats = {
        "id": "acceptance_add_float",
        "title": "Add Float",
        "difficulty": "easy",
        "entry_kind": "function",
        "function_name": "weighted_average",
        "tags": ["python", "math", "add-test"],
        "requirements": [],
        "constraints": [],
        "checker": {"type": "allclose", "atol": 1e-9, "rtol": 1e-9},
        "timeout_seconds": 3,
        "statement": "Return `(a + 2*b) / 3`.",
        "starter_code": "def weighted_average(a: float, b: float) -> float:\n    pass\n",
        "reference_solution": "def weighted_average(a, b):\n    return (a + 2 * b) / 3\n",
        "solution_explanation": "Compute the weighted average.",
        "complexity": {"time": "O(1)", "space": "O(1)"},
        "visible_tests": [{"name": "basic", "args": [1.0, 4.0], "expected": 3.0}],
        "hidden_tests": [],
    }
    create(floats)
    add_generated("acceptance_add_float", "hidden_tests", "fraction", [1.0, 2.0], 1.6666666666666667)
    added.append("float")

    numpy_problem = {
        "id": "acceptance_add_numpy",
        "title": "Add NumPy",
        "difficulty": "medium",
        "entry_kind": "function",
        "function_name": "scale_array",
        "tags": ["python", "numpy", "add-test"],
        "requirements": [{"package": "numpy", "pip": "numpy>=2.0", "import_name": "numpy"}],
        "constraints": [],
        "checker": {"type": "allclose", "atol": 1e-9, "rtol": 1e-9},
        "timeout_seconds": 3,
        "statement": "Return `x * factor` as a NumPy-compatible array.",
        "starter_code": "import numpy as np\n\ndef scale_array(x: list[float], factor: float) -> list[float]:\n    pass\n",
        "reference_solution": "import numpy as np\n\ndef scale_array(x, factor):\n    return np.asarray(x, dtype=float) * factor\n",
        "solution_explanation": "Convert then multiply.",
        "complexity": {"time": "O(n)", "space": "O(n)"},
        "visible_tests": [{"name": "basic", "args": [[1, 2], 3], "expected": [3.0, 6.0]}],
        "hidden_tests": [],
    }
    create(numpy_problem)
    numpy_add = main.api_add_generated_problem_test(
        "acceptance_add_numpy",
        main.AddGeneratedTestCaseRequest(group="hidden_tests", name="negative factor", args=[[1, -2], -0.5]),
    )
    assert numpy_add["saved"] or "Missing required package" in " ".join(numpy_add.get("errors", [])), numpy_add
    if numpy_add["saved"]:
        assert numpy_add["test_case"]["expected"] == [-0.5, 1.0], numpy_add
    added.append("numpy" if numpy_add["saved"] else "numpy-missing-dependency")

    unit_problem = {
        "id": "acceptance_add_unit_test",
        "title": "Add Unit Test",
        "difficulty": "easy",
        "entry_kind": "unit_tests",
        "tags": ["python", "oop", "add-test"],
        "requirements": [],
        "constraints": [],
        "checker": {"type": "exact"},
        "timeout_seconds": 3,
        "statement": "Implement `Box` with `get`.",
        "starter_code": "class Box:\n    pass\n",
        "reference_solution": "class Box:\n    def __init__(self, value):\n        self.value = value\n    def get(self):\n        return self.value\n",
        "solution_explanation": "Store value.",
        "complexity": {"time": "O(1)", "space": "O(1)"},
        "visible_tests": [{"name": "basic", "code": "from user_solution import Box\nassert Box(3).get() == 3"}],
        "hidden_tests": [],
    }
    create(unit_problem)
    unit_add = main.api_add_problem_test(
        "acceptance_add_unit_test",
        main.AddTestCaseRequest(
            group="hidden_tests",
            test_case={"name": "string", "code": "from user_solution import Box\nassert Box('x').get() == 'x'"},
        ),
    )
    assert unit_add["saved"], unit_add
    unit_result = main.api_submit(
        main.SubmitRequest(problem_id="acceptance_add_unit_test", code=unit_problem["reference_solution"], mode="submit")
    )
    assert unit_result["status"] == "Accepted", unit_result
    added.append("unit-tests")

    tagged = main.api_list_problems(tag="add-test")["problems"]
    assert len(tagged) >= 6, tagged
    return ", ".join(added)


def scenario_batch_create_problems() -> str:
    first = problem_template("acceptance_batch_one", "Batch One", "batch")
    second = {
        "id": "acceptance_batch_two",
        "title": "Batch Two",
        "difficulty": "easy",
        "entry_kind": "function",
        "function_name": "triple_value",
        "tags": ["python", "batch"],
        "requirements": [],
        "constraints": [],
        "checker": {"type": "exact"},
        "timeout_seconds": 3,
        "statement": "Return `x * 3`.",
        "starter_code": "def triple_value(x: int) -> int:\n    pass\n",
        "reference_solution": "def triple_value(x):\n    return x * 3\n",
        "solution_explanation": "Multiply by three.",
        "complexity": {"time": "O(1)", "space": "O(1)"},
        "visible_tests": [{"name": "basic", "args": [2], "expected": 6}],
        "hidden_tests": [{"name": "negative", "args": [-2], "expected": -6}],
    }
    content = "Here are problems:\n```json\n" + json.dumps([first, second]) + "\n```"
    validation = main.api_authoring_validate(main.AuthorProblemRequest(content=content))
    assert validation["ok"], validation
    assert validation["count"] == 2, validation
    assert len(validation["problems"]) == 2, validation

    created = main.api_authoring_create_problem(main.AuthorProblemRequest(content=content))
    assert created["ok"], created
    assert created["created_count"] == 2, created
    assert len(created["results"]) == 2, created

    batch = main.api_list_problems(tag="batch")["problems"]
    assert {problem["id"] for problem in batch} >= {"acceptance_batch_one", "acceptance_batch_two"}, batch
    for problem_id in ("acceptance_batch_one", "acceptance_batch_two"):
        problem = main.api_get_problem_raw(problem_id)["problem"]
        judged = main.api_submit(main.SubmitRequest(problem_id=problem_id, code=problem["reference_solution"], mode="submit"))
        assert judged["status"] == "Accepted", judged

    duplicate = main.api_authoring_create_problem(main.AuthorProblemRequest(content=json.dumps([first, second])))
    assert not duplicate["ok"], duplicate
    assert duplicate["created_count"] == 0, duplicate
    assert len(duplicate["errors"]) == 2, duplicate
    return "validated 2, created 2, duplicate batch blocked"


def scenario_reference_expected_verification() -> str:
    problem = problem_template("acceptance_bad_expected", "Bad Expected", "verification")
    problem["visible_tests"] = [{"name": "wrong visible", "args": [2], "expected": 999}]
    content = json.dumps(problem)

    run = main.api_authoring_run_reference(main.AuthorProblemRequest(content=content))
    assert not run["ok"], run
    assert run["result"]["status"] == "Wrong Answer", run
    assert run["result"]["tests"][0]["expected"] == 999, run
    assert run["result"]["tests"][0]["actual"] == 4, run

    validation = main.api_authoring_validate(main.AuthorProblemRequest(content=content))
    assert validation["ok"], validation
    assert validation["problem"]["visible_tests"][0]["expected"] == 4, validation
    assert any("Corrected expected output from reference_solution" in warning for warning in validation["warnings"]), validation

    created = main.api_authoring_create_problem(main.AuthorProblemRequest(content=content))
    assert created["created"], created
    saved = main.api_get_problem_raw(problem["id"])["problem"]
    assert saved["visible_tests"][0]["expected"] == 4, saved
    judged = main.api_submit(main.SubmitRequest(problem_id=problem["id"], code=saved["reference_solution"], mode="submit"))
    assert judged["status"] == "Accepted", judged
    return "validate/create corrected inconsistent expected output from reference solution"


def scenario_llm_problem_draft_loop() -> str:
    bad = problem_template("acceptance_llm_generated", "LLM Generated", "llm")
    bad["visible_tests"] = [{"name": "bad expected", "args": [2], "expected": 999}]
    fixed = copy.deepcopy(bad)
    fixed["visible_tests"] = [{"name": "basic", "args": [2], "expected": 4}]

    result = llm_authoring.generate_problem_draft(
        "Create an easy doubling problem.",
        client=FakeJsonClient(
            json.dumps({"problems": [bad]}),
        ),
        max_attempts=2,
    )
    assert result["ok"], result
    assert len(result["attempts"]) == 1, result
    assert result["problem"]["id"] == fixed["id"], result
    assert result["problem"]["visible_tests"][0]["expected"] == 4, result["problem"]["visible_tests"]
    assert any("Corrected expected output from reference_solution" in warning for warning in result["warnings"]), result

    created = main.api_authoring_create_problem(main.AuthorProblemRequest(content=result["content"]))
    assert created["created"], created
    judged = main.api_submit(main.SubmitRequest(problem_id=fixed["id"], code=fixed["reference_solution"], mode="submit"))
    assert judged["status"] == "Accepted", judged
    return "fake LLM bad expected output corrected deterministically"


def scenario_llm_test_drafts() -> str:
    problem = problem_template("acceptance_llm_tests", "LLM Tests", "llm")
    create(problem)
    raw = main.api_get_problem_raw(problem["id"])["problem"]
    result = llm_authoring.generate_test_drafts(
        raw,
        "Add tests for zero and negative inputs.",
        group="hidden_tests",
        count=2,
        client=FakeJsonClient(
            json.dumps(
                {
                    "tests": [
                        {"name": "negative", "args": [-4]},
                        {"name": "zero", "args": [0]},
                    ]
                }
            )
        ),
    )
    assert result["ok"], result
    assert [test["expected"] for test in result["test_cases"]] == [-8, 0], result

    for test_case in result["test_cases"]:
        added = main.api_add_problem_test(
            problem["id"],
            main.AddTestCaseRequest(group="hidden_tests", test_case=test_case),
        )
        assert added["saved"], added

    judged = main.api_submit(main.SubmitRequest(problem_id=problem["id"], code=problem["reference_solution"], mode="submit"))
    assert judged["status"] == "Accepted", judged
    return "fake LLM test args converted to saved tests with expected outputs"


def scenario_llm_sequential_count() -> str:
    first = problem_template("acceptance_llm_seq_one", "Sequential One", "llm")
    second = problem_template("acceptance_llm_seq_two", "Sequential Two", "llm")
    result = llm_authoring.generate_problem_draft(
        "Create two easy arithmetic problems.",
        count=2,
        client=FakeJsonClient(
            json.dumps({"problems": [first]}),
            json.dumps({"problems": [second]}),
        ),
        max_attempts=1,
    )
    assert result["ok"], result
    assert result["sequential"], result
    assert result["requested_count"] == 2, result
    assert [problem["id"] for problem in result["problems"]] == [first["id"], second["id"]], result
    assert len(result["problem_results"]) == 2, result

    created = main.api_authoring_create_problem(main.AuthorProblemRequest(content=result["content"]))
    assert created["created"], created
    assert created["created_count"] == 2, created
    return "two requested problems were generated and validated one at a time"


def scenario_draft_dependency_install() -> str:
    problem = problem_template("acceptance_draft_numpy_install", "Draft NumPy Install", "numpy")
    problem["tags"] = ["python", "numpy"]
    problem["starter_code"] = "def double_value(x: list[float]) -> list[float]:\n    pass\n"
    problem["reference_solution"] = "def double_value(x):\n    return np.asarray(x, dtype=float) * 2\n"
    problem["visible_tests"] = [{"name": "basic", "args": [[1, 2]], "expected": [2.0, 4.0]}]
    problem["hidden_tests"] = [{"name": "empty", "args": [[]], "expected": []}]

    original = main.install_dependency_requirements
    calls: list[list[dict[str, Any]]] = []

    def fake_install(requirements: list[dict[str, Any]], scope: str = "draft_problem") -> dict[str, Any]:
        calls.append(requirements)
        return {
            "ok": True,
            "scope": scope,
            "installed": [],
            "message": "Nothing to install.",
            "stdout": "",
            "stderr": "",
            "dependency_status": {
                "ok": True,
                "requirements": [
                    {**requirements[0], "installed": True, "installed_version": "test"} if requirements else {}
                ],
                "missing": [],
                "install_command": "",
            },
        }

    try:
        main.install_dependency_requirements = fake_install
        result = main.api_authoring_install_dependencies(main.AuthorProblemRequest(content=json.dumps(problem)))
    finally:
        main.install_dependency_requirements = original

    assert result["ok"], result
    assert calls, result
    assert calls[0][0]["package"] == "numpy", calls
    assert result["validation_ok"], result
    return "draft install endpoint normalized and collected numpy requirement"


def scenario_llm_text_attachments() -> str:
    problem = problem_template("acceptance_llm_attachment", "LLM Attachment", "llm")
    client = FakeJsonClient(json.dumps({"problems": [problem]}))
    result = llm_authoring.generate_problem_draft(
        "Create a problem based on the attached notes.",
        attachments=[
            {
                "name": "notes.md",
                "mime_type": "text/markdown",
                "text": "# Notes\nMake the problem about doubling a value and include clear Input / Output.",
            }
        ],
        client=client,
        max_attempts=1,
    )
    assert result["ok"], result
    assert result["attachments"][0]["kind"] == "text", result
    assert client.calls, "fake client did not receive messages"
    prompt = client.calls[0]["messages"][-1]["content"]
    assert "Attached text source materials" in prompt, prompt
    assert "doubling a value" in prompt, prompt
    return "markdown attachment folded into the LLM prompt context"


class FakeJsonClient:
    def __init__(self, *responses: str) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def generate_json(
        self,
        messages: list[dict[str, str]],
        response_schema: dict[str, Any],
        model: str | None = None,
    ) -> str:
        assert messages, "messages should not be empty"
        assert response_schema.get("schema"), "schema should be provided"
        self.calls.append({"messages": messages, "response_schema": response_schema, "model": model})
        if not self.responses:
            raise AssertionError("FakeJsonClient has no remaining responses")
        return self.responses.pop(0)


def create(problem: dict[str, Any]) -> dict[str, Any]:
    return main.api_authoring_create_problem(main.AuthorProblemRequest(content=json.dumps(problem), overwrite=False))


def add_generated(problem_id: str, group: str, name: str, args: list[Any], expected: Any) -> None:
    result = main.api_add_generated_problem_test(
        problem_id,
        main.AddGeneratedTestCaseRequest(group=group, name=name, args=args),
    )
    assert result["saved"], result
    assert result["test_case"]["expected"] == expected, result
    judged = main.api_submit(
        main.SubmitRequest(problem_id=problem_id, code=result["problem"]["reference_solution"], mode="submit")
    )
    assert judged["status"] == "Accepted", judged


def problem_template(problem_id: str, title: str, tag: str) -> dict[str, Any]:
    return {
        "id": problem_id,
        "title": title,
        "difficulty": "easy",
        "entry_kind": "function",
        "function_name": "double_value",
        "tags": ["python", tag],
        "requirements": [],
        "constraints": [],
        "checker": {"type": "exact"},
        "timeout_seconds": 3,
        "statement": "Return `x * 2`.",
        "starter_code": "def double_value(x: int) -> int:\n    pass\n",
        "reference_solution": "def double_value(x):\n    return x * 2\n",
        "solution_explanation": "Multiply by two.",
        "complexity": {"time": "O(1)", "space": "O(1)"},
        "visible_tests": [{"name": "basic", "args": [2], "expected": 4}],
        "hidden_tests": [{"name": "large", "args": [5], "expected": 10}],
    }


def find_by(rows: list[dict[str, Any]], key: str, value: Any) -> dict[str, Any] | None:
    return next((row for row in rows if row.get(key) == value), None)


if __name__ == "__main__":
    raise SystemExit(main_runner())
