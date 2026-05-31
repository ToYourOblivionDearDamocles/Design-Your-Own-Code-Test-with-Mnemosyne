from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.judge import generate_expected_output, judge_code
from app.problem_authoring import PROBLEM_TEMPLATE, validate_problem_spec


def main() -> int:
    cases = [
        numpy_matrix_vector_case(),
        numpy_nested_object_output_case(),
        torch_tensor_output_case(),
        torch_scalar_output_case(),
        pandas_series_output_case(),
        pandas_dataframe_output_case(),
        pandas_series_input_case(),
        tuple_interface_case(),
        namespace_input_case(),
        dataclass_output_case(),
        namedtuple_output_case(),
        set_output_case(),
    ]

    failed = 0
    ran = 0
    skipped = 0
    for case in cases:
        name = case["name"]
        if case.get("skip"):
            skipped += 1
            print(f"SKIP {name}: {case['skip']}")
            continue
        ran += 1
        try:
            detail = run_case(case)
            print(f"PASS {name}: {detail}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {name}: {exc}")

    print(f"Summary: {ran} ran, {skipped} skipped, {failed} failed")
    return 1 if failed else 0


def run_case(case: dict[str, Any]) -> str:
    problem = case["problem"]
    validation = validate_problem_spec(problem)
    assert validation["ok"], validation
    fixed = validation["problem"]

    judged = judge_code(fixed, fixed["reference_solution"], "submit").as_dict()
    assert judged["status"] == "Accepted", judged

    first_args = fixed["visible_tests"][0]["args"]
    generated = generate_expected_output(fixed, first_args)
    assert generated["ok"], generated

    if "first_actual" in case:
        assert generated["expected"] == case["first_actual"], generated

    return f"{judged['passed']}/{judged['total']} tests, generated expected ok"


def base_problem(
    *,
    problem_id: str,
    title: str,
    function_name: str,
    tags: list[str],
    requirements: list[dict[str, str]],
    checker: dict[str, Any],
    statement_io: str,
    starter_code: str,
    reference_solution: str,
    visible_tests: list[dict[str, Any]],
    hidden_tests: list[dict[str, Any]],
    arg_types: list[Any] | None = None,
    return_type: Any | None = None,
    timeout_seconds: int = 3,
) -> dict[str, Any]:
    problem = copy.deepcopy(PROBLEM_TEMPLATE)
    problem.update(
        {
            "id": problem_id,
            "title": title,
            "difficulty": "medium",
            "entry_kind": "function",
            "function_name": function_name,
            "tags": tags,
            "requirements": requirements,
            "constraints": ["Keep inputs unmodified."],
            "checker": checker,
            "timeout_seconds": timeout_seconds,
            "statement": f"# {title}\n\nValidate a runtime interface used by ML-style practice tasks.\n\n## Input / Output\n\n{statement_io}",
            "starter_code": starter_code,
            "reference_solution": reference_solution,
            "solution_explanation": "Use the declared runtime interface and return the requested value.",
            "complexity": {"time": "O(n)", "space": "O(n)"},
            "visible_tests": visible_tests,
            "hidden_tests": hidden_tests,
        }
    )
    if arg_types is not None:
        problem["arg_types"] = arg_types
    if return_type is not None:
        problem["return_type"] = return_type
    return problem


def has_package(import_name: str) -> bool:
    return importlib.util.find_spec(import_name) is not None


def numpy_requirement() -> list[dict[str, str]]:
    return [{"package": "numpy", "pip": "numpy>=2.0", "import_name": "numpy"}]


def torch_requirement() -> list[dict[str, str]]:
    return [{"package": "torch", "pip": "torch", "import_name": "torch"}]


def pandas_requirement() -> list[dict[str, str]]:
    return [{"package": "pandas", "pip": "pandas", "import_name": "pandas"}]


def allclose_checker() -> dict[str, Any]:
    return {"type": "allclose", "atol": 1e-5, "rtol": 1e-5}


