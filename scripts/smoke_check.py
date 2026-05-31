from __future__ import annotations

import base64
import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app.llm_authoring as llm_authoring
from app.dependencies import build_install_command
from app.judge import judge_code
from app.problem_authoring import PROBLEM_TEMPLATE, format_problem_json, validate_problem_spec
from app.problem_store import get_problem, list_problems


def main() -> int:
    checks = [
        ("problem specs validate", check_problem_specs),
        ("two_sum accepted and wrong answer caught", check_two_sum),
        ("unit-test style problem accepted if present", check_unit_test_problem_if_present),
        ("linear regression numpy problem", check_linear_regression_if_present),
        ("authoring repairs common LLM schema mistakes", check_authoring_repair),
        ("authoring normalizes escaped newlines and imports", check_authoring_newline_import_repair),
        ("authoring normalizes LLM input/output test aliases", check_authoring_test_alias_repair),
        ("authoring schema rejects empty tests", check_authoring_schema_rejects_empty_tests),
        ("authoring rejects mismatched function code", check_authoring_strict_function_name),
        ("authoring requires typed starter signatures", check_authoring_requires_typed_starter),
        ("authoring accepts short inline equations", check_authoring_accepts_short_inline_equations),
        ("judge supports ndarray runtime interface", check_ndarray_runtime_interface),
        ("judge normalizes object outputs", check_object_output_normalization),
        ("authoring corrects bad expected outputs", check_authoring_reference_expected_correction),
        ("problem JSON keeps test arrays compact", check_problem_json_compact_format),
        ("unordered nested checker accepts grouped anagrams", check_unordered_nested_checker),
        ("nested float allclose tolerance matches attention outputs", check_nested_float_allclose_tolerance),
        ("pip command quotes version specs", check_install_command_quote),
        ("Gemini REST payload avoids full schema by default", check_gemini_payload_shape),
        ("DeepSeek payload uses json_object prompt mode", check_deepseek_payload_shape),
        ("LLM provider profiles are exposed", check_llm_provider_profiles),
        ("LLM attachments normalize and reach Gemini", check_llm_attachments),
        ("LLM multimodal source digest avoids repeated PDF uploads", check_llm_multimodal_source_digest_agent),
        ("LLM verifier repair hints are structured", check_llm_repair_hints),
    ]

    failed = 0
    for name, fn in checks:
        try:
            detail = fn()
            print(f"PASS {name}{': ' + detail if detail else ''}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {name}: {exc}")

    return 1 if failed else 0


def check_problem_specs() -> str:
    problem_ids = [problem["id"] for problem in list_problems()]
    assert problem_ids, "no problems found"
    for problem_id in problem_ids:
        result = validate_problem_spec(get_problem(problem_id))
        assert result["ok"], f"{problem_id}: {result['errors']}"
    return f"{len(problem_ids)} problems"


def check_two_sum() -> str:
    problem = get_problem("two_sum")
    accepted = judge_code(problem, problem["reference_solution"], "submit").as_dict()
    assert accepted["status"] == "Accepted", accepted

    wrong_code = "def two_sum(nums, target):\n    return []\n"
    wrong = judge_code(problem, wrong_code, "run").as_dict()
    assert wrong["status"] == "Wrong Answer", wrong
    assert wrong["passed"] < wrong["total"], wrong
    return "accepted path and wrong-answer path"


def check_unit_test_problem_if_present() -> str:
    problem = None
    for item in list_problems():
        candidate = get_problem(item["id"])
        if candidate.get("entry_kind") == "unit_tests":
            problem = candidate
            break
    if problem is None:
        return "not present, skipped"

    result = judge_code(problem, problem["reference_solution"], "submit").as_dict()
    assert result["status"] == "Accepted", result
    return f"{problem['id']} {result['passed']}/{result['total']}"


def check_linear_regression_if_present() -> str:
    try:
        problem = get_problem("linear_regression_gradient_descent")
    except KeyError:
        return "not present, skipped"

    result = judge_code(problem, problem["reference_solution"], "submit").as_dict()
    if result["status"] == "Missing Dependencies":
        return "missing optional dependency, skipped judge acceptance"
    assert result["status"] == "Accepted", result
    return f"{result['passed']}/{result['total']}"


