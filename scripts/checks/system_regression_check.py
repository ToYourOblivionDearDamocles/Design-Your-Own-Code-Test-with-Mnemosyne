from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mnemosyne.api import routes as api_routes
from mnemosyne.api.schemas import CheckCodeRequest
from mnemosyne.runtime.judge import judge_code
from mnemosyne.problem_authoring import AUTHORING_PROMPT, format_problem_json, parse_problem_collection, validate_problem_spec
from mnemosyne.storage.problems import get_problem, list_problems
from mnemosyne.ui import APP_HTML


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
        public = api_routes.api_get_problem(problem_id)
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

    valid_code = api_routes.api_check_code(CheckCodeRequest(code="def f():\n    return 1\n"))
    check("syntax checker accepts valid Python", valid_code["ok"], valid_code)
    invalid_code = api_routes.api_check_code(CheckCodeRequest(code="def f(:\n    pass\n"))
    check("syntax checker rejects invalid Python", not invalid_code["ok"], invalid_code)
    check_equal("syntax checker reports SyntaxError", invalid_code["error_type"], "SyntaxError")

    compact_json = format_problem_json({"visible_tests": [{"name": "negative", "args": [[-2, 4]], "expected": 20}]})
    check("compact JSON keeps nested args on one line", '"args": [[-2, 4]]' in compact_json, compact_json)

    envelope = format_problem_json({"problems": [get_problem("two_sum"), get_problem("solve_two_by_two_linear_system")]})
    envelope_items = parse_problem_collection(envelope)
    check("Direct JSON verifier accepts problems envelope", len(envelope_items) == 2 and envelope_items[0]["id"] == "two_sum", envelope_items)

    check("Create prompt encourages creative problems", "creative freedom" in AUTHORING_PROMPT.lower(), AUTHORING_PROMPT[:500])
    check("Create prompt requires Input / Output section", "Input / Output" in AUTHORING_PROMPT)
    check("Create prompt accepts short inline equations", "Short inline equations" in AUTHORING_PROMPT)
    check("Create prompt supports runtime arg_types", "arg_types" in AUTHORING_PROMPT and "numpy.ndarray" in AUTHORING_PROMPT)
    check("Create prompt supports non-list runtime structures", "scipy.sparse.csr_matrix" in AUTHORING_PROMPT and "complex" in AUTHORING_PROMPT)
    check("Create prompt supports object outputs", 'return_type": "object"' in AUTHORING_PROMPT or "simple object" in AUTHORING_PROMPT)
    lower_prompt = AUTHORING_PROMPT.lower()
    check("Create prompt asks for .json file contents", ".json file" in lower_prompt and "contents" in lower_prompt, AUTHORING_PROMPT[:400])
    check("Create prompt requires raw JSON only", "return raw valid json only" in lower_prompt, AUTHORING_PROMPT[:400])
    check(
        "Create prompt defines first and last character boundary",
        "First character must be { or [" in AUTHORING_PROMPT and "Last character must be } or ]" in AUTHORING_PROMPT,
        AUTHORING_PROMPT[:400],
    )
    check("Create prompt forbids markdown and prose", "Do not wrap it in markdown" in AUTHORING_PROMPT and "Do not include explanations" in AUTHORING_PROMPT)
    try:
        sample_problem = extract_direct_prompt_minimal_sample(AUTHORING_PROMPT)
        sample_validation = validate_problem_spec(sample_problem)
        sample_ok = sample_validation["ok"]
        sample_detail = sample_validation.get("errors")
    except Exception as exc:  # noqa: BLE001 - regression detail should include parse failures.
        sample_ok = False
        sample_detail = repr(exc)
    check("Create prompt minimal sample passes verifier", sample_ok, sample_detail)

    check("UI uses CodeMirror progressive editor", "CodeMirror.fromTextArea" in APP_HTML)
    check("UI has loadProblem stale-request guard", "loadProblemRequestId" in APP_HTML and "requestId !== loadProblemRequestId" in APP_HTML)
    check("UI code submission reads editor abstraction", "getCodeValue()" in APP_HTML)
    check("UI exposes LLM attachment picker", "llmAttachmentInput" in APP_HTML and "collectLlmAttachments" in APP_HTML)
    check("UI accepts PDF markdown and image materials", ".pdf,.md" in APP_HTML and "image/*" in APP_HTML)
    check("UI model chooser accepts custom model names", 'list="llmModelOptions"' in APP_HTML and "datalist id=\"llmModelOptions\"" in APP_HTML)
    check("UI exposes LLM request timeout", "llmTimeoutSeconds" in APP_HTML and "timeout_seconds" in APP_HTML)
    check("Create Direct JSON mode has fixed feedback loop", "setCreateConversationMode" in APP_HTML and "directJsonVerifierChatText" in APP_HTML and "submitDirectJsonDraft" in APP_HTML)
    check("Create Direct JSON prompts are compact and copyable", "compactPromptPreview" in APP_HTML and "copyCreatePrimaryText" in APP_HTML)
    check("Create Direct JSON chat shows submitted JSON and verifier feedback", "appendCreateChatBubble" in APP_HTML and "directJsonVerifierChatText" in APP_HTML and "copyCreateChatBubble" in APP_HTML)
    ui_js_dir = ROOT / "mnemosyne" / "ui_js"
    check("UI script is split into focused Create modules", (ui_js_dir / "create_chat.py").exists() and (ui_js_dir / "create_direct_json.py").exists() and (ui_js_dir / "create_llm.py").exists() and (ui_js_dir / "verifier_feedback.py").exists())
    check("UI script is split into Practice Manage Problem List modules", (ui_js_dir / "practice_learning.py").exists() and (ui_js_dir / "practice_runner.py").exists() and (ui_js_dir / "manage.py").exists() and (ui_js_dir / "problem_list.py").exists() and (ui_js_dir / "llm_status.py").exists())
    check("Editable UI copy JSON is embedded", (ROOT / "mnemosyne" / "ui_copy" / "ui_text.json").exists() and "MNEMOSYNE_UI_TEXT" in APP_HTML and "direct_json" in APP_HTML and "verifier" in APP_HTML)
    check("Create verifier panel can resize independently", "initCreateVerifierSplitter" in APP_HTML and "--create-verifier-height" in APP_HTML)
    check("Create preview uses learning section tabs", "setCreatePreviewSection" in APP_HTML and "createPreviewProblemTab" in APP_HTML and "createPreviewSolutionTab" in APP_HTML)
    check("UI defines central view router", "function setView(view)" in APP_HTML and "setView('catalog')" in APP_HTML and "setView('manage')" in APP_HTML and "setView('llm')" in APP_HTML)

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


def extract_direct_prompt_minimal_sample(prompt: str) -> dict[str, Any]:
    marker = "Minimal single-problem shape:"
    start = prompt.index('{\n  "id": "snake_case_unique_id"', prompt.index(marker))
    end = prompt.index("\n}\n\nRecommended ending format:", start) + 2
    value = json.loads(prompt[start:end])
    if not isinstance(value, dict):
        raise ValueError("Direct JSON minimal sample must be a JSON object.")
    return value


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