def numpy_matrix_vector_case() -> dict[str, Any]:
    if not has_package("numpy"):
        return {"name": "numpy ndarray matrix/vector input -> ndarray output", "skip": "numpy is not installed"}
    return {
        "name": "numpy ndarray matrix/vector input -> ndarray output",
        "first_actual": [4.0, 10.0],
        "problem": base_problem(
            problem_id="runtime_numpy_matvec",
            title="Runtime NumPy MatVec",
            function_name="matvec",
            tags=["python", "numpy", "linear_algebra"],
            requirements=numpy_requirement(),
            checker=allclose_checker(),
            arg_types=[{"type": "numpy.ndarray", "dtype": "float64"}, {"type": "numpy.ndarray", "dtype": "float64"}],
            return_type="numpy.ndarray",
            statement_io="- `A`: `numpy.ndarray`, a 2D matrix.\n- `x`: `numpy.ndarray`, a 1D vector.\n- Return: `numpy.ndarray`, the product `A @ x`.",
            starter_code="import numpy as np\n\ndef matvec(A: np.ndarray, x: np.ndarray) -> np.ndarray:\n    pass\n",
            reference_solution=(
                "import numpy as np\n\n"
                "def matvec(A, x):\n"
                "    assert isinstance(A, np.ndarray)\n"
                "    assert isinstance(x, np.ndarray)\n"
                "    assert A.dtype == np.float64\n"
                "    return A @ x\n"
            ),
            visible_tests=[{"name": "basic", "args": [[[1, 2], [3, 4]], [2, 1]], "expected": [4.0, 10.0]}],
            hidden_tests=[{"name": "identity", "args": [[[1, 0], [0, 1]], [5, -2]], "expected": [5.0, -2.0]}],
        ),
    }


def numpy_nested_object_output_case() -> dict[str, Any]:
    if not has_package("numpy"):
        return {"name": "numpy ndarray inputs -> dict containing ndarray and scalar", "skip": "numpy is not installed"}
    return {
        "name": "numpy ndarray inputs -> dict containing ndarray and scalar",
        "first_actual": {"weights": [2.0, 3.0], "bias": 0.5},
        "problem": base_problem(
            problem_id="runtime_numpy_model_summary",
            title="Runtime NumPy Model Summary",
            function_name="model_summary",
            tags=["python", "numpy", "machine_learning"],
            requirements=numpy_requirement(),
            checker=allclose_checker(),
            arg_types=["numpy.ndarray", "numpy.ndarray"],
            return_type="dict",
            statement_io="- `weights`: `numpy.ndarray`, learned weights.\n- `features`: `numpy.ndarray`, feature matrix.\n- Return: `dict`, with a vector and scalar numeric fields.",
            starter_code="import numpy as np\n\ndef model_summary(weights: np.ndarray, features: np.ndarray) -> dict[str, object]:\n    pass\n",
            reference_solution=(
                "import numpy as np\n\n"
                "def model_summary(weights, features):\n"
                "    assert hasattr(weights, 'shape')\n"
                "    return {'weights': weights.astype(float), 'bias': np.float64(features.mean())}\n"
            ),
            visible_tests=[{"name": "basic", "args": [[2, 3], [[0, 1]]], "expected": {"weights": [2.0, 3.0], "bias": 0.5}}],
            hidden_tests=[{"name": "negative", "args": [[-1, 4], [[2, 4]]], "expected": {"weights": [-1.0, 4.0], "bias": 3.0}}],
        ),
    }