def check_authoring_repair() -> str:
    draft = copy.deepcopy(PROBLEM_TEMPLATE)
    draft["id"] = "repair_numpy_example"
    draft["difficulty"] = "Medium"
    draft["entry_kind"] = "Function "
    draft["tags"] = ["python", "numpy"]
    draft["requirements"] = [
        "Initialize all weights to zero.",
        "Return a NumPy array.",
    ]
    draft.pop("checker", None)
    draft["starter_code"] = "def repair_numpy_example(x: list[float]) -> list[float]:\n    pass\n"
    draft["reference_solution"] = "def repair_numpy_example(x):\n    return np.asarray(x, dtype=float)\n"
    draft["function_name"] = "repair_numpy_example"
    draft["visible_tests"] = [
        {"name": "basic", "args": [[1, 2, 3]], "expected": [1.0, 2.0, 3.0]},
        {"name": "empty", "args": [[]], "expected": []},
    ]
    draft["hidden_tests"] = [{"name": "negative values", "args": [[-2, 4]], "expected": [-2.0, 4.0]}]

    result = validate_problem_spec(draft)
    assert result["ok"], result
    problem = result["problem"]
    assert problem["difficulty"] == "medium", problem
    assert problem["entry_kind"] == "function", problem
    assert problem["requirements"] == [{"package": "numpy", "pip": "numpy>=2.0", "import_name": "numpy"}], problem
    assert len(problem["constraints"]) >= 2, problem
    assert problem["checker"]["type"] == "allclose", problem
    assert problem["starter_code"].startswith("import numpy as np\n\n"), problem["starter_code"]
    assert problem["reference_solution"].startswith("import numpy as np\n\n"), problem["reference_solution"]
    return "requirements -> constraints, numpy/imports inferred, allclose inferred"


def check_authoring_newline_import_repair() -> str:
    draft = copy.deepcopy(PROBLEM_TEMPLATE)
    draft["id"] = "repair_escaped_newlines"
    draft["title"] = "Repair Escaped Newlines"
    draft["function_name"] = "repair_escaped_newlines"
    draft["tags"] = ["python", "numpy"]
    draft["requirements"] = [{"package": "numpy", "pip": "numpy>=2.0", "import_name": "numpy"}]
    draft.pop("checker", None)
    draft["statement"] = "# Repair\\n\\nCompute with $\\nabla f$ notation.\\nReturn the values as floats."
    draft["starter_code"] = "def repair_escaped_newlines(x: list[float]) -> list[float]:\\n    pass\\n"
    draft["reference_solution"] = "def repair_escaped_newlines(x):\\n    return np.asarray(x, dtype=float)\\n"
    draft["visible_tests"] = [{"name": "basic", "args": [[1, 2]], "expected": [1.0, 2.0]}]
    draft["hidden_tests"] = [{"name": "negative", "args": [[-1]], "expected": [-1.0]}]

    result = validate_problem_spec(draft)
    assert result["ok"], result
    problem = result["problem"]
    assert "# Repair\n\nCompute" in problem["statement"], repr(problem["statement"])
    assert "\\nabla" in problem["statement"], repr(problem["statement"])
    assert "\\n" not in problem["starter_code"], repr(problem["starter_code"])
    assert problem["starter_code"].startswith("import numpy as np\n\n"), problem["starter_code"]
    assert problem["reference_solution"].startswith("import numpy as np\n\n"), problem["reference_solution"]
    assert problem["checker"]["type"] == "allclose", problem["checker"]
    return "double-escaped newlines repaired, LaTeX kept, imports inserted"


def check_authoring_test_alias_repair() -> str:
    draft = copy.deepcopy(PROBLEM_TEMPLATE)
    draft["id"] = "repair_test_aliases"
    draft["title"] = "Repair Test Aliases"
    draft["function_name"] = "merge_two_dicts"
    draft["starter_code"] = "def merge_two_dicts(a: dict, b: dict) -> dict:\n    pass\n"
    draft["reference_solution"] = "def merge_two_dicts(a, b):\n    out = dict(a)\n    out.update(b)\n    return out\n"
    draft["visible_tests"] = [
        {"name": "input output", "input": {"a": {"x": 1}, "b": {"y": 2}}, "output": {"x": 1, "y": 2}},
        {"name": "args dict", "args": {"a": {"x": 1}, "b": {"x": 3}}, "result": {"x": 3}},
    ]
    draft["hidden_tests"] = [
        {"name": "named fields", "a": {}, "b": {"z": 4}, "expected_output": {"z": 4}},
    ]

    result = validate_problem_spec(draft)
    assert result["ok"], result
    problem = result["problem"]
    assert problem["visible_tests"][0]["args"] == [{"x": 1}, {"y": 2}], problem["visible_tests"][0]
    assert problem["visible_tests"][0]["expected"] == {"x": 1, "y": 2}, problem["visible_tests"][0]
    assert problem["visible_tests"][1]["args"] == [{"x": 1}, {"x": 3}], problem["visible_tests"][1]
    assert problem["visible_tests"][1]["expected"] == {"x": 3}, problem["visible_tests"][1]
    assert problem["hidden_tests"][0]["args"] == [{}, {"z": 4}], problem["hidden_tests"][0]

    one_arg = copy.deepcopy(PROBLEM_TEMPLATE)
    one_arg["id"] = "repair_single_list_input"
    one_arg["function_name"] = "sum_values"
    one_arg["starter_code"] = "def sum_values(nums: list[int]) -> int:\n    pass\n"
    one_arg["reference_solution"] = "def sum_values(nums):\n    return sum(nums)\n"
    one_arg["visible_tests"] = [{"name": "single list", "input": [1, 2, 3], "output": 6}]
    one_arg["hidden_tests"] = [{"name": "empty", "input": [], "output": 0}]
    one_arg_result = validate_problem_spec(one_arg)
    assert one_arg_result["ok"], one_arg_result
    assert one_arg_result["problem"]["visible_tests"][0]["args"] == [[1, 2, 3]], one_arg_result["problem"]["visible_tests"][0]

    word_count = copy.deepcopy(PROBLEM_TEMPLATE)
    word_count["id"] = "repair_word_frequency_aliases"
    word_count["function_name"] = "count_word_frequency"
    word_count["starter_code"] = "def count_word_frequency(words: list[str]) -> dict[str, int]:\n    pass\n"
    word_count["reference_solution"] = (
        "def count_word_frequency(words):\n"
        "    counts = {}\n"
        "    for word in words:\n"
        "        counts[word] = counts.get(word, 0) + 1\n"
        "    return counts\n"
    )
    word_count["visible_tests"] = [
        {"name": "raw args list", "args": ["apple", "banana", "apple"], "expected_counts": {"apple": 2, "banana": 1}},
        {"name": "named input", "words": ["cat", "cat", "dog"], "expected_result": {"cat": 2, "dog": 1}},
        {"name": "auto expected", "test_input": ["x", "x"]},
    ]
    word_count["hidden_tests"] = [{"name": "empty auto expected", "input_data": []}]
    word_count_result = validate_problem_spec(word_count)
    assert word_count_result["ok"], word_count_result
    fixed = word_count_result["problem"]
    assert fixed["visible_tests"][0]["args"] == [["apple", "banana", "apple"]], fixed["visible_tests"][0]
    assert fixed["visible_tests"][1]["args"] == [["cat", "cat", "dog"]], fixed["visible_tests"][1]
    assert fixed["visible_tests"][2]["expected"] == {"x": 2}, fixed["visible_tests"][2]
    assert fixed["hidden_tests"][0]["args"] == [[]], fixed["hidden_tests"][0]
    assert fixed["hidden_tests"][0]["expected"] == {}, fixed["hidden_tests"][0]
    return "input/output aliases, raw args lists, named fields, and auto expected outputs converted"


