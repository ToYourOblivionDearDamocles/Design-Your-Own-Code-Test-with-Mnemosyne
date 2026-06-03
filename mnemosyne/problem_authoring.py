from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from mnemosyne.authoring.io import _warn, format_problem_json, parse_problem_collection, parse_problem_content, prepare_problem_content
from mnemosyne.prompts import render_prompt
from mnemosyne.storage.problems import PROBLEMS_DIR
from mnemosyne.verifier.layers import (
    _add_layer_issue,
    _empty_verifier_layers,
    _finalize_verifier_layers,
    _merge_verifier_layers,
    build_verifier_layers,
)
from mnemosyne.verifier.contract import (
    AUTHORING_API_SCHEMA,
    DEFAULT_FLOAT_ATOL,
    DEFAULT_FLOAT_RTOL,
    DISPLAY_MATH_COMMAND_RE,
    FUNCTION_RE,
    FUNCTION_TEST_SCHEMA,
    ID_RE,
    IMPORT_NAME_RE,
    INLINE_MATH_RE,
    JSON_VALUE_SCHEMA,
    KNOWN_IMPORT_SNIPPETS,
    KNOWN_PACKAGE_REQUIREMENTS,
    PACKAGE_SPEC_RE,
    PROBLEM_TEMPLATE,
    SUPPORTED_RUNTIME_TYPES,
    TEXT_DEPENDENCY_KEYWORDS,
    TYPE_SPEC_SCHEMA,
    UNIT_TEST_SCHEMA,
    json_value_schema,
)

AUTHORING_PROMPT = render_prompt("direct_json_authoring_prompt")

def validate_problem_spec(problem: dict[str, Any], verify_reference: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    normalized = dict(problem)
    checker_was_missing = "checker" not in problem
    _normalize_scalar_fields(normalized, warnings)
    _normalize_section_aliases(normalized, warnings)

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
    _validate_learning_content(normalized, errors)
    _validate_statement_math(normalized.get("statement"), warnings)

    timeout = normalized.get("timeout_seconds")
    if not isinstance(timeout, int) or timeout < 1 or timeout > 60:
        errors.append("timeout_seconds must be an integer between 1 and 60.")

    for key in ("visible_tests", "hidden_tests"):
        if not isinstance(normalized.get(key), list):
            errors.append(f"{key} must be a list.")

    visible_tests = normalized.get("visible_tests", [])
    if isinstance(visible_tests, list) and not visible_tests:
        errors.append("visible_tests must contain at least one explicit test.")

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
        "layers": build_verifier_layers(errors, warnings),
        "problem": normalized,
    }