def torch_tensor_output_case() -> dict[str, Any]:
    if not has_package("torch"):
        return {"name": "torch tensor input -> tensor output", "skip": "torch is not installed"}
    return {
        "name": "torch tensor input -> tensor output",
        "problem": base_problem(
            problem_id="runtime_torch_softmax",
            title="Runtime Torch Softmax",
            function_name="softmax_vector",
            tags=["python", "torch", "machine_learning"],
            requirements=torch_requirement(),
            checker=allclose_checker(),
            arg_types=[{"type": "torch.Tensor", "dtype": "float32"}],
            return_type="torch.Tensor",
            timeout_seconds=15,
            statement_io="- `logits`: `torch.Tensor`, a 1D float tensor.\n- Return: `torch.Tensor`, softmax probabilities.",
            starter_code="import torch\n\ndef softmax_vector(logits: torch.Tensor) -> torch.Tensor:\n    pass\n",
            reference_solution=(
                "import torch\n\n"
                "def softmax_vector(logits):\n"
                "    assert isinstance(logits, torch.Tensor)\n"
                "    return torch.softmax(logits, dim=0)\n"
            ),
            visible_tests=[{"name": "two logits", "args": [[1.0, 2.0]], "expected": [0.26894143, 0.7310586]}],
            hidden_tests=[{"name": "three logits", "args": [[0.0, 0.0, 0.0]], "expected": [0.33333334, 0.33333334, 0.33333334]}],
        ),
    }


def torch_scalar_output_case() -> dict[str, Any]:
    if not has_package("torch"):
        return {"name": "torch tensor input -> scalar tensor output", "skip": "torch is not installed"}
    return {
        "name": "torch tensor input -> scalar tensor output",
        "first_actual": 2.0,
        "problem": base_problem(
            problem_id="runtime_torch_mean",
            title="Runtime Torch Mean",
            function_name="tensor_mean",
            tags=["python", "torch", "statistics"],
            requirements=torch_requirement(),
            checker=allclose_checker(),
            arg_types=["torch.Tensor"],
            return_type="torch.Tensor",
            timeout_seconds=15,
            statement_io="- `x`: `torch.Tensor`, numeric tensor.\n- Return: `torch.Tensor`, a scalar mean tensor.",
            starter_code="import torch\n\ndef tensor_mean(x: torch.Tensor) -> torch.Tensor:\n    pass\n",
            reference_solution="import torch\n\ndef tensor_mean(x):\n    assert isinstance(x, torch.Tensor)\n    return x.float().mean()\n",
            visible_tests=[{"name": "basic", "args": [[1, 2, 3]], "expected": 2.0}],
            hidden_tests=[{"name": "negative", "args": [[-1, 1]], "expected": 0.0}],
        ),
    }


def pandas_series_output_case() -> dict[str, Any]:
    if not has_package("pandas"):
        return {"name": "pandas DataFrame input -> Series output", "skip": "pandas is not installed"}
    return {
        "name": "pandas DataFrame input -> Series output",
        "first_actual": [4, 6],
        "problem": base_problem(
            problem_id="runtime_pandas_row_sum",
            title="Runtime Pandas Row Sum",
            function_name="row_sum",
            tags=["python", "pandas", "dataframe"],
            requirements=pandas_requirement(),
            checker={"type": "exact"},
            arg_types=["pandas.DataFrame"],
            return_type="pandas.Series",
            statement_io="- `df`: `pandas.DataFrame`, columns `x` and `y`.\n- Return: `pandas.Series`, row-wise sums.",
            starter_code="import pandas as pd\n\ndef row_sum(df: pd.DataFrame) -> pd.Series:\n    pass\n",
            reference_solution="import pandas as pd\n\ndef row_sum(df):\n    assert hasattr(df, 'columns')\n    return df['x'] + df['y']\n",
            visible_tests=[{"name": "basic", "args": [[{"x": 1, "y": 3}, {"x": 2, "y": 4}]], "expected": [4, 6]}],
            hidden_tests=[{"name": "zero", "args": [[{"x": 0, "y": 5}]], "expected": [5]}],
        ),
    }