def check_authoring_schema_rejects_empty_tests() -> str:
    schema = llm_authoring._problem_collection_schema(1)["schema"]
    test_schema = schema["properties"]["problems"]["items"]["properties"]["visible_tests"]["items"]
    encoded = json.dumps(test_schema)
    assert '"args"' in encoded, encoded
    assert '"expected"' in encoded, encoded
    assert '"code"' in encoded, encoded

    empty_test = copy.deepcopy(PROBLEM_TEMPLATE)
    empty_test["id"] = "empty_test_objects"
    empty_test["visible_tests"] = [{}, {}, {}]
    empty_test["hidden_tests"] = [{}]
    result = validate_problem_spec(empty_test)
    assert not result["ok"], result
    joined = "\n".join(result["errors"])
    assert "visible_tests[0].args" in joined, joined
    assert "visible_tests[0].expected" in joined, joined
    return "schema requires args/expected and verifier rejects {} tests"


def check_authoring_strict_function_name() -> str:
    draft = copy.deepcopy(PROBLEM_TEMPLATE)
    draft["id"] = "strict_function_name"
    draft["function_name"] = "expected_name"
    draft["starter_code"] = "def wrong_name(nums: list[int]) -> list[int]:\n    pass\n"
    draft["reference_solution"] = "def wrong_name(nums):\n    return nums\n"

    result = validate_problem_spec(draft)
    assert not result["ok"], result
    joined = "\n".join(result["errors"])
    assert "starter_code must define function `expected_name`" in joined, joined
    assert "reference_solution must define function `expected_name`" in joined, joined
    return "mismatched starter/reference function definitions rejected"


def check_authoring_requires_typed_starter() -> str:
    draft = copy.deepcopy(PROBLEM_TEMPLATE)
    draft["id"] = "missing_starter_types"
    draft["function_name"] = "missing_starter_types"
    draft["starter_code"] = "def missing_starter_types(nums):\n    pass\n"
    draft["reference_solution"] = "def missing_starter_types(nums):\n    return sum(nums)\n"
    draft["visible_tests"] = [{"name": "basic", "args": [[1, 2, 3]], "expected": 6}]
    draft["hidden_tests"] = [{"name": "empty", "args": [[]], "expected": 0}]

    result = validate_problem_spec(draft)
    assert not result["ok"], result
    joined = "\n".join(result["errors"])
    assert "starter_code function `missing_starter_types` must type-annotate parameter `nums`" in joined, joined
    assert "starter_code function `missing_starter_types` must include a return type annotation" in joined, joined
    return "untyped parameter and missing return annotation rejected"


