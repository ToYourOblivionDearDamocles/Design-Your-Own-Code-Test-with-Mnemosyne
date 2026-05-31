from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from app.json_format import dumps_compact_json
from app.problem_store import PROBLEMS_DIR

ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
FUNCTION_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
PACKAGE_SPEC_RE = re.compile(
    r"^[A-Za-z0-9_.-]+(?:\[[A-Za-z0-9_,.-]+\])?(?:\s*(?:==|!=|<=|>=|~=|<|>)\s*[^ ;]+(?:\s*,\s*[^ ;]+)*)?$"
)
IMPORT_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
DEFAULT_FLOAT_ATOL = 1e-5
DEFAULT_FLOAT_RTOL = 1e-5
INLINE_MATH_RE = re.compile(r"(?<!\\)(?<!\$)\$(?!\$)(.+?)(?<!\\)\$(?!\$)", re.DOTALL)
DISPLAY_MATH_COMMAND_RE = re.compile(
    r"\\(?:sum|frac|int|prod|lim|begin|end|sqrt|operatorname|left|right|argmin|argmax)\b"
)

def json_value_schema(depth: int = 4) -> dict[str, Any]:
    if depth <= 0:
        return {
            "anyOf": [
                {"type": "string"},
                {"type": "number"},
                {"type": "integer"},
                {"type": "boolean"},
                {"type": "null"},
            ]
        }
    child = json_value_schema(depth - 1)
    return {
        "anyOf": [
            {"type": "string"},
            {"type": "number"},
            {"type": "integer"},
            {"type": "boolean"},
            {"type": "null"},
            {"type": "array", "items": child},
            {"type": "object", "additionalProperties": child},
        ]
    }


JSON_VALUE_SCHEMA = json_value_schema()
TYPE_SPEC_SCHEMA: dict[str, Any] = {
    "anyOf": [
        {"type": "string"},
        {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "type": {"type": "string"},
                "dtype": {"type": "string"},
            },
            "required": ["type"],
        },
    ]
}
SUPPORTED_RUNTIME_TYPES = {
    "json",
    "json_native",
    "int",
    "float",
    "str",
    "bool",
    "list",
    "dict",
    "tuple",
    "set",
    "frozenset",
    "object",
    "namespace",
    "types.SimpleNamespace",
    "SimpleNamespace",
    "numpy.ndarray",
    "np.ndarray",
    "numpy.array",
    "np.array",
    "ndarray",
    "torch.Tensor",
    "torch.tensor",
    "tensor",
    "pandas.DataFrame",
    "pd.DataFrame",
    "dataframe",
    "pandas.Series",
    "pd.Series",
    "series",
}

FUNCTION_TEST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "args", "expected"],
    "properties": {
        "name": {"type": "string"},
        "args": {
            "type": "array",
            "minItems": 1,
            "items": JSON_VALUE_SCHEMA,
        },
        "expected": JSON_VALUE_SCHEMA,
    },
}

UNIT_TEST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "code"],
    "properties": {
        "name": {"type": "string"},
        "code": {"type": "string"},
    },
}

KNOWN_PACKAGE_REQUIREMENTS: dict[str, dict[str, str]] = {
    "numpy": {"package": "numpy", "pip": "numpy>=2.0", "import_name": "numpy"},
    "np": {"package": "numpy", "pip": "numpy>=2.0", "import_name": "numpy"},
    "torch": {"package": "torch", "pip": "torch", "import_name": "torch"},
    "pytorch": {"package": "torch", "pip": "torch", "import_name": "torch"},
    "pandas": {"package": "pandas", "pip": "pandas", "import_name": "pandas"},
    "pd": {"package": "pandas", "pip": "pandas", "import_name": "pandas"},
    "sklearn": {"package": "scikit-learn", "pip": "scikit-learn", "import_name": "sklearn"},
    "scikit_learn": {"package": "scikit-learn", "pip": "scikit-learn", "import_name": "sklearn"},
    "scikit-learn": {"package": "scikit-learn", "pip": "scikit-learn", "import_name": "sklearn"},
    "matplotlib": {"package": "matplotlib", "pip": "matplotlib", "import_name": "matplotlib"},
    "scipy": {"package": "scipy", "pip": "scipy", "import_name": "scipy"},
    "opencv": {"package": "opencv-python", "pip": "opencv-python", "import_name": "cv2"},
    "opencv-python": {"package": "opencv-python", "pip": "opencv-python", "import_name": "cv2"},
    "cv2": {"package": "opencv-python", "pip": "opencv-python", "import_name": "cv2"},
}
KNOWN_IMPORT_SNIPPETS: dict[str, str] = {
    "numpy": "import numpy as np",
    "torch": "import torch",
    "pandas": "import pandas as pd",
    "sklearn": "import sklearn",
    "matplotlib": "import matplotlib.pyplot as plt",
    "scipy": "import scipy",
    "cv2": "import cv2",
}
TEXT_DEPENDENCY_KEYWORDS = {
    "numpy",
    "torch",
    "pytorch",
    "pandas",
    "sklearn",
    "scikit_learn",
    "scikit-learn",
    "matplotlib",
    "scipy",
    "opencv",
    "opencv-python",
    "cv2",
}

PROBLEM_TEMPLATE: dict[str, Any] = {
    "id": "sum_of_squares",
    "title": "Sum of Squares",
    "difficulty": "easy",
    "entry_kind": "function",
    "function_name": "sum_of_squares",
    "tags": ["python", "math", "array"],
    "requirements": [],
    "constraints": [
        "Use Python only.",
        "Do not modify the input list.",
    ],
    "checker": {"type": "exact"},
    "timeout_seconds": 3,
    "statement": "# Sum of Squares\n\nWrite a function `sum_of_squares(nums)` that returns the sum of each number squared.\n\n## Input / Output\n\n- `nums`: `list[int]`, a list of integers.\n- Return: `int`, the sum of squared values.\n\nMathematically, return:\n\n$$\n\\sum_{i=0}^{n-1} nums[i]^2\n$$",
    "starter_code": "def sum_of_squares(nums: list[int]) -> int:\n    pass\n",
    "reference_solution": "def sum_of_squares(nums):\n    return sum(x * x for x in nums)\n",
    "solution_explanation": "Square each number and add the results.",
    "complexity": {
        "time": "O(n)",
        "space": "O(1)",
    },
    "visible_tests": [
        {"name": "basic", "args": [[1, 2, 3]], "expected": 14},
        {"name": "empty", "args": [[]], "expected": 0},
    ],
    "hidden_tests": [
        {"name": "negative values", "args": [[-2, 4]], "expected": 20},
    ],
}

AUTHORING_API_SCHEMA: dict[str, Any] = {
    "name": "mnemosyne_problem",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "id",
            "title",
            "difficulty",
            "entry_kind",
            "tags",
            "requirements",
            "constraints",
            "checker",
            "timeout_seconds",
            "statement",
            "starter_code",
            "reference_solution",
            "solution_explanation",
            "complexity",
            "visible_tests",
            "hidden_tests",
        ],
        "properties": {
            "id": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"},
            "title": {"type": "string"},
            "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
            "entry_kind": {"type": "string", "enum": ["function", "unit_tests"]},
            "function_name": {"type": "string", "pattern": "^[A-Za-z_][A-Za-z0-9_]*$"},
            "arg_types": {"type": "array", "items": TYPE_SPEC_SCHEMA},
            "return_type": TYPE_SPEC_SCHEMA,
            "tags": {"type": "array", "items": {"type": "string"}},
            "requirements": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "package": {"type": "string"},
                        "pip": {"type": "string"},
                        "import_name": {"type": "string"},
                    },
                    "required": ["package", "pip", "import_name"],
                },
            },
            "constraints": {"type": "array", "items": {"type": "string"}},
            "checker": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "type": {"type": "string", "enum": ["exact", "allclose", "unordered_nested"]},
                    "atol": {"type": "number"},
                    "rtol": {"type": "number"},
                },
                "required": ["type"],
            },
            "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 60},
            "statement": {"type": "string"},
            "starter_code": {"type": "string"},
            "reference_solution": {"type": "string"},
            "solution_explanation": {"type": "string"},
            "complexity": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "time": {"type": "string"},
                    "space": {"type": "string"},
                },
                "required": ["time", "space"],
            },
            "visible_tests": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "anyOf": [
                        FUNCTION_TEST_SCHEMA,
                        UNIT_TEST_SCHEMA,
                    ]
                },
            },
            "hidden_tests": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "anyOf": [
                        FUNCTION_TEST_SCHEMA,
                        UNIT_TEST_SCHEMA,
                    ]
                },
            },
        },
    },
}

