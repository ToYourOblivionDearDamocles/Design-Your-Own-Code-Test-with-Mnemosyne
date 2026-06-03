from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from mnemosyne.runtime.dependencies import check_problem_requirements, problem_requirements
from mnemosyne.verifier.contract import DEFAULT_FLOAT_ATOL, DEFAULT_FLOAT_RTOL


@dataclass
class JudgeResult:
    status: str
    passed: int
    total: int
    tests: list[dict[str, Any]]
    stdout: str = ""
    stderr: str = ""
    error: str | None = None
    metadata: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "total": self.total,
            "tests": self.tests,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error": self.error,
            "metadata": self.metadata or {},
        }


def judge_code(problem: dict[str, Any], user_code: str, mode: Literal["run", "submit"]) -> JudgeResult:
    visible = problem.get("visible_tests", [])
    hidden = problem.get("hidden_tests", [])
    # Mnemosyne no longer exposes a hidden-test workflow in the UI. Treat legacy
    # hidden_tests as additional explicit tests so Run and Verify cover them.
    tests = visible + hidden

    if not tests:
        return JudgeResult(
            status="Invalid Problem",
            passed=0,
            total=0,
            tests=[],
            error="No tests found.",
        )

    use_docker = os.getenv("JUDGE_USE_DOCKER", "0") == "1"
    dependency_status = check_problem_requirements(problem)
    if not use_docker and not dependency_status["ok"]:
        missing = ", ".join(req["package"] for req in dependency_status["missing"])
        install_command = dependency_status["install_command"]
        message = f"Missing required package(s): {missing}."
        if install_command:
            message += f" Install them with: {install_command}"
        return JudgeResult(
            status="Missing Dependencies",
            passed=0,
            total=len(tests),
            tests=[],
            error=message,
            metadata={"dependency_status": dependency_status},
        )

    with tempfile.TemporaryDirectory(prefix="mnemosyne_") as tmp:
        workdir = Path(tmp)
        (workdir / "user_solution.py").write_text(user_code, encoding="utf-8")
        (workdir / "tests.json").write_text(json.dumps(tests), encoding="utf-8")
        (workdir / "test_runner.py").write_text(_build_test_runner(problem), encoding="utf-8")

        if use_docker:
            completed = _run_in_docker(
                workdir,
                timeout_seconds=int(problem.get("timeout_seconds", 3)),
                image=str(problem.get("docker_image") or os.getenv("JUDGE_DOCKER_IMAGE", "python:3.11-slim")),
            )
        else:
            completed = _run_locally(workdir, timeout_seconds=int(problem.get("timeout_seconds", 3)))

    return _parse_completed_process(completed, total=len(tests))


def generate_expected_output(problem: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    if problem.get("entry_kind", "function") != "function":
        return {
            "ok": False,
            "error": "Expected output generation is only available for function problems.",
        }

    reference_solution = problem.get("reference_solution") or problem.get("solution")
    if not isinstance(reference_solution, str) or not reference_solution.strip():
        return {
            "ok": False,
            "error": "This problem has no reference_solution to generate expected output.",
        }

    trial_problem = copy.deepcopy(problem)
    trial_problem["visible_tests"] = [{"name": "generated_expected", "args": args, "expected": "__expected_generation_sentinel__"}]
    trial_problem["hidden_tests"] = []
    result = judge_code(trial_problem, reference_solution, "run").as_dict()

    if result["status"] == "Missing Dependencies":
        return {
            "ok": False,
            "error": result.get("error") or "Missing dependencies.",
            "result": result,
        }

    tests = result.get("tests") or []
    if not tests:
        return {
            "ok": False,
            "error": result.get("error") or "Reference solution did not return a test result.",
            "result": result,
        }

    test = tests[0]
    if test.get("error"):
        return {
            "ok": False,
            "error": test["error"],
            "result": result,
        }

    return {
        "ok": True,
        "expected": test.get("actual"),
        "result": result,
    }


def _run_locally(workdir: Path, timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            [sys.executable, "test_runner.py"],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as e:
        return subprocess.CompletedProcess(
            args=e.cmd or [],
            returncode=124,
            stdout=e.stdout or "",
            stderr=(e.stderr or "") + f"\nTimeout after {timeout_seconds}s",
        )


def _run_in_docker(workdir: Path, timeout_seconds: int, image: str) -> subprocess.CompletedProcess[str]:
    if shutil.which("docker") is None:
        return subprocess.CompletedProcess(
            args=[],
            returncode=127,
            stdout="",
            stderr="Docker is not installed or not on PATH.",
        )

    cmd = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--memory",
        "256m",
        "--cpus",
        "1",
        "-v",
        f"{workdir}:/workspace:ro",
        "-w",
        "/workspace",
        image,
        "python",
        "test_runner.py",
    ]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds + 5)
    except subprocess.TimeoutExpired as e:
        return subprocess.CompletedProcess(
            args=e.cmd or [],
            returncode=124,
            stdout=e.stdout or "",
            stderr=(e.stderr or "") + f"\nTimeout after {timeout_seconds}s",
        )