def check_authoring_accepts_short_inline_equations() -> str:
    draft = copy.deepcopy(PROBLEM_TEMPLATE)
    draft["id"] = "inline_full_equation"
    draft["statement"] = "Compute the loss $L(x) = x^2 + 1$ and return it. Short symbols like $x$ are fine."

    result = validate_problem_spec(draft)
    assert result["ok"], result
    assert not any("statement has long inline math" in warning for warning in result["warnings"]), result

    long_inline = copy.deepcopy(draft)
    long_inline["statement"] = (
        "Compute the update $L(\\theta) = \\frac{1}{2m} \\sum_{i=1}^{m} "
        "(x_i^T \\theta - y_i)^2 + \\lambda \\sum_{j=1}^{n} \\theta_j^2$."
    )
    long_result = validate_problem_spec(long_inline)
    assert long_result["ok"], long_result
    assert any("statement has long inline math" in warning for warning in long_result["warnings"]), long_result
    return "short inline equations accepted; long inline formulas warn instead of failing"


def check_ndarray_runtime_interface() -> str:
    if importlib.util.find_spec("numpy") is None:
        return "numpy not installed, skipped"

    problem = copy.deepcopy(PROBLEM_TEMPLATE)
    problem["id"] = "ndarray_runtime_interface"
    problem["title"] = "NDArray Runtime Interface"
    problem["function_name"] = "first_column"
    problem["tags"] = ["python", "numpy"]
    problem["arg_types"] = ["numpy.ndarray"]
    problem["return_type"] = "numpy.ndarray"
    problem["requirements"] = [{"package": "numpy", "pip": "numpy>=2.0", "import_name": "numpy"}]
    problem["checker"] = {"type": "allclose", "atol": 1e-5, "rtol": 1e-5}
    problem["statement"] = (
        "Return the first column of matrix `A`.\n\n"
        "## Input / Output\n\n"
        "- `A`: `numpy.ndarray`, a two-dimensional numeric array.\n"
        "- Return: `numpy.ndarray`, the first column."
    )
    problem["starter_code"] = "import numpy as np\n\ndef first_column(A: np.ndarray) -> np.ndarray:\n    pass\n"
    problem["reference_solution"] = "import numpy as np\n\ndef first_column(A):\n    assert hasattr(A, 'shape')\n    return A[:, 0]\n"
    problem["visible_tests"] = [{"name": "basic", "args": [[[1, 2], [3, 4]]], "expected": [1, 3]}]
    problem["hidden_tests"] = [{"name": "one_col", "args": [[[5], [6]]], "expected": [5, 6]}]

    result = validate_problem_spec(problem)
    assert result["ok"], result
    judged = judge_code(result["problem"], result["problem"]["reference_solution"], "submit").as_dict()
    assert judged["status"] == "Accepted", judged
    assert judged["tests"][0]["actual"] == [1, 3], judged
    return "arg_types converted JSON lists to np.ndarray before function call"


def check_object_output_normalization() -> str:
    problem = copy.deepcopy(PROBLEM_TEMPLATE)
    problem["id"] = "object_output_normalization"
    problem["title"] = "Object Output Normalization"
    problem["function_name"] = "make_metrics"
    problem["tags"] = ["python", "object"]
    problem["return_type"] = "object"
    problem["checker"] = {"type": "allclose", "atol": 1e-5, "rtol": 1e-5}
    problem["statement"] = (
        "Return an object with public metric fields.\n\n"
        "## Input / Output\n\n"
        "- `correct`: `int`, correct predictions.\n"
        "- `total`: `int`, total predictions.\n"
        "- Return: simple object with public `loss` and `accuracy` fields."
    )
    problem["starter_code"] = "def make_metrics(correct: int, total: int) -> object:\n    pass\n"
    problem["reference_solution"] = (
        "class Metrics:\n"
        "    def __init__(self, loss, accuracy):\n"
        "        self.loss = loss\n"
        "        self.accuracy = accuracy\n\n"
        "def make_metrics(correct, total):\n"
        "    accuracy = correct / total\n"
        "    return Metrics(loss=1 - accuracy, accuracy=accuracy)\n"
    )
    problem["visible_tests"] = [{"name": "basic", "args": [3, 4], "expected": {"loss": 0.25, "accuracy": 0.75}}]
    problem["hidden_tests"] = [{"name": "perfect", "args": [5, 5], "expected": {"loss": 0.0, "accuracy": 1.0}}]

    result = validate_problem_spec(problem)
    assert result["ok"], result
    judged = judge_code(result["problem"], result["problem"]["reference_solution"], "submit").as_dict()
    assert judged["status"] == "Accepted", judged
    assert judged["tests"][0]["actual"] == {"loss": 0.25, "accuracy": 0.75}, judged
    return "public object attributes compared against JSON object expected values"


def check_authoring_reference_expected_correction() -> str:
    draft = copy.deepcopy(PROBLEM_TEMPLATE)
    draft["id"] = "bad_expected_output"
    draft["visible_tests"] = [{"name": "wrong expected", "args": [[1, 2, 3]], "expected": 999}]

    result = validate_problem_spec(draft)
    assert result["ok"], result
    fixed = result["problem"]
    assert fixed["visible_tests"][0]["expected"] == 14, fixed["visible_tests"]
    joined = "\n".join(result["warnings"])
    assert "Corrected expected output from reference_solution" in joined, joined
    judged = judge_code(fixed, fixed["reference_solution"], "submit").as_dict()
    assert judged["status"] == "Accepted", judged
    return "reference solution output is used to correct stale expected values"