AUTHORING_PROMPT = """You are generating coding-practice problems for Mnemosyne, my local Python practice app.

Most reliable chat output format:
- Return exactly one fenced json code block.
- Put no prose before or after the code block.
- Inside the code block, the content must be valid JSON, not Python.

Critical JSON punctuation rules:
- Use ASCII straight double quotes for every JSON key and every JSON string delimiter: "
- Never use Chinese or smart quotes: “ ” ‘ ’
- Never use single quotes as JSON delimiters.
- Never add trailing commas.
- Newlines inside code strings must be escaped once as \\n in JSON text, for example "def f(x):\\n    pass\\n".
- Do not double escape newlines as \\\\n text that would display literally in the app.
- Keep test case values compact. Prefer one short test object per line, for example {"name": "negative values", "args": [[-2, 4]], "expected": 20}.
- Do not pretty-print nested test arrays as stair-step lists.
- If the problem involves mathematics, optimization, probability, linear algebra, calculus, statistics, or ML loss functions, prefer display math in the statement using $$...$$ for important standalone equations.
- Inline math $...$ is allowed for short symbols and short equations, for example $x$, $i = j$, $A = LU$, or $\\lambda_i > 0$.
- Very long or multi-line formulas are easier to read as display math $$...$$; the verifier may normalize or warn about those, but short inline equations are accepted.
- For function problems, the statement must include an "Input / Output" section that names each parameter and its expected runtime data structure, such as list[int], numpy.ndarray, torch.Tensor, pandas.DataFrame, int, float, str, dict[str, int], tuple[int, int], or a simple object.
- For function problems, starter_code must type-annotate every parameter and include a return type annotation, for example def solve(nums: list[int], target: int) -> list[int]: or import numpy as np; def solve(x: np.ndarray) -> np.ndarray:.
- If the user-facing function should receive arrays/tensors/dataframes/simple objects, add optional arg_types and return_type. The tests still store JSON-serializable values, but the judge converts args before calling the function and normalizes outputs for comparison.
- For one problem, return one JSON object.
- For multiple problems, return one JSON array of problem objects.
- Before final answer, check that the first non-space character inside the code block is { or [.
- Use only the fields shown in the schema below.

Content quality and creative freedom:
- Within the required JSON shape, use your own judgment and creativity to make the problem useful, original, and enjoyable to practice.
- If my request is broad, choose a concrete learning objective, realistic context, and meaningful edge cases.
- Prefer problems that teach a clear Python / AI engineering / data / math concept over generic toy tasks.
- Vary the setting, title, constraints, examples, and hidden tests when creating multiple problems.
- Make the statement concise but polished, like a real practice problem, not a schema-filling exercise.
- Thank you for helping me create thoughtful local practice problems. Do not include this thank-you sentence in the JSON output.

Single-problem shape:
```json
{
  "id": "snake_case_unique_id",
  "title": "Human Readable Title",
  "difficulty": "easy",
  "entry_kind": "function",
  "function_name": "python_function_name",
  "arg_types": ["list[int]"],
  "return_type": "int",
  "tags": ["python", "topic"],
  "requirements": [
    {"package": "package-name", "pip": "package-name>=1.0", "import_name": "import_name"}
  ],
  "constraints": ["Problem rule or implementation requirement"],
  "checker": {"type": "exact"},
  "timeout_seconds": 3,
  "statement": "Markdown problem statement. Include an Input / Output section naming each parameter and return runtime type/data structure. Prefer display math $$...$$ for important standalone equations when the problem is mathematical. Short inline equations like $A = LU$ are accepted. In JSON, LaTeX backslashes must be escaped, e.g. \\\\theta and \\\\sum.",
  "starter_code": "def python_function_name(x: list[int]) -> int:\\n    pass\\n",
  "reference_solution": "def python_function_name(...):\\n    ...\\n",
  "solution_explanation": "Brief explanation of the approach.",
  "complexity": {"time": "O(...)", "space": "O(...)"},
  "visible_tests": [{"name": "basic", "args": [[1, 2, 3]], "expected": 6}],
  "hidden_tests": [{"name": "edge case", "args": [[]], "expected": 0}]
}
```

Multi-problem shape:
```json
[
  {
    "id": "first_problem_id",
    "title": "First Problem",
    "difficulty": "easy",
    "entry_kind": "function",
    "function_name": "first_problem_id",
    "arg_types": ["int"],
    "return_type": "int",
    "tags": ["python"],
    "requirements": [],
    "constraints": [],
    "checker": {"type": "exact"},
    "timeout_seconds": 3,
    "statement": "Markdown statement.",
    "starter_code": "def first_problem_id(x: int) -> int:\\n    pass\\n",
    "reference_solution": "def first_problem_id(x):\\n    return x\\n",
    "solution_explanation": "Brief explanation.",
    "complexity": {"time": "O(1)", "space": "O(1)"},
    "visible_tests": [{"name": "basic", "args": [1], "expected": 1}],
    "hidden_tests": [{"name": "hidden", "args": [2], "expected": 2}]
  }
]
```

Rules:
- Use Python only.
- Supported entry kinds:
  - Use "function" for ordinary input/output problems. Include function_name. Tests use {"args": [...], "expected": ...}.
  - Use "unit_tests" for class/OOP/stateful problems. Omit function_name. Tests use {"code": "from user_solution import ClassName\\n...assert ..."}.
- For entry_kind, use "function" unless I explicitly ask for unit tests or a class/stateful problem.
- The id must match ^[a-z][a-z0-9_]*$.
- The "requirements" field is ONLY for Python package dependencies. Use [] for standard-library-only problems.
- Put problem instructions like "initialize weights to zero" in "constraints", not in "requirements".
- If requirements contains a package, starter_code and reference_solution must include the matching import.
  - NumPy: import numpy as np
  - PyTorch: import torch
  - pandas: import pandas as pd
- Supported checker values:
  - {"type": "exact"} for ordinary exact equality.
  - {"type": "allclose", "atol": 1e-5, "rtol": 1e-5} for floats, arrays, tensors, and approximate numeric answers.
  - {"type": "unordered_nested"} for nested lists where group order and item order do not matter, such as group-anagrams.
- The starter_code and reference_solution must define the same function_name.
- The statement must tell the user the input and output data structures clearly.
- For function problems, include an "Input / Output" section with one bullet per parameter and one bullet for the return value.
- For function problems, starter_code must include Python type hints for every parameter and a return type annotation. Good examples: list[int], list[float], list[list[float]], int, float, str, dict[str, int], tuple[int, int], np.ndarray, torch.Tensor, pd.DataFrame.
- Use optional arg_types and return_type to declare runtime conversion for non-JSON interfaces. Supported values include "numpy.ndarray", "torch.Tensor", "pandas.DataFrame", "pandas.Series", "object", "types.SimpleNamespace", "set", plus JSON-native types. For example, if starter_code is `def solve(A: np.ndarray) -> np.ndarray`, set "arg_types": ["numpy.ndarray"] and "return_type": "numpy.ndarray".
- If a function returns a simple object/dataclass/namedtuple, set "return_type": "object" and write expected as a JSON object matching the public fields. The judge normalizes public object attributes before comparison.
- visible_tests and hidden_tests must be enough to catch common wrong solutions.
- Each function test uses args as a list of positional arguments and expected as the exact expected return value.
- Never use input/output/inputs/result in function tests. Those keys are invalid. Use args/expected only.
- For `def f(a, b)`, use {"args": [value_for_a, value_for_b], "expected": answer}.
- For `def f(nums)`, a list input must still be wrapped as one positional argument: {"args": [[1, 2, 3]], "expected": 6}.
- Formatting preference: write short test objects on one line and keep list values compact, e.g. {"name": "negative values", "args": [[-2, 4]], "expected": 20}.
- For NumPy, PyTorch, pandas, or similar libraries, keep test args and expected values JSON-serializable: numbers, strings, booleans, null, lists, and objects. If arg_types is set, the judge converts args before calling starter/reference/user code. If arg_types is omitted, reference_solution must convert JSON values itself.
- Problem statements are Markdown. For math-heavy problems, prefer at least one display equation block using $$...$$, for example a loss function, recurrence, matrix formula, probability expression, or optimization objective.
- Short inline equations like $A = LU$, $i = j$, or $\\lambda_i > 0$ are acceptable. Use display math for long formulas that should stand on their own line.
- Keep all JSON strings properly escaped. Markdown statements may contain JSON newline escapes like \\n\\n between paragraphs. Code strings should use \\n for each line break.
- Do not reveal hidden_tests in the statement.

Example for an external package:
"requirements": [
  {"package": "numpy", "pip": "numpy>=2.0", "import_name": "numpy"}
],
"constraints": ["Return a NumPy-compatible array-like result."],
"checker": {"type": "allclose", "atol": 1e-5, "rtol": 1e-5}

Few-shot examples of valid tests:
- Single list argument: for `def sum_values(nums)`, use {"args": [[1, 2, 3]], "expected": 6}, not {"args": [1, 2, 3]}.
- Multi-argument function: for `def clamp_value(x, lo, hi)`, use {"args": [5, 1, 10], "expected": 5}.
- NumPy/allclose: use JSON-native lists in tests, e.g. {"args": [[1, 2, 3], 2], "expected": [2.0, 4.0, 6.0]}.
- OOP/unit_tests: use {"code": "from user_solution import Counter\\nc = Counter()\\nc.increment()\\nassert c.get_value() == 1"}.

API mode, if I use a model API instead of chat:
- Prefer a structured-output / JSON-schema response format.
- The schema endpoint in this app is GET /api/authoring/schema.
- The app will also accept pasted fenced json and will normalize common smart double quotes, but you should still produce strict JSON.

Create problem(s) from this request:
[PASTE MY TOPIC / REQUIREMENTS HERE]
"""


