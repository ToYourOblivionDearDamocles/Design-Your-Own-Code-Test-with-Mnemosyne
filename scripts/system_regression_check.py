from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import main
from app.judge import judge_code
from app.problem_authoring import AUTHORING_PROMPT, format_problem_json, validate_problem_spec
from app.problem_store import get_problem, list_problems
from app.ui import APP_HTML


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


def check_equal(name: str, actual: Any, expected: Any) -> None:
    check(name, actual == expected, f"expected {expected!r}, got {actual!r}")


def main_check() -> int:
    problems = list_problems()
    check("problem bank is not empty", bool(problems))
    check("problem ids are unique", len({p["id"] for p in problems}) == len(problems), problems)
    check("starter codes are not all identical", len({get_problem(p["id"]).get("starter_code", "") for p in problems}) > 1)

    counter = get_problem_or_none("counter_class")
    if counter:
        counter_starter = counter.get("starter_code", "")
        check("counter problem has Counter starter", "class Counter" in counter_starter)
    else:
        check("counter_class sample problem is optional", True)

    for item in problems:
        problem_id = item["id"]
        raw = get_problem(problem_id)
        public = main.api_get_problem(problem_id)
        starter = raw.get("starter_code", "")

        check_equal(f"{problem_id}: raw id matches catalog id", raw.get("id"), problem_id)
        check(f"{problem_id}: raw starter_code is present", isinstance(starter, str) and bool(starter.strip()))
        check_equal(f"{problem_id}: API starter matches problem.json", public.get("starter_code"), starter)
        check(f"{problem_id}: API exposes starter_code", "starter_code" in public)
        check(f"{problem_id}: API hides reference_solution", "reference_solution" not in public)
        check(f"{problem_id}: API hides hidden_tests", "hidden_tests" not in public)
        check(f"{problem_id}: dependency status present", "dependency_status" in public)

        if problem_id != "counter_class":
            check(f"{problem_id}: starter is not Counter starter", "class Counter" not in starter)

        if raw.get("entry_kind", "function") == "function":
            function_name = raw.get("function_name")
            check(f"{problem_id}: function_name is declared", isinstance(function_name, str) and bool(function_name))
            check(f"{problem_id}: starter defines function_name", f"def {function_name}" in starter)
            check(f"{problem_id}: starter signature has input/output types", starter_has_typed_signature(starter, str(function_name)))

        validation = validate_problem_spec(raw)
        check(f"{problem_id}: verifier accepts problem", validation["ok"], validation.get("errors"))

    two_sum = get_problem("two_sum")
    two_sum_ok = judge_code(two_sum, two_sum["reference_solution"], "submit").as_dict()
    check_equal("two_sum reference solution accepted", two_sum_ok["status"], "Accepted")
    two_sum_wrong = judge_code(two_sum, "def two_sum(nums, target):\n    return []\n", "run").as_dict()
    check_equal("two_sum wrong solution rejected", two_sum_wrong["status"], "Wrong Answer")

    counter = get_problem_or_none("counter_class")
    if counter:
        counter_ok = judge_code(counter, counter["reference_solution"], "submit").as_dict()
        check_equal("counter reference solution accepted", counter_ok["status"], "Accepted")
    else:
        check("counter reference solution skipped when sample is absent", True)

    valid_code = main.api_check_code(main.CheckCodeRequest(code="def f():\n    return 1\n"))
    check("syntax checker accepts valid Python", valid_code["ok"], valid_code)
    invalid_code = main.api_check_code(main.CheckCodeRequest(code="def f(:\n    pass\n"))
    check("syntax checker rejects invalid Python", not invalid_code["ok"], invalid_code)
    check_equal("syntax checker reports SyntaxError", invalid_code["error_type"], "SyntaxError")

    compact_json = format_problem_json({"visible_tests": [{"name": "negative", "args": [[-2, 4]], "expected": 20}]})
    check("compact JSON keeps nested args on one line", '"args": [[-2, 4]]' in compact_json, compact_json)

    check("Create prompt encourages creative problems", "creative freedom" in AUTHORING_PROMPT.lower(), AUTHORING_PROMPT[:500])
    check("Create prompt requires Input / Output section", "Input / Output" in AUTHORING_PROMPT)
    check("Create prompt accepts short inline equations", "Short inline equations" in AUTHORING_PROMPT)
    check("Create prompt supports runtime arg_types", "arg_types" in AUTHORING_PROMPT and "numpy.ndarray" in AUTHORING_PROMPT)
    check("Create prompt supports object outputs", 'return_type": "object"' in AUTHORING_PROMPT or "simple object" in AUTHORING_PROMPT)

    check("UI uses CodeMirror progressive editor", "CodeMirror.fromTextArea" in APP_HTML)
    check("UI has loadProblem stale-request guard", "loadProblemRequestId" in APP_HTML and "requestId !== loadProblemRequestId" in APP_HTML)
    check("UI code submission reads editor abstraction", "getCodeValue()" in APP_HTML)
    check("UI exposes LLM attachment picker", "llmAttachmentInput" in APP_HTML and "collectLlmAttachments" in APP_HTML)
    check("UI accepts PDF markdown and image materials", ".pdf,.md" in APP_HTML and "image/*" in APP_HTML)
    check("UI model chooser accepts custom model names", 'list="llmModelOptions"' in APP_HTML and "datalist id=\"llmModelOptions\"" in APP_HTML)
    check("UI exposes LLM request timeout", "llmTimeoutSeconds" in APP_HTML and "timeout_seconds" in APP_HTML)

    script_text = extract_main_script(APP_HTML)
    script_path = Path("/private/tmp/mnemosyne_system_ui.js")
    script_path.write_text(script_text, encoding="utf-8")
    node = subprocess.run(["node", "--check", str(script_path)], text=True, capture_output=True)
    check("main UI script passes node --check", node.returncode == 0, node.stderr)

    check("at least 40 regression checks ran", CHECKS_RUN >= 40, CHECKS_RUN)
    print(f"\nSummary: {CHECKS_RUN - len(FAILURES)}/{CHECKS_RUN} checks passed")
    return 1 if FAILURES else 0


def extract_main_script(html: str) -> str:
    first = html.index("  <script>")
    start = html.index("  <script>", first + 1) + len("  <script>")
    end = html.index("  </script>", start)
    return html[start:end]


def starter_has_typed_signature(code: str, function_name: str) -> bool:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            args = list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs)
            named_args = [arg for arg in args if arg.arg != "self"]
            if any(arg.annotation is None for arg in named_args):
                return False
            if node.args.vararg and node.args.vararg.annotation is None:
                return False
            if node.args.kwarg and node.args.kwarg.annotation is None:
                return False
            return node.returns is not None
    return False


def get_problem_or_none(problem_id: str) -> dict[str, Any] | None:
    try:
        return get_problem(problem_id)
    except KeyError:
        return None


if __name__ == "__main__":
    raise SystemExit(main_check())