def check_problem_json_compact_format() -> str:
    draft = copy.deepcopy(PROBLEM_TEMPLATE)
    draft["visible_tests"] = [{"name": "negative values", "args": [[-2, 4]], "expected": 20}]

    text = format_problem_json(draft)
    assert '"args": [[-2, 4]]' in text, text
    assert '"expected": 20' in text, text
    assert '"args": [\n      [\n        -2' not in text, text
    return "args arrays stay on one line"


def check_unordered_nested_checker() -> str:
    problem = copy.deepcopy(PROBLEM_TEMPLATE)
    problem["id"] = "group_anagrams"
    problem["title"] = "Group Anagrams"
    problem["function_name"] = "group_anagrams"
    problem["tags"] = ["python", "hashmap", "anagram"]
    problem.pop("checker", None)
    problem["statement"] = "Group strings that are anagrams. Group order does not matter."
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

    result = validate_problem_spec(problem)
    assert result["ok"], result
    fixed = result["problem"]
    assert fixed["checker"]["type"] == "unordered_nested", fixed["checker"]
    judged = judge_code(fixed, fixed["reference_solution"], "submit").as_dict()
    assert judged["status"] == "Accepted", judged
    return "group order and inner item order ignored"


def check_nested_float_allclose_tolerance() -> str:
    expected = [
        [
            [2.921378560560599, 3.921378560560599, 4.9213785605605995],
            [2.078621439439401, 3.078621439439401, 4.078621439439401],
        ]
    ]
    actual = [
        [
            [2.9213724270418826, 3.9213724270418826, 4.921372427041883],
            [2.0786275729581174, 3.0786275729581174, 4.078627572958117],
        ]
    ]
    problem = copy.deepcopy(PROBLEM_TEMPLATE)
    problem["id"] = "scaled_dot_attention_02"
    problem["title"] = "Scaled Dot Attention"
    problem["function_name"] = "scaled_dot_attention_02"
    problem["tags"] = ["python", "attention", "float"]
    problem.pop("checker", None)
    problem["starter_code"] = "def scaled_dot_attention_02() -> list[list[list[float]]]:\n    pass\n"
    problem["reference_solution"] = f"def scaled_dot_attention_02():\n    return {repr(actual)}\n"
    problem["visible_tests"] = [{"name": "basic", "args": [], "expected": expected}]
    problem["hidden_tests"] = [{"name": "same", "args": [], "expected": expected}]

    result = validate_problem_spec(problem)
    assert result["ok"], result
    fixed = result["problem"]
    assert fixed["checker"] == {"type": "allclose", "atol": 1e-5, "rtol": 1e-5}, fixed["checker"]
    judged = judge_code(fixed, fixed["reference_solution"], "submit").as_dict()
    assert judged["status"] == "Accepted", judged

    exact_problem = copy.deepcopy(fixed)
    exact_problem["checker"] = {"type": "exact"}
    exact_judged = judge_code(exact_problem, exact_problem["reference_solution"], "submit").as_dict()
    assert exact_judged["status"] == "Wrong Answer", exact_judged

    tight_problem = copy.deepcopy(problem)
    tight_problem["checker"] = {"type": "allclose", "atol": 1e-6, "rtol": 1e-6}
    tight_result = validate_problem_spec(tight_problem)
    assert tight_result["ok"], tight_result
    assert tight_result["problem"]["checker"] == {"type": "allclose", "atol": 1e-5, "rtol": 1e-5}, tight_result
    assert any("Relaxed allclose tolerance" in warning for warning in tight_result["warnings"]), tight_result
    return "1e-5 allclose accepts nested attention-style float drift, and too-tight allclose is relaxed"


def check_install_command_quote() -> str:
    command = build_install_command([{"package": "numpy", "pip": "numpy>=2.0", "import_name": "numpy"}])
    assert command == ".venv/bin/pip install 'numpy>=2.0'", command
    return command