SMART_DOUBLE_QUOTES = str.maketrans({
    "“": '"',
    "”": '"',
    "„": '"',
    "‟": '"',
})
SMART_SINGLE_QUOTES = str.maketrans({
    "‘": "'",
    "’": "'",
    "‚": "'",
    "‛": "'",
})


def prepare_problem_content(content: str, warnings: list[str] | None = None) -> str:
    cleaned = content.strip().removeprefix("\ufeff").strip()
    if not cleaned:
        raise ValueError("Invalid JSON: content is empty.")

    fenced = re.match(r"^```(?:json|JSON)?\s*\n?(.*?)\n?```\s*$", cleaned, re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()
        _warn(warnings, "Removed markdown json code fence before parsing.")
    else:
        start, end = _json_bounds(cleaned)
        if start >= 0 and end > start and (start > 0 or end < len(cleaned) - 1):
            cleaned = cleaned[start : end + 1].strip()
            _warn(warnings, "Ignored text before or after the JSON object.")

    if any(ch in cleaned for ch in "“”„‟"):
        cleaned = cleaned.translate(SMART_DOUBLE_QUOTES)
        _warn(warnings, 'Converted smart double quotes to straight JSON quotes (").')
    if any(ch in cleaned for ch in "‘’‚‛"):
        cleaned = cleaned.translate(SMART_SINGLE_QUOTES)
        _warn(warnings, "Converted smart apostrophes to ASCII apostrophes inside JSON text.")

    return cleaned


def parse_problem_content(content: str, warnings: list[str] | None = None) -> dict[str, Any]:
    cleaned = prepare_problem_content(content, warnings)
    data = _loads_problem_json(cleaned)
    if not isinstance(data, dict):
        raise ValueError("Problem JSON must be an object.")
    return data


def parse_problem_collection(content: str, warnings: list[str] | None = None) -> list[dict[str, Any]]:
    cleaned = prepare_problem_content(content, warnings)
    data = _loads_problem_json(cleaned)
    if isinstance(data, dict):
        return [data]
    if not isinstance(data, list):
        raise ValueError("Problem JSON must be an object or an array of objects.")
    if not data:
        raise ValueError("Problem JSON array must contain at least one problem.")
    problems: list[dict[str, Any]] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Problem JSON array item {idx} must be an object.")
        problems.append(item)
    return problems


def _loads_problem_json(cleaned: str) -> Any:
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        hint = ""
        if "'" in cleaned:
            hint = " JSON syntax still requires straight double quotes for keys and string delimiters."
        raise ValueError(f"Invalid JSON: {e.msg} at line {e.lineno}, column {e.colno}.{hint}") from e


def _json_bounds(text: str) -> tuple[int, int]:
    candidates = []
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start >= 0 and end > start:
            candidates.append((start, end))
    if not candidates:
        return -1, -1
    return min(candidates, key=lambda item: item[0])


def _warn(warnings: list[str] | None, message: str) -> None:
    if warnings is not None and message not in warnings:
        warnings.append(message)


def validate_problem_spec(problem: dict[str, Any], verify_reference: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    normalized = dict(problem)
    checker_was_missing = "checker" not in problem
    _normalize_scalar_fields(normalized, warnings)

    _require_string(normalized, "id", errors)
    _require_string(normalized, "title", errors)
    _require_string(normalized, "difficulty", errors)
    _require_string(normalized, "entry_kind", errors)
    _require_string(normalized, "statement", errors)
    _require_string(normalized, "starter_code", errors)
    _require_string(normalized, "reference_solution", errors)
    _require_string(normalized, "solution_explanation", errors)

    problem_id = str(normalized.get("id", ""))
    if problem_id and not ID_RE.match(problem_id):
        errors.append("id must match ^[a-z][a-z0-9_]*$ and use snake_case.")

    difficulty = str(normalized.get("difficulty", ""))
    if difficulty and difficulty not in {"easy", "medium", "hard"}:
        errors.append("difficulty must be one of: easy, medium, hard.")

    entry_kind = str(normalized.get("entry_kind", ""))
    if entry_kind not in {"function", "unit_tests"}:
        errors.append("entry_kind must be either 'function' or 'unit_tests'.")

    normalized.setdefault("tags", [])
    normalized.setdefault("requirements", [])
    normalized.setdefault("constraints", [])
    normalized.setdefault("checker", {"type": "exact"})
    normalized.setdefault("timeout_seconds", 3)
    normalized.setdefault("visible_tests", [])
    normalized.setdefault("hidden_tests", [])
    _normalize_problem_fields(normalized, warnings, checker_was_missing)

    if not isinstance(normalized["tags"], list) or not all(isinstance(t, str) for t in normalized["tags"]):
        errors.append("tags must be a list of strings.")

    if not isinstance(normalized["requirements"], list):
        errors.append("requirements must be a list.")
    else:
        _validate_requirements(normalized["requirements"], errors, warnings)

    if not isinstance(normalized["constraints"], list) or not all(isinstance(c, str) for c in normalized["constraints"]):
        errors.append("constraints must be a list of strings.")

    _validate_checker(normalized.get("checker"), errors)
    _validate_complexity(normalized.get("complexity"), errors)
    _validate_statement_math(normalized.get("statement"), warnings)

    timeout = normalized.get("timeout_seconds")
    if not isinstance(timeout, int) or timeout < 1 or timeout > 60:
        errors.append("timeout_seconds must be an integer between 1 and 60.")

    for key in ("visible_tests", "hidden_tests"):
        if not isinstance(normalized.get(key), list):
            errors.append(f"{key} must be a list.")

    visible_tests = normalized.get("visible_tests", [])
    hidden_tests = normalized.get("hidden_tests", [])
    if isinstance(visible_tests, list) and not visible_tests:
        errors.append("visible_tests must contain at least one test.")
    if isinstance(hidden_tests, list) and not hidden_tests:
        warnings.append("hidden_tests is empty. This is okay for drafts, but real practice problems should include hidden tests.")

    if entry_kind == "function":
        _validate_function_problem(normalized, errors)
    elif entry_kind == "unit_tests":
        _validate_unit_test_problem(normalized, errors)

    if verify_reference and not errors:
        _verify_reference_solution_outputs(normalized, errors, warnings)

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "problem": normalized,
    }


def validate_problem_collection(problems: list[dict[str, Any]], verify_reference: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for idx, problem in enumerate(problems):
        validation = validate_problem_spec(problem, verify_reference=verify_reference)
        problem_id = str(validation.get("problem", {}).get("id") or problem.get("id") or f"item_{idx}")
        prefix = f"problems[{idx}] ({problem_id})"
        errors.extend(f"{prefix}: {error}" for error in validation["errors"])
        warnings.extend(f"{prefix}: {warning}" for warning in validation["warnings"])
        if validation.get("problem"):
            normalized.append(validation["problem"])
        if problem_id in seen_ids:
            errors.append(f"{prefix}: duplicate problem id in this batch.")
        seen_ids.add(problem_id)

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "problems": normalized,
        "problem": normalized[0] if len(normalized) == 1 else None,
        "count": len(normalized),
    }


def create_problem_from_content(content: str, overwrite: bool = False) -> dict[str, Any]:
    parse_warnings: list[str] = []
    problem = parse_problem_content(content, warnings=parse_warnings)
    validation = validate_problem_spec(problem)
    validation["warnings"] = parse_warnings + validation["warnings"]
    if not validation["ok"]:
        return {
            "ok": False,
            "created": False,
            **validation,
        }

    normalized = validation["problem"]
    problem_id = normalized["id"]
    problem_dir = (PROBLEMS_DIR / problem_id).resolve()
    problems_root = PROBLEMS_DIR.resolve()
    if problems_root not in problem_dir.parents:
        return {
            "ok": False,
            "created": False,
            "errors": ["Resolved problem path is outside the problems directory."],
            "warnings": validation["warnings"],
            "problem": normalized,
        }

    path = problem_dir / "problem.json"
    if path.exists() and not overwrite:
        return {
            "ok": False,
            "created": False,
            "errors": [f"Problem '{problem_id}' already exists. Enable overwrite to replace it."],
            "warnings": validation["warnings"],
            "problem": normalized,
        }

    problem_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(format_problem_json(normalized) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "created": True,
        "problem_id": problem_id,
        "path": str(path),
        "errors": [],
        "warnings": validation["warnings"],
        "problem": normalized,
    }


def create_problem_collection_from_content(content: str, overwrite: bool = False) -> dict[str, Any]:
    parse_warnings: list[str] = []
    problems = parse_problem_collection(content, warnings=parse_warnings)
    validation = validate_problem_collection(problems)
    validation["warnings"] = parse_warnings + validation["warnings"]
    if not validation["ok"]:
        return {"ok": False, "created": False, "created_count": 0, "results": [], **validation}

    results: list[dict[str, Any]] = []
    batch_errors: list[str] = []
    created_count = 0
    for problem in validation["problems"]:
        item = _create_validated_problem(problem, overwrite=overwrite)
        results.append(item)
        if item["created"]:
            created_count += 1
        else:
            batch_errors.extend(item["errors"])

    ok = not batch_errors
    if len(results) == 1:
        single = results[0]
        return {
            **single,
            "created_count": created_count,
            "results": results,
            "warnings": validation["warnings"] + single.get("warnings", []),
        }

    return {
        "ok": ok,
        "created": ok and created_count == len(results),
        "created_count": created_count,
        "total": len(results),
        "results": results,
        "errors": batch_errors,
        "warnings": validation["warnings"],
        "problems": validation["problems"],
        "problem": None,
    }


def _create_validated_problem(normalized: dict[str, Any], overwrite: bool = False) -> dict[str, Any]:
    problem_id = normalized["id"]
    problem_dir = (PROBLEMS_DIR / problem_id).resolve()
    problems_root = PROBLEMS_DIR.resolve()
    if problems_root not in problem_dir.parents:
        return {
            "ok": False,
            "created": False,
            "problem_id": problem_id,
            "errors": ["Resolved problem path is outside the problems directory."],
            "warnings": [],
            "problem": normalized,
        }

    path = problem_dir / "problem.json"
    if path.exists() and not overwrite:
        return {
            "ok": False,
            "created": False,
            "problem_id": problem_id,
            "errors": [f"Problem '{problem_id}' already exists. Enable overwrite to replace it."],
            "warnings": [],
            "problem": normalized,
        }

    problem_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(format_problem_json(normalized) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "created": True,
        "problem_id": problem_id,
        "path": str(path),
        "errors": [],
        "warnings": [],
        "problem": normalized,
    }


def _normalize_scalar_fields(problem: dict[str, Any], warnings: list[str]) -> None:
    for key in ("id", "title", "difficulty", "entry_kind", "function_name"):
        value = problem.get(key)
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if key in {"difficulty", "entry_kind"}:
            stripped = stripped.lower()
        if stripped != value:
            problem[key] = stripped
            _warn(warnings, f"Normalized whitespace/case in {key}.")


def _require_string(problem: dict[str, Any], key: str, errors: list[str]) -> None:
    if not isinstance(problem.get(key), str) or not problem.get(key, "").strip():
        errors.append(f"{key} is required and must be a non-empty string.")


def _validate_function_problem(problem: dict[str, Any], errors: list[str]) -> None:
    function_name = problem.get("function_name")
    if not isinstance(function_name, str) or not FUNCTION_RE.match(function_name):
        errors.append("function_name is required for function problems and must be a valid Python identifier.")
    elif function_name:
        for field in ("starter_code", "reference_solution"):
            ok, syntax_error = _code_defines_function(problem.get(field), function_name)
            if syntax_error:
                errors.append(
                    f"{field} has invalid Python syntax: {syntax_error.msg} at line {syntax_error.lineno}."
                )
            elif not ok:
                errors.append(f"{field} must define function `{function_name}`.")
        starter_errors = _function_signature_type_errors(problem.get("starter_code"), function_name)
        errors.extend(starter_errors)
    arg_bounds = _function_arg_bounds(problem, function_name) if isinstance(function_name, str) else None
    arg_names = _function_arg_names(problem, function_name) if isinstance(function_name, str) else []
    _validate_runtime_type_fields(problem, arg_names, errors)

    for group_name in ("visible_tests", "hidden_tests"):
        tests = problem.get(group_name, [])
        if not isinstance(tests, list):
            continue
        for idx, test in enumerate(tests):
            prefix = f"{group_name}[{idx}]"
            if not isinstance(test, dict):
                errors.append(f"{prefix} must be an object.")
                continue
            if "args" not in test or not isinstance(test.get("args"), list):
                errors.append(f"{prefix}.args must be a list of positional arguments.")
            elif arg_bounds:
                min_args, max_args = arg_bounds
                arg_count = len(test["args"])
                if arg_count < min_args or (max_args is not None and arg_count > max_args):
                    expected = f"{min_args}" if max_args == min_args else f"{min_args}-{max_args}" if max_args is not None else f"at least {min_args}"
                    errors.append(f"{prefix}.args has {arg_count} item(s), but {function_name} expects {expected} positional argument(s).")
            if "expected" not in test:
                errors.append(f"{prefix}.expected is required.")


def _function_arg_bounds(problem: dict[str, Any], function_name: str) -> tuple[int, int | None] | None:
    for field in ("starter_code", "reference_solution"):
        code = problem.get(field)
        if not isinstance(code, str):
            continue
        try:
            tree = ast.parse(code)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                args = list(node.args.posonlyargs) + list(node.args.args)
                if args and args[0].arg == "self":
                    args = args[1:]
                required = len(args) - len(node.args.defaults)
                maximum = None if node.args.vararg else len(args)
                return max(0, required), maximum
    return None


def _function_arg_names(problem: dict[str, Any], function_name: str) -> list[str]:
    for field in ("starter_code", "reference_solution"):
        code = problem.get(field)
        if not isinstance(code, str):
            continue
        try:
            tree = ast.parse(code)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                args = list(node.args.posonlyargs) + list(node.args.args)
                if args and args[0].arg == "self":
                    args = args[1:]
                return [arg.arg for arg in args]
    return []


def _code_defines_function(code: Any, function_name: str) -> tuple[bool, SyntaxError | None]:
    if not isinstance(code, str):
        return False, None
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, exc
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return True, None
    return False, None


def _function_signature_type_errors(code: Any, function_name: str) -> list[str]:
    if not isinstance(code, str):
        return []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            errors: list[str] = []
            args = list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs)
            for arg in args:
                if arg.arg == "self":
                    continue
                if arg.annotation is None:
                    errors.append(f"starter_code function `{function_name}` must type-annotate parameter `{arg.arg}`.")
            if node.args.vararg and node.args.vararg.annotation is None:
                errors.append(f"starter_code function `{function_name}` must type-annotate parameter `*{node.args.vararg.arg}`.")
            if node.args.kwarg and node.args.kwarg.annotation is None:
                errors.append(f"starter_code function `{function_name}` must type-annotate parameter `**{node.args.kwarg.arg}`.")
            if node.returns is None:
                errors.append(f"starter_code function `{function_name}` must include a return type annotation.")
            return errors
    return []