def pandas_dataframe_output_case() -> dict[str, Any]:
    if not has_package("pandas"):
        return {"name": "pandas DataFrame input -> DataFrame output", "skip": "pandas is not installed"}
    return {
        "name": "pandas DataFrame input -> DataFrame output",
        "first_actual": [{"group": "a", "total": 4}, {"group": "b", "total": 2}],
        "problem": base_problem(
            problem_id="runtime_pandas_group_totals",
            title="Runtime Pandas Group Totals",
            function_name="group_totals",
            tags=["python", "pandas", "aggregation"],
            requirements=pandas_requirement(),
            checker={"type": "exact"},
            arg_types=["pandas.DataFrame"],
            return_type="pandas.DataFrame",
            statement_io="- `df`: `pandas.DataFrame`, columns `group` and `value`.\n- Return: `pandas.DataFrame`, records with `group` and `total`.",
            starter_code="import pandas as pd\n\ndef group_totals(df: pd.DataFrame) -> pd.DataFrame:\n    pass\n",
            reference_solution=(
                "import pandas as pd\n\n"
                "def group_totals(df):\n"
                "    out = df.groupby('group', as_index=False)['value'].sum()\n"
                "    out = out.rename(columns={'value': 'total'}).sort_values('group').reset_index(drop=True)\n"
                "    return out\n"
            ),
            visible_tests=[
                {
                    "name": "basic",
                    "args": [[{"group": "a", "value": 1}, {"group": "b", "value": 2}, {"group": "a", "value": 3}]],
                    "expected": [{"group": "a", "total": 4}, {"group": "b", "total": 2}],
                }
            ],
            hidden_tests=[{"name": "single", "args": [[{"group": "z", "value": 5}]], "expected": [{"group": "z", "total": 5}]}],
        ),
    }


def pandas_series_input_case() -> dict[str, Any]:
    if not has_package("pandas"):
        return {"name": "pandas Series input -> float output", "skip": "pandas is not installed"}
    return {
        "name": "pandas Series input -> float output",
        "first_actual": 2.0,
        "problem": base_problem(
            problem_id="runtime_pandas_series_mean",
            title="Runtime Pandas Series Mean",
            function_name="series_mean",
            tags=["python", "pandas", "statistics"],
            requirements=pandas_requirement(),
            checker=allclose_checker(),
            arg_types=["pandas.Series"],
            return_type="float",
            statement_io="- `s`: `pandas.Series`, numeric values.\n- Return: `float`, the mean.",
            starter_code="import pandas as pd\n\ndef series_mean(s: pd.Series) -> float:\n    pass\n",
            reference_solution="import pandas as pd\n\ndef series_mean(s):\n    assert hasattr(s, 'mean')\n    return float(s.mean())\n",
            visible_tests=[{"name": "basic", "args": [[1, 2, 3]], "expected": 2.0}],
            hidden_tests=[{"name": "single", "args": [[7]], "expected": 7.0}],
        ),
    }


def tuple_interface_case() -> dict[str, Any]:
    return {
        "name": "tuple input -> tuple output",
        "first_actual": [2, 1],
        "problem": base_problem(
            problem_id="runtime_tuple_swap",
            title="Runtime Tuple Swap",
            function_name="swap_pair",
            tags=["python", "tuple"],
            requirements=[],
            checker={"type": "exact"},
            arg_types=["tuple[int,int]"],
            return_type="tuple[int,int]",
            statement_io="- `pair`: `tuple[int, int]`.\n- Return: `tuple[int, int]`, swapped.",
            starter_code="def swap_pair(pair: tuple[int, int]) -> tuple[int, int]:\n    pass\n",
            reference_solution="def swap_pair(pair):\n    assert isinstance(pair, tuple)\n    return (pair[1], pair[0])\n",
            visible_tests=[{"name": "basic", "args": [[1, 2]], "expected": [2, 1]}],
            hidden_tests=[{"name": "negative", "args": [[-1, 5]], "expected": [5, -1]}],
        ),
    }


def namespace_input_case() -> dict[str, Any]:
    return {
        "name": "object namespace input -> dict output",
        "first_actual": {"final_lr": 0.30000000000000004, "steps": 3},
        "problem": base_problem(
            problem_id="runtime_namespace_config",
            title="Runtime Namespace Config",
            function_name="summarize_config",
            tags=["python", "object", "config"],
            requirements=[],
            checker=allclose_checker(),
            arg_types=["object"],
            return_type="dict",
            statement_io="- `cfg`: object with public fields `lr` and `steps`.\n- Return: `dict`, a JSON-like summary.",
            starter_code="def summarize_config(cfg: object) -> dict[str, float | int]:\n    pass\n",
            reference_solution="def summarize_config(cfg):\n    return {'final_lr': cfg.lr * cfg.steps, 'steps': cfg.steps}\n",
            visible_tests=[{"name": "basic", "args": [{"lr": 0.1, "steps": 3}], "expected": {"final_lr": 0.3, "steps": 3}}],
            hidden_tests=[{"name": "zero", "args": [{"lr": 0.05, "steps": 0}], "expected": {"final_lr": 0.0, "steps": 0}}],
        ),
    }