def check_gemini_payload_shape() -> str:
    original = llm_authoring._urlopen_json
    seen_payloads = []

    def fake_urlopen_json(request, timeout_seconds, label):  # noqa: ANN001 - local monkeypatch.
        payload = json.loads(request.data.decode("utf-8"))
        seen_payloads.append(payload)
        return {"candidates": [{"content": {"parts": [{"text": "{\"ok\": true}"}]}}]}

    try:
        llm_authoring._urlopen_json = fake_urlopen_json
        client = llm_authoring.GeminiClient(api_key="test-key")
        text = client.generate_json(
            [{"role": "user", "content": "Return {\"ok\": true}."}],
            {
                "name": "mnemosyne_problem_collection",
                "schema": {
                    "type": "object",
                    "properties": {"ok": {"type": "boolean"}},
                    "required": ["ok"],
                },
            },
            model="gemini-2.5-flash",
        )
    finally:
        llm_authoring._urlopen_json = original

    assert text == "{\"ok\": true}", text
    assert seen_payloads, "Gemini request was not made"
    generation_config = seen_payloads[0]["generationConfig"]
    assert generation_config["responseMimeType"] == "application/json", generation_config
    assert "responseJsonSchema" not in generation_config, generation_config
    assert "responseFormat" not in generation_config, generation_config
    assert generation_config["thinkingConfig"] == {"thinkingBudget": 0}, generation_config
    request_text = seen_payloads[0]["contents"][0]["parts"][0]["text"]
    assert "Required JSON contract" in request_text, request_text
    assert "Few-shot examples" in request_text, request_text
    assert "Single list argument" in request_text, request_text
    assert "NumPy/allclose" in request_text, request_text
    seen_payloads.clear()
    try:
        llm_authoring._urlopen_json = fake_urlopen_json
        text = client.generate_json_with_attachments(
            [{"role": "user", "content": "Create from this diagram."}],
            {
                "name": "mnemosyne_problem_collection",
                "schema": {
                    "type": "object",
                    "properties": {"ok": {"type": "boolean"}},
                    "required": ["ok"],
                },
            },
            model="gemini-2.5-flash",
            attachments=[
                {
                    "name": "diagram.png",
                    "mime_type": "image/png",
                    "content_base64": base64.b64encode(b"fake image").decode("ascii"),
                }
            ],
        )
    finally:
        llm_authoring._urlopen_json = original
    assert text == "{\"ok\": true}", text
    parts = seen_payloads[0]["contents"][0]["parts"]
    assert parts[1]["inlineData"]["mimeType"] == "image/png", parts
    assert parts[1]["inlineData"]["data"], parts

    seen_payloads.clear()
    try:
        llm_authoring._urlopen_json = fake_urlopen_json
        text = client.generate_json(
            [{"role": "user", "content": "Return {\"ok\": true}."}],
            {
                "name": "mnemosyne_problem_collection",
                "schema": {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]},
            },
            model="gemini-2.5-pro",
        )
    finally:
        llm_authoring._urlopen_json = original
    assert text == "{\"ok\": true}", text
    pro_generation_config = seen_payloads[0]["generationConfig"]
    assert "thinkingConfig" not in pro_generation_config, pro_generation_config

    seen_payloads.clear()
    try:
        llm_authoring._urlopen_json = fake_urlopen_json
        text = client.generate_json(
            [{"role": "user", "content": "Return {\"ok\": true}."}],
            {
                "name": "mnemosyne_problem_collection",
                "schema": {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]},
            },
            model="gemini-3.1-pro-preview",
        )
    finally:
        llm_authoring._urlopen_json = original
    assert text == "{\"ok\": true}", text
    gemini31_pro_config = seen_payloads[0]["generationConfig"]
    assert "thinkingConfig" not in gemini31_pro_config, gemini31_pro_config

    seen_payloads.clear()

    def fake_thinking_budget_error(request, timeout_seconds, label):  # noqa: ANN001 - local monkeypatch.
        payload = json.loads(request.data.decode("utf-8"))
        seen_payloads.append(payload)
        if len(seen_payloads) == 1:
            raise llm_authoring.LLMRequestError(
                "Gemini API request failed (400): Budget 0 is invalid. This model only works in thinking mode."
            )
        return {"candidates": [{"content": {"parts": [{"text": "{\"ok\": true}"}]}}]}

    try:
        llm_authoring._urlopen_json = fake_thinking_budget_error
        text = client.generate_json(
            [{"role": "user", "content": "Return {\"ok\": true}."}],
            {
                "name": "mnemosyne_problem_collection",
                "schema": {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]},
            },
            model="gemini-2.5-flash",
        )
    finally:
        llm_authoring._urlopen_json = original
    assert text == "{\"ok\": true}", text
    assert seen_payloads[0]["generationConfig"]["thinkingConfig"] == {"thinkingBudget": 0}, seen_payloads
    assert "thinkingConfig" not in seen_payloads[1]["generationConfig"], seen_payloads
    assert llm_authoring._gemini_request_timeout(60, "gemini-2.5-flash", [{"mime_type": "application/pdf"}]) == 180
    assert llm_authoring._gemini_request_timeout(60, "gemini-3.1-pro-preview", [{"mime_type": "application/pdf"}]) == 240
    return "responseMimeType only + prompt contract + inlineData + safe thinking fallback"