def validate_problem_collection(problems: list[dict[str, Any]], verify_reference: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    layers = _empty_verifier_layers()

    for idx, problem in enumerate(problems):
        validation = validate_problem_spec(problem, verify_reference=verify_reference)
        problem_id = str(validation.get("problem", {}).get("id") or problem.get("id") or f"item_{idx}")
        prefix = f"problems[{idx}] ({problem_id})"
        prefixed_errors = [f"{prefix}: {error}" for error in validation["errors"]]
        prefixed_warnings = [f"{prefix}: {warning}" for warning in validation["warnings"]]
        errors.extend(prefixed_errors)
        warnings.extend(prefixed_warnings)
        _merge_verifier_layers(layers, validation.get("layers", []), prefix=prefix)
        if validation.get("problem"):
            normalized.append(validation["problem"])
        if problem_id in seen_ids:
            duplicate = f"{prefix}: duplicate problem id in this batch."
            errors.append(duplicate)
            _add_layer_issue(layers, "schema", "errors", duplicate)
        seen_ids.add(problem_id)

    _finalize_verifier_layers(layers)
    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "layers": layers,
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



def _validate_learning_content(problem: dict[str, Any], errors: list[str]) -> None:
    tags = problem.get("tags")
    if not isinstance(tags, list) or not any(isinstance(tag, str) and tag.strip() for tag in tags):
        errors.append("tags must contain at least one topic tag.")

    statement = problem.get("statement")
    if isinstance(statement, str):
        normalized_statement = " ".join(statement.lower().split())
        if problem.get("entry_kind") == "function":
            if "input / output" not in normalized_statement and "input/output" not in normalized_statement:
                errors.append('statement must include an "Input / Output" section.')
            if "return" not in normalized_statement:
                errors.append("statement must describe the return value.")
            if isinstance(problem.get("function_name"), str):
                for arg_name in _function_arg_names(problem, str(problem["function_name"])):
                    if not re.search(rf"`?{re.escape(arg_name)}`?", statement):
                        errors.append(f"statement Input / Output section must mention parameter `{arg_name}`.")
    elif statement is not None:
        errors.append("statement must be a Markdown string.")

    theory = problem.get("theory") or problem.get("theory_markdown") or problem.get("algorithm_theory")
    if not isinstance(theory, str) or not theory.strip():
        errors.append("theory is required and must be a non-empty Markdown string.")

    examples = problem.get("examples") if "examples" in problem else problem.get("worked_examples")
    if not _examples_have_content(examples):
        errors.append("examples must contain at least one worked example with a name/title and body/walkthrough/explanation.")



def _examples_have_content(examples: Any) -> bool:
    if isinstance(examples, str):
        return bool(examples.strip())
    if not isinstance(examples, list) or not examples:
        return False
    for example in examples:
        if isinstance(example, str) and example.strip():
            return True
        if not isinstance(example, dict):
            continue
        name = example.get("name") or example.get("title")
        body = example.get("body") or example.get("walkthrough") or example.get("explanation")
        if isinstance(name, str) and name.strip() and isinstance(body, str) and body.strip():
            return True
    return False

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
    valid_arg_types = isinstance(arg_types, list)
    if arg_types is not None:
        if not valid_arg_types:
            errors.append("arg_types must be a list when provided.")
        else:
            if arg_names and len(arg_types) != len(arg_names):
                errors.append(f"arg_types has {len(arg_types)} item(s), but function_name expects {len(arg_names)} argument(s).")
            for idx, type_spec in enumerate(arg_types):
                if not _valid_runtime_type_spec(type_spec):
                    errors.append(f"arg_types[{idx}] must be a supported type string or {{\"type\":\"...\",\"dtype\":\"...\"}} object.")

    if "return_type" in problem and not _valid_runtime_type_spec(problem.get("return_type")):
        errors.append("return_type must be a supported type string or {\"type\":\"...\",\"dtype\":\"...\"} object.")

    function_name = problem.get("function_name")
    if not isinstance(function_name, str):
        return
    signature = _starter_signature_annotations(problem.get("starter_code"), function_name)
    if not signature:
        return

    declared_arg_types = arg_types if valid_arg_types else []
    annotations = signature.get("args", {})
    for idx, arg_name in enumerate(arg_names):
        annotation = annotations.get(arg_name)
        declared = declared_arg_types[idx] if idx < len(declared_arg_types) else None
        _validate_runtime_declaration_pair(
            annotation=annotation,
            declared=declared,
            location=f"parameter `{arg_name}`",
            declaration_name=f"arg_types[{idx}]",
            errors=errors,
        )

    _validate_runtime_declaration_pair(
        annotation=signature.get("return"),
        declared=problem.get("return_type") if "return_type" in problem else None,
        location="return annotation",
        declaration_name="return_type",
        errors=errors,
    )


def _starter_signature_annotations(code: Any, function_name: str) -> dict[str, Any] | None:
    if not isinstance(code, str):
        return None
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            args = list(node.args.posonlyargs) + list(node.args.args)
            if args and args[0].arg == "self":
                args = args[1:]
            return {
                "args": {arg.arg: _annotation_text(arg.annotation) for arg in args if arg.annotation is not None},
                "return": _annotation_text(node.returns) if node.returns is not None else None,
            }
    return None


def _annotation_text(annotation: ast.AST | None) -> str | None:
    if annotation is None:
        return None
    try:
        return ast.unparse(annotation).strip().strip('"\'')
    except Exception:  # pragma: no cover - ast.unparse should be available on supported Python.
        return None


def _validate_runtime_declaration_pair(
    *,
    annotation: Any,
    declared: Any,
    location: str,
    declaration_name: str,
    errors: list[str],
) -> None:
    annotation_family = _runtime_type_family(annotation)
    declared_family = _runtime_type_family(declared)
    annotation_requires = _runtime_family_requires_declaration(annotation_family)
    declared_requires = _runtime_family_requires_declaration(declared_family)

    if annotation_requires and declared is None:
        suggestion = _suggest_runtime_type(annotation)
        errors.append(
            f"starter_code {location} is annotated as `{annotation}`, so {declaration_name} must declare "
            f"the runtime conversion{f' (for example {suggestion})' if suggestion else ''}. "
            "Without this, JSON tests are passed as plain lists/dicts instead of the user-facing Python structure."
        )
        return

    if annotation_requires and declared is not None and not _runtime_families_compatible(annotation_family, declared_family):
        errors.append(
            f"starter_code {location} is annotated as `{annotation}`, but {declaration_name} declares "
            f"`{_runtime_type_name(declared)}`. These runtime types do not match."
        )
        return

    if declared_requires and annotation is not None and not _runtime_families_compatible(annotation_family, declared_family):
        errors.append(
            f"{declaration_name} declares `{_runtime_type_name(declared)}`, but starter_code {location} is annotated as "
            f"`{annotation}`. Make the visible function signature match the runtime conversion."
        )


def _runtime_type_family(type_spec: Any) -> str:
    key = _runtime_type_key(_runtime_type_name(type_spec))
    key = key.removeprefix("typing.").removeprefix("builtins.")
    if not key or key in {"any", "json", "json_native", "none"}:
        return "json"
    if key in {"int", "float", "str", "bool"}:
        return "json_scalar"
    if key == "complex":
        return "complex"
    if key == "list" or key.startswith("list[") or key.startswith("typing.list["):
        return "json_list"
    if key == "dict" or key.startswith("dict[") or key.startswith("typing.dict["):
        return "json_dict"
    if key == "tuple" or key.startswith("tuple["):
        return "tuple"
    if key == "set" or key.startswith("set["):
        return "set"
    if key == "frozenset" or key.startswith("frozenset["):
        return "frozenset"
    if key in {"object", "namespace", "types.simplenamespace", "simplenamespace"}:
        return "object"
    if (
        key in {"numpy.ndarray", "np.ndarray", "numpy.array", "np.array", "ndarray"}
        or key.startswith("numpy.typing.ndarray")
        or key.startswith("npt.ndarray")
        or key.startswith("ndarray[")
    ):
        return "numpy.ndarray"
    if key in {"torch.tensor", "tensor"}:
        return "torch.Tensor"
    if key in {"pandas.dataframe", "pd.dataframe", "dataframe"}:
        return "pandas.DataFrame"
    if key in {"pandas.series", "pd.series", "series"}:
        return "pandas.Series"
    if key in {"scipy.sparse.csr_matrix", "sparse.csr_matrix", "sp.csr_matrix", "csr_matrix"}:
        return "scipy.sparse.csr_matrix"
    if key in {"scipy.sparse.csc_matrix", "sparse.csc_matrix", "sp.csc_matrix", "csc_matrix"}:
        return "scipy.sparse.csc_matrix"
    if key in {"scipy.sparse.coo_matrix", "sparse.coo_matrix", "sp.coo_matrix", "coo_matrix"}:
        return "scipy.sparse.coo_matrix"
    return "unknown"


def _runtime_family_requires_declaration(family: str) -> bool:
    return family in {
        "complex",
        "tuple",
        "set",
        "frozenset",
        "object",
        "numpy.ndarray",
        "torch.Tensor",
        "pandas.DataFrame",
        "pandas.Series",
        "scipy.sparse.csr_matrix",
        "scipy.sparse.csc_matrix",
        "scipy.sparse.coo_matrix",
    }


def _runtime_families_compatible(annotation_family: str, declared_family: str) -> bool:
    if annotation_family == declared_family:
        return True
    if annotation_family.startswith("json") and declared_family.startswith("json"):
        return True
    return False


def _suggest_runtime_type(annotation: Any) -> str:
    family = _runtime_type_family(annotation)
    if family in {"unknown", "json", "json_scalar", "json_list", "json_dict"}:
        return ""
    return json.dumps(family)


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
        from mnemosyne.runtime.judge import judge_code
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


def _normalize_section_aliases(problem: dict[str, Any], warnings: list[str]) -> None:
    _rename_first_available(problem, ("problem", "problem_markdown", "problem_statement", "prompt"), "statement", warnings)
    _rename_first_available(problem, ("theory_markdown", "algorithm_theory"), "theory", warnings)
    _rename_first_available(problem, ("example", "worked_examples", "worked_example"), "examples", warnings)
    _rename_first_available(problem, ("test_cases", "tests", "explicit_tests"), "visible_tests", warnings)
    _rename_first_available(problem, ("complexities", "time_space_complexity"), "complexity", warnings)

    if "solution" in problem:
        solution = problem.get("solution")
        if isinstance(solution, dict):
            if "reference_solution" not in problem and isinstance(solution.get("code"), str):
                problem["reference_solution"] = solution["code"]
                _warn(warnings, "Converted solution.code to reference_solution.")
            explanation = solution.get("explanation") or solution.get("body") or solution.get("text")
            if "solution_explanation" not in problem and isinstance(explanation, str):
                problem["solution_explanation"] = explanation
                _warn(warnings, "Converted solution explanation to solution_explanation.")
        elif isinstance(solution, str):
            if "reference_solution" not in problem and _looks_like_python_solution(solution):
                problem["reference_solution"] = solution
                _warn(warnings, "Converted solution to reference_solution.")
            elif "solution_explanation" not in problem:
                problem["solution_explanation"] = solution
                _warn(warnings, "Converted solution to solution_explanation.")

    if "answer" in problem and "reference_solution" not in problem and isinstance(problem.get("answer"), str):
        problem["reference_solution"] = problem.pop("answer")
        _warn(warnings, "Converted answer to reference_solution.")


def _rename_first_available(problem: dict[str, Any], aliases: tuple[str, ...], target: str, warnings: list[str]) -> None:
    if target in problem:
        return
    for alias in aliases:
        if alias in problem:
            problem[target] = problem.pop(alias)
            _warn(warnings, f"Renamed {alias} to {target}.")
            return


def _looks_like_python_solution(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False
    if re.search(r"(^|\n)\s*(def|class)\s+", stripped):
        return True
    try:
        ast.parse(stripped)
    except SyntaxError:
        return False
    return "\n" in stripped and any(token in stripped for token in ("return ", "import ", "assert "))


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
        from mnemosyne.runtime.judge import generate_expected_output
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
        elif key.startswith("scipy.") or key.startswith("sparse.") or key.startswith("sp.") or key in {"csr_matrix", "csc_matrix", "coo_matrix"}:
            candidates.add("scipy")

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