def _parse_completed_process(completed: subprocess.CompletedProcess[str], total: int) -> JudgeResult:
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""

    if completed.returncode == 124:
        return JudgeResult(
            status="Time Limit Exceeded",
            passed=0,
            total=total,
            tests=[],
            stdout=stdout,
            stderr=stderr,
            error="Submission timed out.",
        )

    marker = "__JUDGE_RESULT__="
    result_line = None
    for line in stdout.splitlines():
        if line.startswith(marker):
            result_line = line[len(marker):]

    if result_line is None:
        details = stderr.strip() or stdout.strip()
        message = "No structured result returned by test runner."
        if details:
            message += "\n\nRunner output:\n" + details[-4000:]
        return JudgeResult(
            status="Runtime Error",
            passed=0,
            total=total,
            tests=[],
            stdout=stdout,
            stderr=stderr,
            error=message,
        )

    try:
        data = json.loads(result_line)
    except json.JSONDecodeError as e:
        return JudgeResult(
            status="Runtime Error",
            passed=0,
            total=total,
            tests=[],
            stdout=stdout,
            stderr=stderr,
            error=f"Could not parse test runner result: {e}",
        )

    tests = data.get("tests", [])
    passed = sum(1 for t in tests if t.get("passed"))
    status = "Accepted" if passed == len(tests) and completed.returncode == 0 else "Wrong Answer"
    if data.get("runner_error"):
        status = "Runtime Error"
        if str(data["runner_error"]).startswith("Missing required package"):
            status = "Missing Dependencies"

    return JudgeResult(
        status=status,
        passed=passed,
        total=len(tests),
        tests=tests,
        stdout=stdout,
        stderr=stderr,
        error=data.get("runner_error"),
    )