def check_deepseek_payload_shape() -> str:
    original = llm_authoring._urlopen_json
    seen_payloads = []

    def fake_urlopen_json(request, timeout_seconds, label):  # noqa: ANN001 - local monkeypatch.
        payload = json.loads(request.data.decode("utf-8"))
        seen_payloads.append((request.full_url, payload, label))
        return {"choices": [{"message": {"content": "{\"ok\": true}", "reasoning_content": "hidden reasoning"}}]}

    try:
        llm_authoring._urlopen_json = fake_urlopen_json
        client = llm_authoring.DeepSeekClient(api_key="test-key", model="deepseek-v4-flash")
        text = client.generate_json(
            [{"role": "user", "content": "Return {\"ok\": true} as json."}],
            {
                "name": "mnemosyne_problem_collection",
                "schema": {
                    "type": "object",
                    "properties": {"ok": {"type": "boolean"}},
                    "required": ["ok"],
                },
            },
        )
    finally:
        llm_authoring._urlopen_json = original

    assert text == "{\"ok\": true}", text
    assert seen_payloads, "DeepSeek request was not made"
    url, payload, label = seen_payloads[0]
    assert url == "https://api.deepseek.com/chat/completions", url
    assert label == "DeepSeek API", label
    assert payload["response_format"] == {"type": "json_object"}, payload
    assert "json_schema" not in json.dumps(payload), payload
    request_text = payload["messages"][-1]["content"]
    assert "Required JSON contract" in request_text, request_text
    assert "Few-shot examples" in request_text, request_text
    return "json_object + prompt contract"


def check_llm_provider_profiles() -> str:
    status = llm_authoring.llm_status()
    providers = {provider["id"]: provider for provider in status["providers"]}
    for provider_id in ("ollama", "gemini", "deepseek", "openai", "openai_compatible"):
        profile = providers[provider_id].get("profile")
        assert isinstance(profile, dict), providers[provider_id]
        assert profile.get("strategy"), providers[provider_id]
        assert "supports_json_schema" in profile, providers[provider_id]
        assert "supports_multimodal_attachments" in profile, providers[provider_id]
    gemini_models = providers["gemini"]["available_models"]
    assert "gemini-3.5-flash" in gemini_models, gemini_models
    assert "gemini-3.1-pro-preview" in gemini_models, gemini_models
    assert "gemini-2.5-pro" in gemini_models, gemini_models
    assert "gemini-2.5-flash-preview-09-2025" in gemini_models, gemini_models
    return ", ".join(sorted(providers))


def check_llm_attachments() -> str:
    bundle = llm_authoring._prepare_llm_attachments(
        [
            {"name": "lesson.md", "mime_type": "text/markdown", "text": "# Lesson\nUse Cholesky."},
            {
                "name": "figure.png",
                "mime_type": "image/png",
                "content_base64": base64.b64encode(b"fake image").decode("ascii"),
            },
        ]
    )
    assert not bundle["errors"], bundle
    assert "Use Cholesky" in bundle["text_context"], bundle
    assert bundle["multimodal"][0]["mime_type"] == "image/png", bundle
    request = llm_authoring._augment_request_with_attachments("Create one problem.", bundle)
    assert "Attached text source materials" in request, request
    assert "Additional PDF/image source materials" in request, request

    bad = llm_authoring._prepare_llm_attachments(
        [{"name": "archive.zip", "mime_type": "application/zip", "content_base64": base64.b64encode(b"zip").decode("ascii")}]
    )
    assert bad["errors"], bad
    return "text folded into prompt, images kept for multimodal provider, unsupported files rejected"