def _validate_requirements(requirements: list[Any], errors: list[str], warnings: list[str]) -> None:
    for idx, req in enumerate(requirements):
        prefix = f"requirements[{idx}]"
        if isinstance(req, str):
            if _looks_like_problem_instruction(req):
                errors.append(
                    f"{prefix} looks like a problem instruction, not a package dependency. "
                    "Move it to constraints. Package requirements should look like "
                    '{"package":"numpy","pip":"numpy>=2.0","import_name":"numpy"}.'
                )
            else:
                warnings.append(f"{prefix} is a string package spec. Object form is preferred for clarity.")
            continue
        if not isinstance(req, dict):
            errors.append(f"{prefix} must be a package object or string package spec.")
            continue
        for key in ("package", "pip", "import_name"):
            if not isinstance(req.get(key), str) or not req.get(key, "").strip():
                errors.append(f"{prefix}.{key} must be a non-empty string.")
        import_name = req.get("import_name")
        if isinstance(import_name, str) and import_name.strip() and not IMPORT_NAME_RE.match(import_name):
            errors.append(f"{prefix}.import_name must be a valid Python import path.")


def _validate_checker(checker: Any, errors: list[str]) -> None:
    if checker is None:
        return
    if not isinstance(checker, dict):
        errors.append("checker must be an object.")
        return
    checker_type = checker.get("type", "exact")
    if checker_type not in {"exact", "allclose", "unordered_nested"}:
        errors.append("checker.type must be one of: exact, allclose, unordered_nested.")
    for key in ("atol", "rtol"):
        if key in checker and not isinstance(checker[key], (int, float)):
            errors.append(f"checker.{key} must be a number.")