def dataclass_output_case() -> dict[str, Any]:
    return {
        "name": "dataclass object output -> JSON object comparison",
        "first_actual": {"weights": [2.0, 4.0], "bias": 0.5},
        "problem": base_problem(
            problem_id="runtime_dataclass_output",
            title="Runtime Dataclass Output",
            function_name="make_summary",
            tags=["python", "object", "machine_learning"],
            requirements=[],
            checker=allclose_checker(),
            return_type="object",
            statement_io="- `scale`: `float`.\n- Return: object with public `weights` and `bias` fields.",
            starter_code="def make_summary(scale: float) -> object:\n    pass\n",
            reference_solution=(
                "from dataclasses import dataclass\n\n"
                "@dataclass\n"
                "class ModelSummary:\n"
                "    weights: list[float]\n"
                "    bias: float\n\n"
                "def make_summary(scale):\n"
                "    return ModelSummary(weights=[scale, scale * 2], bias=0.5)\n"
            ),
            visible_tests=[{"name": "basic", "args": [2.0], "expected": {"weights": [2.0, 4.0], "bias": 0.5}}],
            hidden_tests=[{"name": "small", "args": [0.5], "expected": {"weights": [0.5, 1.0], "bias": 0.5}}],
        ),
    }


def namedtuple_output_case() -> dict[str, Any]:
    return {
        "name": "namedtuple object output -> JSON object comparison",
        "first_actual": {"loss": 0.09999999999999998, "accuracy": 0.9},
        "problem": base_problem(
            problem_id="runtime_namedtuple_metrics",
            title="Runtime NamedTuple Metrics",
            function_name="metrics",
            tags=["python", "object", "metrics"],
            requirements=[],
            checker=allclose_checker(),
            return_type="object",
            statement_io="- `correct`: `int`.\n- `total`: `int`.\n- Return: namedtuple-like object with `loss` and `accuracy`.",
            starter_code="def metrics(correct: int, total: int) -> object:\n    pass\n",
            reference_solution=(
                "from collections import namedtuple\n\n"
                "Metrics = namedtuple('Metrics', ['loss', 'accuracy'])\n\n"
                "def metrics(correct, total):\n"
                "    acc = correct / total\n"
                "    return Metrics(loss=1 - acc, accuracy=acc)\n"
            ),
            visible_tests=[{"name": "basic", "args": [9, 10], "expected": {"loss": 0.1, "accuracy": 0.9}}],
            hidden_tests=[{"name": "quarter loss", "args": [3, 4], "expected": {"loss": 0.25, "accuracy": 0.75}}],
        ),
    }


def set_output_case() -> dict[str, Any]:
    return {
        "name": "set output -> sorted JSON list comparison",
        "first_actual": [1, 2, 3],
        "problem": base_problem(
            problem_id="runtime_set_output",
            title="Runtime Set Output",
            function_name="unique_labels",
            tags=["python", "set"],
            requirements=[],
            checker={"type": "exact"},
            return_type="set",
            statement_io="- `labels`: `list[int]`.\n- Return: `set`, unique labels.",
            starter_code="def unique_labels(labels: list[int]) -> set[int]:\n    pass\n",
            reference_solution="def unique_labels(labels):\n    return set(labels)\n",
            visible_tests=[{"name": "basic", "args": [[3, 1, 2, 3]], "expected": [1, 2, 3]}],
            hidden_tests=[{"name": "empty", "args": [[]], "expected": []}],
        ),
    }


if __name__ == "__main__":
    raise SystemExit(main())