def check_llm_multimodal_source_digest_agent() -> str:
    digest = {
        "summary": "A Cholesky lecture about symmetric positive definite matrices.",
        "key_concepts": ["Cholesky factorization", "triangular solves"],
        "problem_briefs": [
            {
                "id_hint": "digest_cholesky_diagonal",
                "title": "Cholesky Diagonal",
                "learning_goal": "Compute a simple diagonal Cholesky factor.",
                "interface": "def cholesky_diagonal(diagonal: list[float]) -> list[float]",
                "packages": [],
                "edge_cases": ["unit diagonal", "large values"],
                "source_notes": "Use positive diagonal matrices.",
            },
            {
                "id_hint": "digest_triangular_sum",
                "title": "Triangular Sum",
                "learning_goal": "Work with lower-triangular entries.",
                "interface": "def lower_triangle_sum(matrix: list[list[int]]) -> int",
                "packages": [],
                "edge_cases": ["1x1 matrix", "negative entries"],
                "source_notes": "Sum entries where row >= column.",
            },
        ],
    }
    first_problem = copy.deepcopy(PROBLEM_TEMPLATE)
    first_problem.update(
        {
            "id": "digest_cholesky_diagonal",
            "title": "Cholesky Diagonal",
            "function_name": "cholesky_diagonal",
            "statement": "# Cholesky Diagonal\n\nReturn square roots for a diagonal SPD matrix.\n\n## Input / Output\n\n- `diagonal`: `list[float]`.\n- Return: `list[float]`.",
            "starter_code": "def cholesky_diagonal(diagonal: list[float]) -> list[float]:\n    pass\n",
            "reference_solution": "import math\n\ndef cholesky_diagonal(diagonal):\n    return [math.sqrt(x) for x in diagonal]\n",
            "checker": {"type": "allclose", "atol": 1e-5, "rtol": 1e-5},
            "visible_tests": [{"name": "basic", "args": [[4.0, 9.0]], "expected": [2.0, 3.0]}],
            "hidden_tests": [{"name": "unit", "args": [[1.0]], "expected": [1.0]}],
        }
    )
    second_problem = copy.deepcopy(PROBLEM_TEMPLATE)
    second_problem.update(
        {
            "id": "digest_lower_triangle_sum",
            "title": "Lower Triangle Sum",
            "function_name": "lower_triangle_sum",
            "statement": "# Lower Triangle Sum\n\nSum entries on and below the diagonal.\n\n## Input / Output\n\n- `matrix`: `list[list[int]]`.\n- Return: `int`.",
            "starter_code": "def lower_triangle_sum(matrix: list[list[int]]) -> int:\n    pass\n",
            "reference_solution": "def lower_triangle_sum(matrix):\n    return sum(matrix[i][j] for i in range(len(matrix)) for j in range(i + 1))\n",
            "visible_tests": [{"name": "basic", "args": [[[1, 2], [3, 4]]], "expected": 8}],
            "hidden_tests": [{"name": "one", "args": [[[5]]], "expected": 5}],
        }
    )
    client = FakeMultimodalClient(
        json.dumps(digest),
        json.dumps({"problems": [first_problem]}),
        json.dumps({"problems": [second_problem]}),
    )
    result = llm_authoring.generate_problem_draft(
        "Create two coding problems from this lecture.",
        count=2,
        client=client,
        attachments=[
            {
                "name": "lecture07_cholesky.pdf",
                "mime_type": "application/pdf",
                "content_base64": base64.b64encode(b"%PDF fake").decode("ascii"),
            }
        ],
        timeout_seconds=180,
    )

    assert result["ok"], result
    assert result["count"] == 2, result
    assert result.get("agent_plan", {}).get("summary"), result
    assert any("Agent speedup" in warning for warning in result["warnings"]), result["warnings"]
    assert client.calls[0]["attachments"], client.calls
    assert all(not call.get("attachments") for call in client.calls[1:]), client.calls
    assert "source digest" in client.calls[1]["messages"][0]["content"].lower() or "source digest" in client.calls[1]["messages"][-1]["content"].lower(), client.calls[1]
    return "one multimodal digest call, then text-only per-problem generation"


class FakeMultimodalClient:
    def __init__(self, *responses: str) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def generate_json(
        self,
        messages: list[dict[str, str]],
        response_schema: dict[str, Any],
        model: str | None = None,
    ) -> str:
        self.calls.append({"messages": messages, "response_schema": response_schema, "model": model, "attachments": []})
        if not self.responses:
            raise AssertionError("FakeMultimodalClient has no remaining responses")
        return self.responses.pop(0)

    def generate_json_with_attachments(
        self,
        messages: list[dict[str, str]],
        response_schema: dict[str, Any],
        model: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> str:
        self.calls.append(
            {
                "messages": messages,
                "response_schema": response_schema,
                "model": model,
                "attachments": attachments or [],
            }
        )
        if not self.responses:
            raise AssertionError("FakeMultimodalClient has no remaining responses")
        return self.responses.pop(0)


def check_llm_repair_hints() -> str:
    errors = [
        "problems[0] (count_word_frequency): visible_tests[0].args must be a list of positional arguments.",
        "problems[0] (count_word_frequency): visible_tests[0].expected is required.",
        "problems[0] (count_word_frequency): reference_solution output mismatch on hidden_tests[0] (bad): expected 5, actual 4.",
        "problems[0] (chol): reference_solution raises an error on visible_tests[0] (basic): AttributeError: 'list' object has no attribute 'shape'.",
        "problems[0] (chol): statement has long inline math that may read better as display math: $L = A A^T$.",
        "problem 1: Gemini API request timed out after 60s.",
    ]
    report = llm_authoring._repair_hint_report(errors, [])
    codes = {hint["code"] for hint in report["hints"]}
    assert "function_test_shape" in codes, report
    assert "expected_mismatch" in codes, report
    assert "json_list_array_conversion" in codes, report
    assert "display_math_preferred" in codes, report
    assert "llm_timeout" in codes, report
    assert report["raw_error_count"] == len(errors), report
    mismatch_hint = next(hint for hint in report["hints"] if hint["code"] == "expected_mismatch")
    suggested = mismatch_hint.get("suggested_edits") or []
    assert suggested and suggested[0]["actual_from_reference"] == 4, report
    assert suggested[0]["current_expected"] == 5, report

    messages = llm_authoring._repair_problem_messages("Create a word frequency problem.", "{\"problems\":[]}", errors, [])
    prompt = messages[-1]["content"]
    assert "Verifier repair report JSON" in prompt, prompt
    assert '"code": "function_test_shape"' in prompt, prompt
    assert '"actual_from_reference": 4' in prompt, prompt
    assert "Do not include this report" in prompt, prompt
    return ", ".join(sorted(codes))


if __name__ == "__main__":
    raise SystemExit(main())