def _build_test_runner(problem: dict[str, Any]) -> str:
    entry_kind = problem.get("entry_kind", "function")
    function_name = problem.get("function_name", "")
    checker_json = json.dumps(problem.get("checker", {"type": "exact"}))
    arg_types_json = json.dumps(problem.get("arg_types", []))
    return_type_json = json.dumps(problem.get("return_type", None))
    requirements_json = json.dumps(problem_requirements(problem))
    requirement_helpers = textwrap.indent(
        textwrap.dedent(
            f"""
            REQUIREMENTS = json.loads({requirements_json!r})

            def check_runtime_requirements():
                missing = []
                for req in REQUIREMENTS:
                    if req.get("optional"):
                        continue
                    import_name = req.get("import_name") or req.get("package")
                    if import_name and importlib.util.find_spec(import_name) is None:
                        missing.append(req)
                if not missing:
                    return None
                packages = ", ".join(req.get("package", req.get("pip", "")) for req in missing)
                install = " ".join(req.get("pip") or req.get("package", "") for req in missing).strip()
                message = f"Missing required package(s) in judge runtime: {{packages}}."
                if install:
                    message += f" Install them with: .venv/bin/pip install {{install}}"
                return message
            """
        ).strip(),
        " " * 12,
    )

    if entry_kind == "function":
        return textwrap.dedent(
            f"""
            import dataclasses
            import importlib
            import importlib.util
            import json
            import math
            import traceback
            import types

{requirement_helpers}

            CHECKER = json.loads({checker_json!r})
            ARG_TYPES = json.loads({arg_types_json!r})
            RETURN_TYPE = json.loads({return_type_json!r})

            def type_name(type_spec):
                if isinstance(type_spec, dict):
                    return str(type_spec.get("type") or "")
                return str(type_spec or "")

            def type_dtype(type_spec):
                if isinstance(type_spec, dict):
                    return type_spec.get("dtype")
                return None

            def type_key(type_spec):
                return type_name(type_spec).strip().replace(" ", "").lower()

            def convert_value(value, type_spec):
                key = type_key(type_spec)
                dtype = type_dtype(type_spec)
                if key in {{"", "json", "json_native", "int", "float", "str", "bool", "list", "dict"}}:
                    return value
                if key.startswith(("list[", "dict[")):
                    return value
                if key in {{"complex", "builtins.complex"}}:
                    if isinstance(value, dict):
                        return complex(value.get("real", 0), value.get("imag", 0))
                    if isinstance(value, (list, tuple)) and len(value) == 2:
                        return complex(value[0], value[1])
                    return complex(value)
                if key == "tuple":
                    return tuple(value)
                if key.startswith("tuple["):
                    return tuple(value)
                if key == "set" or key.startswith("set["):
                    return set(value)
                if key == "frozenset" or key.startswith("frozenset["):
                    return frozenset(value)
                if key in {{"object", "namespace", "types.simplenamespace", "simplenamespace"}}:
                    return types.SimpleNamespace(**value) if isinstance(value, dict) else value
                if key in {{"numpy.ndarray", "np.ndarray", "numpy.array", "np.array", "ndarray"}}:
                    import numpy as np
                    return np.asarray(value, dtype=dtype) if dtype else np.asarray(value)
                if key in {{"torch.tensor", "tensor"}}:
                    import torch
                    torch_dtype = getattr(torch, str(dtype).removeprefix("torch."), None) if dtype else None
                    return torch.tensor(value, dtype=torch_dtype) if torch_dtype is not None else torch.tensor(value)
                if key in {{"pandas.dataframe", "pd.dataframe", "dataframe"}}:
                    import pandas as pd
                    return pd.DataFrame(value, dtype=dtype) if dtype else pd.DataFrame(value)
                if key in {{"pandas.series", "pd.series", "series"}}:
                    import pandas as pd
                    return pd.Series(value, dtype=dtype) if dtype else pd.Series(value)
                if key in {{"scipy.sparse.csr_matrix", "sparse.csr_matrix", "sp.csr_matrix", "csr_matrix"}}:
                    from scipy import sparse
                    return sparse.csr_matrix(value, dtype=dtype) if dtype else sparse.csr_matrix(value)
                if key in {{"scipy.sparse.csc_matrix", "sparse.csc_matrix", "sp.csc_matrix", "csc_matrix"}}:
                    from scipy import sparse
                    return sparse.csc_matrix(value, dtype=dtype) if dtype else sparse.csc_matrix(value)
                if key in {{"scipy.sparse.coo_matrix", "sparse.coo_matrix", "sp.coo_matrix", "coo_matrix"}}:
                    from scipy import sparse
                    return sparse.coo_matrix(value, dtype=dtype) if dtype else sparse.coo_matrix(value)
                return value

            def convert_args(args):
                if not ARG_TYPES:
                    return args
                converted = []
                for idx, value in enumerate(args):
                    type_spec = ARG_TYPES[idx] if idx < len(ARG_TYPES) else None
                    converted.append(convert_value(value, type_spec))
                return converted

            def normalize(x):
                if hasattr(x, "detach") and callable(x.detach):
                    x = x.detach()
                if hasattr(x, "cpu") and callable(x.cpu):
                    x = x.cpu()
                module_name = getattr(type(x), "__module__", "")
                class_name = getattr(type(x), "__name__", "")
                if isinstance(x, complex):
                    return {{"real": normalize(x.real), "imag": normalize(x.imag)}}
                if module_name.startswith("scipy.sparse") and hasattr(x, "toarray") and callable(x.toarray):
                    return normalize(x.toarray())
                if module_name.startswith("pandas.") and class_name == "DataFrame":
                    return normalize(x.to_dict(orient="records"))
                if module_name.startswith("pandas.") and class_name == "Series":
                    return normalize(x.tolist())
                if dataclasses.is_dataclass(x) and not isinstance(x, type):
                    return normalize(dataclasses.asdict(x))
                if hasattr(x, "model_dump") and callable(x.model_dump):
                    return normalize(x.model_dump())
                if hasattr(x, "tolist") and callable(x.tolist):
                    return normalize(x.tolist())
                if hasattr(x, "item") and callable(x.item):
                    try:
                        return normalize(x.item())
                    except Exception:
                        pass
                if isinstance(x, tuple) and hasattr(x, "_fields"):
                    return {{field: normalize(getattr(x, field)) for field in x._fields}}
                if isinstance(x, tuple):
                    return [normalize(item) for item in x]
                if isinstance(x, (set, frozenset)):
                    normalized_items = [normalize(item) for item in x]
                    return sorted(normalized_items, key=lambda item: json.dumps(item, sort_keys=True, default=str))
                if isinstance(x, list):
                    return [normalize(item) for item in x]
                if isinstance(x, dict):
                    return {{str(k): normalize(v) for k, v in x.items()}}
                if hasattr(x, "__dict__") and not isinstance(x, type):
                    public_attrs = {{
                        str(k): v
                        for k, v in vars(x).items()
                        if not str(k).startswith("_") and not callable(v)
                    }}
                    if public_attrs:
                        return {{k: normalize(v) for k, v in public_attrs.items()}}
                return x

            def values_equal(actual, expected):
                actual = normalize(actual)
                expected = normalize(expected)
                checker_type = CHECKER.get("type", "exact")
                if checker_type == "allclose":
                    return allclose(actual, expected, CHECKER.get("atol", {DEFAULT_FLOAT_ATOL!r}), CHECKER.get("rtol", {DEFAULT_FLOAT_RTOL!r}))
                if checker_type == "unordered_nested":
                    return unordered_nested(actual) == unordered_nested(expected)
                return actual == expected

            def unordered_nested(value):
                value = normalize(value)
                if isinstance(value, list):
                    normalized_items = [unordered_nested(item) for item in value]
                    return sorted(normalized_items, key=lambda item: json.dumps(item, sort_keys=True, default=str))
                if isinstance(value, dict):
                    return {{str(k): unordered_nested(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}}
                return value

            def allclose(actual, expected, atol, rtol):
                if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
                    return math.isclose(float(actual), float(expected), abs_tol=float(atol), rel_tol=float(rtol))
                if isinstance(actual, list) and isinstance(expected, list):
                    if len(actual) != len(expected):
                        return False
                    return all(allclose(a, e, atol, rtol) for a, e in zip(actual, expected))
                if isinstance(actual, dict) and isinstance(expected, dict):
                    if set(actual.keys()) != set(expected.keys()):
                        return False
                    return all(allclose(actual[k], expected[k], atol, rtol) for k in actual)
                return actual == expected

            def main():
                tests = json.load(open("tests.json", "r", encoding="utf-8"))
                results = []
                runner_error = None
                requirement_error = check_runtime_requirements()
                if requirement_error:
                    print("__JUDGE_RESULT__=" + json.dumps({{"tests": results, "runner_error": requirement_error}}))
                    raise SystemExit(1)
                try:
                    mod = importlib.import_module("user_solution")
                    fn = getattr(mod, {function_name!r})
                except Exception:
                    runner_error = traceback.format_exc()
                    print("__JUDGE_RESULT__=" + json.dumps({{"tests": results, "runner_error": runner_error}}))
                    raise SystemExit(1)

                for idx, t in enumerate(tests):
                    name = t.get("name", f"test_{{idx}}")
                    args = t.get("args", [])
                    expected = t.get("expected")
                    try:
                        call_args = convert_args(args)
                        actual = fn(*call_args)
                        normalized_actual = normalize(actual)
                        normalized_expected = normalize(expected)
                        passed = values_equal(actual, expected)
                        results.append({{
                            "name": name,
                            "passed": passed,
                            "expected": normalized_expected,
                            "actual": normalized_actual,
                        }})
                    except Exception:
                        results.append({{
                            "name": name,
                            "passed": False,
                            "expected": expected,
                            "actual": None,
                            "error": traceback.format_exc(),
                        }})

                print("__JUDGE_RESULT__=" + json.dumps({{"tests": results, "runner_error": runner_error}}, default=str))
                raise SystemExit(0 if all(r["passed"] for r in results) else 1)

            if __name__ == "__main__":
                main()
            """
        )

    if entry_kind == "unit_tests":
        return textwrap.dedent(
            f"""
            import importlib
            import importlib.util
            import json
            import traceback

{requirement_helpers}

            def main():
                tests = json.load(open("tests.json", "r", encoding="utf-8"))
                results = []
                runner_error = None
                requirement_error = check_runtime_requirements()
                if requirement_error:
                    print("__JUDGE_RESULT__=" + json.dumps({{"tests": results, "runner_error": requirement_error}}))
                    raise SystemExit(1)

                for idx, t in enumerate(tests):
                    name = t.get("name", f"test_{{idx}}")
                    code = t.get("code", "")
                    try:
                        namespace = {{}}
                        exec(code, namespace, namespace)
                        results.append({{"name": name, "passed": True}})
                    except Exception:
                        results.append({{
                            "name": name,
                            "passed": False,
                            "error": traceback.format_exc(),
                        }})

                print("__JUDGE_RESULT__=" + json.dumps({{"tests": results, "runner_error": runner_error}}, default=str))
                raise SystemExit(0 if all(r["passed"] for r in results) else 1)

            if __name__ == "__main__":
                main()
            """
        )

    return textwrap.dedent(
        f"""
        import json
        print("__JUDGE_RESULT__=" + json.dumps({{
            "tests": [],
            "runner_error": "Unsupported entry_kind: {entry_kind}"
        }}))
        raise SystemExit(1)
        """
    )
