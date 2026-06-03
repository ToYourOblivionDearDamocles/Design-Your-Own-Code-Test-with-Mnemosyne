from __future__ import annotations

import re
from typing import Any

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
    "complex",
    "builtins.complex",
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
    "numpy.typing.NDArray",
    "npt.NDArray",
    "NDArray",
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
    "scipy.sparse.csr_matrix",
    "scipy.sparse.csc_matrix",
    "scipy.sparse.coo_matrix",
    "sparse.csr_matrix",
    "sparse.csc_matrix",
    "sparse.coo_matrix",
    "sp.csr_matrix",
    "sp.csc_matrix",
    "sp.coo_matrix",
    "csr_matrix",
    "csc_matrix",
    "coo_matrix",
}

FUNCTION_TEST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "args", "expected"],
    "properties": {
        "name": {"type": "string"},
        "args": {
            "type": "array",
            "minItems": 0,
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
    "theory": "## Key Idea\n\nSquaring a number multiplies it by itself. The total is the sum of those squared values.",
    "examples": [
        {
            "name": "Walkthrough: basic list",
            "body": "For `nums = [1, 2, 3]`, compute `1^2 + 2^2 + 3^2 = 14`.",
        }
    ],
    "solution_explanation": "Square each number and add the results.",
    "complexity": {
        "time": "O(n)",
        "space": "O(1)",
    },
    "visible_tests": [
        {"name": "basic", "args": [[1, 2, 3]], "expected": 14},
        {"name": "empty", "args": [[]], "expected": 0},
        {"name": "negative values", "args": [[-2, 4]], "expected": 20},
    ],
    "hidden_tests": [],
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
            "theory",
            "examples",
            "solution_explanation",
            "complexity",
            "visible_tests",
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
            "theory": {"type": "string"},
            "examples": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "anyOf": [
                        {"type": "string"},
                        {
                            "type": "object",
                            "additionalProperties": True,
                            "properties": {
                                "name": {"type": "string"},
                                "title": {"type": "string"},
                                "body": {"type": "string"},
                                "walkthrough": {"type": "string"},
                                "explanation": {"type": "string"},
                            },
                        },
                    ]
                },
            },
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
                "minItems": 0,
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