def _validate_complexity(complexity: Any, errors: list[str]) -> None:
    if not isinstance(complexity, dict):
        errors.append("complexity must be an object with time and space strings.")
        return
    for key in ("time", "space"):
        if not isinstance(complexity.get(key), str) or not complexity.get(key, "").strip():
            errors.append(f"complexity.{key} must be a non-empty string.")


def _validate_unit_test_problem(problem: dict[str, Any], errors: list[str]) -> None:
    for group_name in ("visible_tests", "hidden_tests"):
        tests = problem.get(group_name, [])
        if not isinstance(tests, list):
            continue
        for idx, test in enumerate(tests):
            prefix = f"{group_name}[{idx}]"
            if not isinstance(test, dict):
                errors.append(f"{prefix} must be an object.")
                continue
            if not isinstance(test.get("code"), str) or not test.get("code", "").strip():
                errors.append(f"{prefix}.code must be a non-empty Python test string.")


def _validate_runtime_type_fields(problem: dict[str, Any], arg_names: list[str], errors: list[str]) -> None:
    arg_types = problem.get("arg_types")
    if arg_types is not None:
        if not isinstance(arg_types, list):
            errors.append("arg_types must be a list when provided.")
        else:
            if arg_names and len(arg_types) != len(arg_names):
                errors.append(f"arg_types has {len(arg_types)} item(s), but function_name expects {len(arg_names)} argument(s).")
            for idx, type_spec in enumerate(arg_types):
                if not _valid_runtime_type_spec(type_spec):
                    errors.append(f"arg_types[{idx}] must be a supported type string or {{\"type\":\"...\",\"dtype\":\"...\"}} object.")

    if "return_type" in problem and not _valid_runtime_type_spec(problem.get("return_type")):
        errors.append("return_type must be a supported type string or {\"type\":\"...\",\"dtype\":\"...\"} object.")


def _valid_runtime_type_spec(type_spec: Any) -> bool:
    if isinstance(type_spec, str):
        return _runtime_type_supported(type_spec)
    if isinstance(type_spec, dict):
        type_name = type_spec.get("type")
        dtype = type_spec.get("dtype")
        return (
            isinstance(type_name, str)
            and _runtime_type_supported(type_name)
            and (dtype is None or isinstance(dtype, str))
        )
    return False


def _runtime_type_supported(type_name: str) -> bool:
    key = _runtime_type_key(type_name)
    if key in {_runtime_type_key(item) for item in SUPPORTED_RUNTIME_TYPES}:
        return True
    return key.startswith(("list[", "dict[", "tuple[", "set[", "frozenset["))


def _validate_statement_math(statement: Any, warnings: list[str]) -> None:
    if not isinstance(statement, str) or "$" not in statement:
        return
    cleaned = _strip_markdown_code(statement)
    for segment in _inline_math_segments(cleaned):
        if not _inline_math_should_be_display(segment):
            continue
        _warn(
            warnings,
            "statement has long inline math that may read better as display math: "
            f"${_short_inline_math(segment)}$. Short inline equations are accepted."
        )


def _strip_markdown_code(text: str) -> str:
    without_fences = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return re.sub(r"`[^`]*`", "", without_fences)


def _inline_math_segments(text: str) -> list[str]:
    return [match.group(1).strip() for match in INLINE_MATH_RE.finditer(text) if match.group(1).strip()]


def _inline_math_should_be_display(segment: str) -> bool:
    stripped = segment.strip()
    if "\n" in stripped:
        return True
    if len(stripped) > 96:
        return True
    if DISPLAY_MATH_COMMAND_RE.search(stripped) and len(stripped) > 48:
        return True
    operator_count = sum(stripped.count(op) for op in ("+", "-", "*", "/", "^", "\\cdot", "\\times"))
    return len(stripped) > 60 and operator_count >= 3


def _short_inline_math(segment: str) -> str:
    compact = " ".join(segment.split())
    return compact if len(compact) <= 80 else compact[:77] + "..."


def _verify_reference_solution_outputs(problem: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    reference_solution = problem.get("reference_solution") or problem.get("solution")
    if not isinstance(reference_solution, str) or not reference_solution.strip():
        errors.append("reference_solution is required for deterministic verification.")
        return

    try:
        from app.judge import judge_code
    except Exception as exc:  # noqa: BLE001 - verifier should report infrastructure failures clearly.
        warnings.append(f"Skipped reference_solution verification because the judge could not be loaded: {exc}")
        return

    result = judge_code(problem, reference_solution, "submit").as_dict()
    status = result.get("status")
    if status == "Accepted":
        return

    if status == "Missing Dependencies":
        message = result.get("error") or "required packages are missing"
        warnings.append(f"Skipped reference_solution execution because dependencies are missing: {message}")
        return

    refs = _reference_test_refs(problem)
    failed = [
        (idx, test)
        for idx, test in enumerate(result.get("tests") or [])
        if not test.get("passed")
    ]

    if not failed:
        message = result.get("error") or status or "unknown judge failure"
        errors.append(f"reference_solution verification failed: {message}")
        return

    corrected = 0
    for idx, test in failed:
        ref = refs[idx] if idx < len(refs) else None
        label = ref["label"] if ref else f"test[{idx}]"
        if test.get("error"):
            errors.append(f"reference_solution raises an error on {label}: {_first_error_line(test['error'])}")
            continue
        if ref and "actual" in test:
            problem[ref["group"]][ref["index"]]["expected"] = test.get("actual")
            corrected += 1
            warnings.append(
                "Corrected expected output from reference_solution on "
                f"{label}: expected {_short_json(test.get('expected'))}, "
                f"actual {_short_json(test.get('actual'))}."
            )
            continue
        errors.append(
            "reference_solution output mismatch on "
            f"{label}: expected {_short_json(test.get('expected'))}, "
            f"actual {_short_json(test.get('actual'))}."
        )

    if corrected:
        warnings.append(f"Updated {corrected} test expected output(s) using reference_solution.")


def _reference_test_labels(problem: dict[str, Any]) -> list[str]:
    return [item["label"] for item in _reference_test_refs(problem)]


def _reference_test_refs(problem: dict[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for group_name in ("visible_tests", "hidden_tests"):
        tests = problem.get(group_name)
        if not isinstance(tests, list):
            continue
        for idx, test in enumerate(tests):
            name = ""
            if isinstance(test, dict):
                name = str(test.get("name") or "").strip()
            refs.append(
                {
                    "group": group_name,
                    "index": idx,
                    "label": f"{group_name}[{idx}]" + (f" ({name})" if name else ""),
                }
            )
    return refs

def _first_error_line(error: Any) -> str:
    text = str(error).strip()
    if not text:
        return "unknown error"
    for line in reversed(text.splitlines()):
        if line.strip():
            return line.strip()[:500]
    return text[:500]


def _short_json(value: Any, max_chars: int = 500) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, default=str)
    except TypeError:
        text = str(value)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def format_problem_json(value: Any) -> str:
    return dumps_compact_json(value, ensure_ascii=False)


def _normalize_problem_fields(problem: dict[str, Any], warnings: list[str], checker_was_missing: bool) -> None:
    _normalize_text_and_code_fields(problem, warnings)
    _infer_missing_function_name(problem, warnings)
    _normalize_runtime_type_aliases(problem, warnings)
    _normalize_function_test_aliases(problem, warnings)
    _move_instruction_requirements_to_constraints(problem, warnings)
    _infer_package_requirements(problem, warnings)
    _complete_package_requirements(problem, warnings)
    _ensure_declared_package_imports(problem, warnings)
    _infer_numeric_checker(problem, warnings, checker_was_missing)
    _relax_numeric_checker_tolerance(problem, warnings)
    _infer_unordered_nested_checker(problem, warnings, checker_was_missing)
    _fill_missing_expected_outputs(problem, warnings)


def _normalize_runtime_type_aliases(problem: dict[str, Any], warnings: list[str]) -> None:
    if "input_types" in problem and "arg_types" not in problem:
        problem["arg_types"] = problem.pop("input_types")
        _warn(warnings, "Renamed input_types to arg_types.")
    if "parameter_types" in problem and "arg_types" not in problem:
        problem["arg_types"] = problem.pop("parameter_types")
        _warn(warnings, "Renamed parameter_types to arg_types.")
    if "output_type" in problem and "return_type" not in problem:
        problem["return_type"] = problem.pop("output_type")
        _warn(warnings, "Renamed output_type to return_type.")


def _infer_missing_function_name(problem: dict[str, Any], warnings: list[str]) -> None:
    if problem.get("entry_kind", "function") != "function":
        return
    if isinstance(problem.get("function_name"), str) and problem["function_name"].strip():
        return

    candidates: list[str] = []
    for field in ("starter_code", "reference_solution"):
        code = problem.get(field)
        if not isinstance(code, str):
            continue
        try:
            tree = ast.parse(code)
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                candidates.append(node.name)

    unique = _dedupe_preserving_order(candidates)
    problem_id = problem.get("id")
    if isinstance(problem_id, str) and problem_id in unique:
        problem["function_name"] = problem_id
        _warn(warnings, f"Inferred function_name `{problem_id}` from problem id and code.")
        return
    if len(unique) == 1:
        problem["function_name"] = unique[0]
        _warn(warnings, f"Inferred function_name `{unique[0]}` from code.")


def _normalize_function_test_aliases(problem: dict[str, Any], warnings: list[str]) -> None:
    if problem.get("entry_kind", "function") != "function":
        return
    function_name = problem.get("function_name")
    if not isinstance(function_name, str) or not function_name.strip():
        return

    arg_names = _function_arg_names(problem, function_name)
    for group_name in ("visible_tests", "hidden_tests"):
        tests = problem.get(group_name)
        if not isinstance(tests, list):
            continue
        for idx, test in enumerate(tests):
            if not isinstance(test, dict):
                continue

            if "expected" not in test:
                expected_key = _expected_value_key(test)
                if expected_key:
                    test["expected"] = test.pop(expected_key)
                    _warn(warnings, f"Converted {group_name}[{idx}].{expected_key} to expected.")

            if "args" in test and isinstance(test.get("args"), dict):
                args = _coerce_test_input_to_args(test["args"], arg_names)
                if args is not None:
                    test["args"] = args
                    _warn(warnings, f"Converted {group_name}[{idx}].args object to positional args.")
                continue

            if "args" in test and isinstance(test.get("args"), list):
                if len(arg_names) == 1 and len(test["args"]) != 1:
                    test["args"] = [test["args"]]
                    _warn(warnings, f"Wrapped {group_name}[{idx}].args as one positional list argument.")
                continue

            if "args" not in test:
                input_key = _first_existing_key(
                    test,
                    (
                        "input",
                        "inputs",
                        "test_input",
                        "input_data",
                        "input_value",
                        "input_values",
                        "arguments",
                        "params",
                        "parameters",
                        "case",
                        "given",
                    ),
                )
                if input_key:
                    args = _coerce_test_input_to_args(test.pop(input_key), arg_names)
                    if args is not None:
                        test["args"] = args
                        _warn(warnings, f"Converted {group_name}[{idx}].{input_key} to args.")
                    continue

                if arg_names and all(name in test for name in arg_names):
                    test["args"] = [test[name] for name in arg_names]
                    _warn(warnings, f"Converted named argument fields in {group_name}[{idx}] to args.")
                    continue

                inferred_key = _single_input_value_key(test, arg_names)
                if inferred_key:
                    test["args"] = [test[inferred_key]]
                    _warn(warnings, f"Inferred {group_name}[{idx}].{inferred_key} as the single positional argument.")


def _first_existing_key(data: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        if key in data:
            return key
    return None


def _expected_value_key(test: dict[str, Any]) -> str | None:
    direct = _first_existing_key(
        test,
        (
            "expected_output",
            "expected_result",
            "expected_value",
            "expected_values",
            "expected_answer",
            "expected_counts",
            "expected_count",
            "expected_frequency",
            "expected_frequencies",
            "output",
            "outputs",
            "output_data",
            "answer",
            "result",
            "return",
            "returns",
        ),
    )
    if direct:
        return direct

    for key in test:
        normalized = key.lower().replace("-", "_")
        if normalized != "expected" and normalized.startswith("expected_"):
            return key
    return None


def _single_input_value_key(test: dict[str, Any], arg_names: list[str]) -> str | None:
    if len(arg_names) != 1:
        return None

    metadata = {
        "name",
        "description",
        "explanation",
        "note",
        "notes",
        "args",
        "expected",
        "code",
    }
    candidates = []
    for key in test:
        normalized = key.lower().replace("-", "_")
        if normalized in metadata:
            continue
        if normalized.startswith("expected") or normalized.startswith("output") or normalized in {"answer", "result"}:
            continue
        candidates.append(key)
    return candidates[0] if len(candidates) == 1 else None


def _coerce_test_input_to_args(value: Any, arg_names: list[str]) -> list[Any] | None:
    if isinstance(value, dict):
        if arg_names and all(name in value for name in arg_names):
            return [value[name] for name in arg_names]
        if len(arg_names) == 1:
            return [value]
        return None

    if isinstance(value, list):
        if len(arg_names) == 1:
            return [value]
        return value

    if len(arg_names) == 1:
        return [value]
    return None


def _fill_missing_expected_outputs(problem: dict[str, Any], warnings: list[str]) -> None:
    if problem.get("entry_kind", "function") != "function":
        return

    missing: list[tuple[str, int, dict[str, Any]]] = []
    for group_name in ("visible_tests", "hidden_tests"):
        tests = problem.get(group_name)
        if not isinstance(tests, list):
            continue
        for idx, test in enumerate(tests):
            if isinstance(test, dict) and "expected" not in test and isinstance(test.get("args"), list):
                missing.append((group_name, idx, test))
    if not missing:
        return

    try:
        from app.judge import generate_expected_output
    except Exception as exc:  # noqa: BLE001 - verifier should stay usable if judge import fails.
        _warn(warnings, f"Could not auto-fill expected outputs because the judge could not be loaded: {exc}")
        return

    for group_name, idx, test in missing:
        result = generate_expected_output(problem, test["args"])
        if not result.get("ok"):
            _warn(warnings, f"Could not auto-fill {group_name}[{idx}].expected: {result.get('error')}")
            continue
        test["expected"] = result.get("expected")
        _warn(warnings, f"Auto-filled {group_name}[{idx}].expected from reference_solution.")


def _normalize_text_and_code_fields(problem: dict[str, Any], warnings: list[str]) -> None:
    for field in ("statement", "solution_explanation"):
        value = problem.get(field)
        if not isinstance(value, str):
            continue
        fixed, changed, suspicious = _normalize_markdown_newline_markers(value)
        if changed:
            problem[field] = fixed
            _warn(warnings, f"Normalized escaped newline markers in {field}.")
        if suspicious:
            _warn(warnings, f"{field} still contains literal \\n text; check whether it is intended LaTeX or a double-escaped newline.")

    for field in ("starter_code", "reference_solution"):
        value = problem.get(field)
        if not isinstance(value, str):
            continue
        fixed, changed = _normalize_python_code_newline_markers(value)
        if changed:
            problem[field] = fixed
            _warn(warnings, f"Normalized escaped newline markers in {field}.")

    for group_name in ("visible_tests", "hidden_tests"):
        tests = problem.get(group_name)
        if not isinstance(tests, list):
            continue
        for idx, test in enumerate(tests):
            if not isinstance(test, dict) or not isinstance(test.get("code"), str):
                continue
            fixed, changed = _normalize_python_code_newline_markers(test["code"])
            if changed:
                test["code"] = fixed
                _warn(warnings, f"Normalized escaped newline markers in {group_name}[{idx}].code.")


def _normalize_markdown_newline_markers(text: str) -> tuple[str, bool, bool]:
    if "\\n" not in text:
        return text, False, False

    def replace_run(match: re.Match[str]) -> str:
        return "\n" * (len(match.group(0)) // 2)

    fixed = re.sub(r"(?:\\n){2,}", replace_run, text)
    fixed = re.sub(r"\\n(?=$|[^a-z])", "\n", fixed)
    suspicious = bool(re.search(r"\\n(?=$|[^a-z])", fixed))
    return fixed, fixed != text, suspicious


def _normalize_python_code_newline_markers(code: str) -> tuple[str, bool]:
    if "\\n" not in code and "\\r\\n" not in code and "\\t" not in code:
        return code, False
    if _python_code_parses(code):
        return code, False

    fixed = code.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "\t")
    if fixed != code and _python_code_parses(fixed):
        return fixed, True
    return code, False


def _python_code_parses(code: str) -> bool:
    try:
        ast.parse(code)
    except SyntaxError:
        return False
    return True


def _move_instruction_requirements_to_constraints(problem: dict[str, Any], warnings: list[str]) -> None:
    requirements = problem.get("requirements")
    constraints = problem.get("constraints")
    if not isinstance(requirements, list):
        return

    kept_requirements: list[Any] = []
    moved_constraints: list[str] = []

    for req in requirements:
        if isinstance(req, str):
            text = req.strip()
            if not text:
                continue
            if _looks_like_problem_instruction(text):
                moved_constraints.append(text)
            else:
                kept_requirements.append(_package_requirement_from_spec(text))
            continue
        kept_requirements.append(req)

    if moved_constraints and isinstance(constraints, list):
        existing = {str(item).strip() for item in constraints if isinstance(item, str)}
        for constraint in moved_constraints:
            if constraint not in existing:
                constraints.append(constraint)
                existing.add(constraint)
        warnings.append(f"Moved {len(moved_constraints)} instruction-like requirements to constraints.")

    if kept_requirements != requirements:
        problem["requirements"] = kept_requirements


def _infer_package_requirements(problem: dict[str, Any], warnings: list[str]) -> None:
    requirements = problem.get("requirements")
    if not isinstance(requirements, list):
        return

    existing = {
        str(req.get("package") or req.get("import_name") or req.get("pip") or "").lower()
        for req in requirements
        if isinstance(req, dict)
    }
    existing.update(
        str(req).split("=", 1)[0].split("<", 1)[0].split(">", 1)[0].strip().lower()
        for req in requirements
        if isinstance(req, str)
    )

    inferred: list[dict[str, str]] = []
    for candidate in _dependency_candidates(problem):
        requirement = KNOWN_PACKAGE_REQUIREMENTS.get(candidate)
        if not requirement:
            continue
        package_key = requirement["package"].lower()
        import_key = requirement["import_name"].lower()
        if package_key in existing or import_key in existing:
            continue
        requirements.append(dict(requirement))
        inferred.append(requirement)
        existing.update({package_key, import_key})

    if inferred:
        labels = ", ".join(req["package"] for req in inferred)
        warnings.append(f"Inferred package requirement(s): {labels}.")


def _complete_package_requirements(problem: dict[str, Any], warnings: list[str]) -> None:
    requirements = problem.get("requirements")
    if not isinstance(requirements, list):
        return

    completed: list[Any] = []
    changed = False
    for req in requirements:
        requirement = _requirement_object(req)
        if requirement:
            completed.append(requirement)
            changed = changed or requirement != req
        else:
            completed.append(req)

    if changed:
        problem["requirements"] = completed
        _warn(warnings, "Normalized package requirement objects to package/pip/import_name.")


def _ensure_declared_package_imports(problem: dict[str, Any], warnings: list[str]) -> None:
    requirements = problem.get("requirements")
    if not isinstance(requirements, list):
        return

    required_imports = _declared_imports(requirements)
    if not required_imports:
        return

    for field in ("starter_code", "reference_solution"):
        code = problem.get(field)
        if not isinstance(code, str) or not code.strip():
            continue

        missing = [
            item
            for item in required_imports
            if not _code_imports_requirement(code, item["import_name"])
        ]
        if not missing:
            continue

        snippets = _dedupe_preserving_order(item["snippet"] for item in missing)
        labels = ", ".join(_dedupe_preserving_order(item["label"] for item in missing))
        problem[field] = "\n".join(snippets) + "\n\n" + code.lstrip()
        _warn(warnings, f"Added missing package import(s) to {field}: {labels}.")


def _declared_imports(requirements: list[Any]) -> list[dict[str, str]]:
    imports: list[dict[str, str]] = []
    seen: set[str] = set()

    for req in requirements:
        requirement = _requirement_object(req)
        if not requirement:
            continue
        import_name = requirement["import_name"]
        if not IMPORT_NAME_RE.match(import_name):
            continue
        top_level = import_name.split(".", 1)[0]
        key = top_level.lower()
        if key in seen:
            continue
        seen.add(key)
        imports.append(
            {
                "import_name": import_name,
                "snippet": KNOWN_IMPORT_SNIPPETS.get(key, f"import {import_name}"),
                "label": requirement["package"],
            }
        )

    return imports


def _requirement_object(req: Any) -> dict[str, str] | None:
    if isinstance(req, str):
        if _looks_like_problem_instruction(req):
            return None
        return _package_requirement_from_spec(req)
    if not isinstance(req, dict):
        return None

    package = str(req.get("package") or "").strip()
    pip = str(req.get("pip") or "").strip()
    import_name = str(req.get("import_name") or "").strip()

    if not package and pip:
        package = _package_name_from_pip_spec(pip)
    if not package:
        return None

    mapped = KNOWN_PACKAGE_REQUIREMENTS.get(_normalize_dependency_name(package))
    if mapped:
        package = package or mapped["package"]
        pip = pip or mapped["pip"]
        import_name = import_name or mapped["import_name"]

    if not pip:
        pip = package
    if not import_name:
        import_name = package.replace("-", "_")

    return {
        "package": package,
        "pip": pip,
        "import_name": import_name,
    }


def _package_name_from_pip_spec(spec: str) -> str:
    package_match = re.match(r"\s*([A-Za-z0-9_.-]+)", spec)
    return package_match.group(1) if package_match else spec.strip()


def _code_imports_requirement(code: str, import_name: str) -> bool:
    top_level = import_name.split(".", 1)[0].lower()
    modules = _imported_top_level_modules(code)
    if top_level in modules or import_name.lower() in modules:
        return True

    escaped = re.escape(top_level)
    return bool(
        re.search(rf"^\s*import\s+{escaped}(?:[.\s]|$)", code, re.MULTILINE)
        or re.search(rf"^\s*from\s+{escaped}(?:[.\s]|$)", code, re.MULTILINE)
    )


def _dedupe_preserving_order(values: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value)
        if text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _infer_numeric_checker(problem: dict[str, Any], warnings: list[str], checker_was_missing: bool) -> None:
    if not checker_was_missing:
        return
    if not _looks_like_numeric_array_problem(problem):
        return
    problem["checker"] = {"type": "allclose", "atol": DEFAULT_FLOAT_ATOL, "rtol": DEFAULT_FLOAT_RTOL}
    warnings.append("Inferred checker allclose for numeric array/tensor style outputs.")


def _relax_numeric_checker_tolerance(problem: dict[str, Any], warnings: list[str]) -> None:
    checker = problem.get("checker")
    if not isinstance(checker, dict) or checker.get("type") != "allclose":
        return
    if not _looks_like_numeric_array_problem(problem):
        return

    changed = False
    for key, minimum in (("atol", DEFAULT_FLOAT_ATOL), ("rtol", DEFAULT_FLOAT_RTOL)):
        value = checker.get(key)
        if not isinstance(value, (int, float)) or float(value) < minimum:
            checker[key] = minimum
            changed = True

    if changed:
        warnings.append("Relaxed allclose tolerance to 1e-5 for numeric array/tensor style outputs.")


def _infer_unordered_nested_checker(problem: dict[str, Any], warnings: list[str], checker_was_missing: bool) -> None:
    if not checker_was_missing:
        return
    text = " ".join(
        str(problem.get(key, ""))
        for key in ("id", "title", "function_name", "statement", "solution_explanation")
    ).lower()
    tags = " ".join(str(tag).lower() for tag in problem.get("tags", []) if isinstance(tag, str))
    combined = f"{text} {tags}"
    if "anagram" not in combined and "group" not in combined:
        return
    tests = [
        test
        for group_name in ("visible_tests", "hidden_tests")
        for test in problem.get(group_name, [])
        if isinstance(test, dict)
    ]
    expected_values = [test.get("expected") for test in tests if "expected" in test]
    if not expected_values or not all(_is_nested_list(value) for value in expected_values):
        return
    problem["checker"] = {"type": "unordered_nested"}
    warnings.append("Inferred checker unordered_nested for grouped unordered outputs.")


def _is_nested_list(value: Any) -> bool:
    return isinstance(value, list) and any(isinstance(item, list) for item in value)


def _looks_like_problem_instruction(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    return not bool(PACKAGE_SPEC_RE.match(stripped))


def _package_requirement_from_spec(spec: str) -> dict[str, str]:
    package_match = re.match(r"\s*([A-Za-z0-9_.-]+)", spec)
    package = package_match.group(1) if package_match else spec.strip()
    mapped = KNOWN_PACKAGE_REQUIREMENTS.get(package.lower())
    if mapped:
        return {**mapped, "pip": spec.strip() or mapped["pip"]}
    return {
        "package": package,
        "pip": spec.strip() or package,
        "import_name": package.replace("-", "_"),
    }


def _dependency_candidates(problem: dict[str, Any]) -> set[str]:
    candidates: set[str] = set()

    for tag in problem.get("tags", []):
        if isinstance(tag, str):
            candidates.add(_normalize_dependency_name(tag))

    for field in ("starter_code", "reference_solution"):
        code = problem.get(field)
        if isinstance(code, str):
            candidates.update(_imported_top_level_modules(code))

    for type_spec in _runtime_type_specs(problem):
        key = _runtime_type_key(_runtime_type_name(type_spec))
        if key.startswith("numpy.") or key.startswith("np.") or key in {"ndarray"}:
            candidates.add("numpy")
        elif key.startswith("torch.") or key == "tensor":
            candidates.add("torch")
        elif key.startswith("pandas.") or key.startswith("pd.") or key in {"dataframe", "series"}:
            candidates.add("pandas")

    text = " ".join(
        str(problem.get(field, ""))
        for field in ("title", "statement", "solution_explanation")
    ).lower()
    for keyword in TEXT_DEPENDENCY_KEYWORDS:
        pattern = rf"(?<![a-z0-9_]){re.escape(keyword)}(?![a-z0-9_])"
        if re.search(pattern, text):
            candidates.add(keyword)

    return {candidate for candidate in candidates if candidate}


def _runtime_type_specs(problem: dict[str, Any]) -> list[Any]:
    specs: list[Any] = []
    arg_types = problem.get("arg_types")
    if isinstance(arg_types, list):
        specs.extend(arg_types)
    if "return_type" in problem:
        specs.append(problem.get("return_type"))
    return specs


def _runtime_type_name(type_spec: Any) -> str:
    if isinstance(type_spec, dict):
        return str(type_spec.get("type") or "")
    return str(type_spec or "")


def _runtime_type_key(type_name: str) -> str:
    return type_name.strip().replace(" ", "").lower()


def _normalize_dependency_name(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _imported_top_level_modules(code: str) -> set[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()

    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".", 1)[0].lower())
                if alias.asname:
                    modules.add(alias.asname.lower())
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".", 1)[0].lower())
    return modules


def _looks_like_numeric_array_problem(problem: dict[str, Any]) -> bool:
    candidates = _dependency_candidates(problem)
    if candidates.intersection({"numpy", "np", "torch", "pytorch"}):
        return True
    tests = []
    if isinstance(problem.get("visible_tests"), list):
        tests.extend(problem["visible_tests"])
    if isinstance(problem.get("hidden_tests"), list):
        tests.extend(problem["hidden_tests"])
    return any(_contains_float(test.get("expected")) for test in tests if isinstance(test, dict))


def _contains_float(value: Any) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    return False
