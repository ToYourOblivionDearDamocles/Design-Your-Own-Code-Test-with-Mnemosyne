from __future__ import annotations

import subprocess

from fastapi import APIRouter, HTTPException, Query

from mnemosyne.api.helpers import _error_result, _parse_error_result, _with_repair_hints, collect_problem_requirements
from mnemosyne.api.schemas import (
    AddGeneratedTestCaseRequest,
    AddTestCaseRequest,
    AuthorExpectedRequest,
    AuthorProblemRequest,
    ChatGenerateJsonRequest,
    CheckCodeRequest,
    GenerateExpectedRequest,
    InstallRequirementsRequest,
    LlmProblemDraftRequest,
    LlmProblemEditRequest,
    LlmRepairDraftRequest,
    LlmTestDraftRequest,
    SaveProblemRequest,
    SubmitRequest,
    VerifierRepairHintsRequest,
    VerifierValidateRequest,
)
from mnemosyne.chat_models import service as chat_model_service
from mnemosyne.storage.submissions import get_submission, list_submissions, list_wrong_problems, save_submission
from mnemosyne.runtime.dependencies import check_problem_requirements
from mnemosyne.runtime.judge import generate_expected_output, judge_code
from mnemosyne.llm_authoring import edit_problem_draft, generate_problem_draft, generate_test_drafts, repair_problem_draft
from mnemosyne.runtime.package_manager import install_dependency_requirements, install_requirements, runtime_status
from mnemosyne.problem_authoring import (
    AUTHORING_PROMPT,
    PROBLEM_TEMPLATE,
    create_problem_collection_from_content,
    parse_problem_content,
    validate_problem_spec,
)
from mnemosyne.storage.problems import (
    append_test_case,
    delete_problem,
    get_problem,
    list_problems,
    list_tags,
    problem_solution,
    public_problem,
    save_problem,
)
from mnemosyne.verifier import service as verifier_service


router = APIRouter()


@router.get("/api/problems")
def api_list_problems(tag: str | None = None):
    problems = list_problems()
    if tag:
        problems = [p for p in problems if tag in p.get("tags", [])]
    return {"problems": problems, "tag": tag}


@router.get("/api/tags")
def api_list_tags():
    return {"tags": list_tags()}


@router.get("/api/authoring/template")
def api_authoring_template():
    return {"template": PROBLEM_TEMPLATE}


@router.get("/api/authoring/prompt")
def api_authoring_prompt():
    return {"prompt": AUTHORING_PROMPT}


@router.get("/api/authoring/schema")
def api_authoring_schema():
    return {"schema": verifier_service.authoring_schema()}


@router.get("/api/verifier/schema")
def api_verifier_schema():
    return {"schema": verifier_service.authoring_schema()}


@router.post("/api/verifier/validate")
def api_verifier_validate(req: VerifierValidateRequest):
    return verifier_service.validate_content(req.content, verify_reference=req.verify_reference)


@router.post("/api/verifier/repair-hints")
def api_verifier_repair_hints(req: VerifierRepairHintsRequest):
    return verifier_service.repair_hints(req.errors, req.warnings)


@router.post("/api/authoring/validate")
def api_authoring_validate(req: AuthorProblemRequest):
    return verifier_service.validate_content(req.content)


@router.post("/api/authoring/run-reference")
def api_authoring_run_reference(req: AuthorProblemRequest):
    return verifier_service.run_reference_content(req.content)


@router.post("/api/authoring/problems")
def api_authoring_create_problem(req: AuthorProblemRequest):
    try:
        return _with_repair_hints(create_problem_collection_from_content(req.content, overwrite=req.overwrite))
    except ValueError as e:
        return _parse_error_result(e, [], created=False, created_count=0)


@router.post("/api/authoring/install-dependencies")
def api_authoring_install_dependencies(req: AuthorProblemRequest):
    validation = verifier_service.validate_content(req.content, verify_reference=False)
    requirements = collect_problem_requirements(validation.get("problems", []))
    if validation.get("errors") and not requirements:
        return _with_repair_hints(
            {
                "ok": False,
                "installed": [],
                "errors": validation.get("errors", []),
                "warnings": validation.get("warnings", []),
                "problem": validation.get("problem"),
                "problems": validation.get("problems", []),
            }
        )

    install_result = install_dependency_requirements(requirements)
    return {
        **install_result,
        "validation_ok": validation.get("ok", False),
        "validation_errors": validation.get("errors", []),
        "warnings": validation.get("warnings", []),
        "problem": validation.get("problem"),
        "problems": validation.get("problems", []),
    }


@router.post("/api/authoring/expected")
def api_authoring_generate_expected(req: AuthorExpectedRequest):
    parse_warnings: list[str] = []
    try:
        problem = parse_problem_content(req.content, warnings=parse_warnings)
    except ValueError as e:
        return {**_parse_error_result(e, parse_warnings), "expected": None}

    validation = validate_problem_spec(problem)
    warnings = parse_warnings + validation["warnings"]
    if not validation["ok"]:
        return {"ok": False, "errors": validation["errors"], "warnings": warnings, "expected": None}

    result = generate_expected_output(validation["problem"], req.args)
    return {**result, "warnings": warnings}


@router.get("/api/llm/status")
def api_llm_status():
    return chat_model_service.status()


@router.get("/api/chat-models/status")
def api_chat_models_status():
    return chat_model_service.status()


@router.post("/api/chat-models/generate-json")
def api_chat_models_generate_json(req: ChatGenerateJsonRequest):
    return chat_model_service.generate_json(
        messages=req.messages,
        response_schema=req.response_schema,
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        attachments=req.attachments,
        timeout_seconds=req.timeout_seconds,
    )


@router.post("/api/llm/author/problems")
def api_llm_author_problems(req: LlmProblemDraftRequest):
    return generate_problem_draft(
        req.request,
        provider=req.provider,
        api_key=req.api_key,
        count=req.count,
        model=req.model,
        max_attempts=req.max_attempts,
        attachments=req.attachments,
        timeout_seconds=req.timeout_seconds,
    )


@router.post("/api/llm/author/repair")
def api_llm_repair_problem(req: LlmRepairDraftRequest):
    return repair_problem_draft(
        req.content,
        user_request=req.request,
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        max_attempts=req.max_attempts,
    )


@router.post("/api/llm/problems/{problem_id}/edit")
def api_llm_edit_problem(problem_id: str, req: LlmProblemEditRequest):
    try:
        problem = get_problem(problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    return edit_problem_draft(
        problem,
        req.request,
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        max_attempts=req.max_attempts,
    )


@router.post("/api/llm/problems/{problem_id}/tests")
def api_llm_generate_tests(problem_id: str, req: LlmTestDraftRequest):
    try:
        problem = get_problem(problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    return generate_test_drafts(
        problem,
        req.request,
        group=req.group,
        count=req.count,
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
    )


@router.get("/api/problems/{problem_id}")
def api_get_problem(problem_id: str):
    try:
        problem = get_problem(problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    data = public_problem(problem)
    data["dependency_status"] = check_problem_requirements(problem)
    return data


@router.get("/api/problems/{problem_id}/raw")
def api_get_problem_raw(problem_id: str):
    try:
        problem = get_problem(problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    return {"problem": problem}


@router.put("/api/problems/{problem_id}")
def api_update_problem(problem_id: str, req: SaveProblemRequest):
    try:
        existing = get_problem(problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    parse_warnings: list[str] = []
    try:
        problem = parse_problem_content(req.content, warnings=parse_warnings)
    except ValueError as e:
        return {**_parse_error_result(e, parse_warnings), "saved": False}

    if problem.get("id") != existing.get("id"):
        return {
            "ok": False,
            "saved": False,
            "errors": ["Editing cannot change the problem id. Create a new problem instead."],
            "warnings": parse_warnings,
            "problem": problem,
        }

    validation = validate_problem_spec(problem)
    validation["warnings"] = parse_warnings + validation["warnings"]
    if not validation["ok"]:
        return {"saved": False, **validation}

    path = save_problem(validation["problem"])
    return {"ok": True, "saved": True, "path": str(path), **validation}


@router.delete("/api/problems/{problem_id}")
def api_delete_problem(problem_id: str):
    try:
        deleted_path = delete_problem(problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    return {"ok": True, "deleted": True, "problem_id": problem_id, "path": str(deleted_path)}


@router.post("/api/problems/{problem_id}/tests")
def api_add_problem_test(problem_id: str, req: AddTestCaseRequest):
    try:
        updated = append_test_case(problem_id, req.group, req.test_case)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    except ValueError as e:
        return {**_error_result(e, [], failed_layer="schema"), "saved": False}

    validation = validate_problem_spec(updated)
    if not validation["ok"]:
        return {"saved": False, **validation}

    save_problem(validation["problem"])
    return {"ok": True, "saved": True, "problem": updated, "warnings": validation["warnings"], "errors": []}


@router.post("/api/problems/{problem_id}/tests/generated")
def api_add_generated_problem_test(problem_id: str, req: AddGeneratedTestCaseRequest):
    if req.group not in {"visible_tests", "hidden_tests"}:
        return {"ok": False, "saved": False, "errors": ["group must be visible_tests or legacy hidden_tests"], "warnings": [], "problem": None}
    try:
        problem = get_problem(problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")

    name = req.name.strip() or "new test"
    candidate = dict(problem)
    candidate_tests = list(candidate.get(req.group, []))
    candidate_tests.append({"name": name, "args": req.args, "expected": None})
    candidate[req.group] = candidate_tests
    candidate_validation = validate_problem_spec(candidate, verify_reference=False)
    if not candidate_validation["ok"]:
        return {"ok": False, "saved": False, **candidate_validation}

    expected = generate_expected_output(problem, req.args)
    if not expected.get("ok"):
        return {
            "ok": False,
            "saved": False,
            "errors": [str(expected.get("error") or "Could not generate expected output.")],
            "warnings": expected.get("warnings", []),
            "problem": problem,
        }

    test_case = {
        "name": name,
        "args": req.args,
        "expected": expected.get("expected"),
    }
    try:
        updated = append_test_case(problem_id, req.group, test_case)
    except ValueError as e:
        return {**_error_result(e, [], failed_layer="schema"), "saved": False}

    validation = validate_problem_spec(updated)
    if not validation["ok"]:
        return {"saved": False, **validation}

    save_problem(validation["problem"])
    return {
        "ok": True,
        "saved": True,
        "test_case": test_case,
        "problem": validation["problem"],
        "warnings": validation["warnings"],
        "errors": [],
    }


@router.post("/api/problems/{problem_id}/expected")
def api_generate_problem_expected(problem_id: str, req: GenerateExpectedRequest):
    try:
        problem = get_problem(problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    return generate_expected_output(problem, req.args)


@router.get("/api/problems/{problem_id}/solution")
def api_get_problem_solution(problem_id: str):
    try:
        problem = get_problem(problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem_solution(problem)


@router.get("/api/runtime")
def api_runtime(problem_id: str | None = None):
    if problem_id:
        try:
            return runtime_status(problem_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Problem not found")
    return runtime_status(None)


@router.post("/api/runtime/install")
def api_runtime_install(req: InstallRequirementsRequest):
    if req.scope not in {"current_problem", "optional_ml"}:
        raise HTTPException(status_code=400, detail="Unsupported install scope")
    if req.scope == "current_problem" and not req.problem_id:
        raise HTTPException(status_code=400, detail="problem_id is required for current_problem")

    try:
        return install_requirements(req.scope, req.problem_id)  # type: ignore[arg-type]
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Package install timed out")


@router.post("/api/submit")
def api_submit(req: SubmitRequest):
    if req.mode not in {"run", "submit"}:
        raise HTTPException(status_code=400, detail="mode must be 'run' or 'submit'")
    try:
        problem = get_problem(req.problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")

    result = judge_code(problem, req.code, req.mode).as_dict()  # type: ignore[arg-type]
    submission_id = save_submission(
        problem_id=str(problem["id"]),
        problem_title=str(problem.get("title", problem["id"])),
        mode=req.mode,
        code=req.code,
        result=result,
    )
    result["submission_id"] = submission_id
    return result


@router.post("/api/check-code")
def api_check_code(req: CheckCodeRequest):
    try:
        compile(req.code, "user_solution.py", "exec")
    except SyntaxError as e:
        return {
            "ok": False,
            "error_type": e.__class__.__name__,
            "message": e.msg,
            "line": e.lineno,
            "offset": e.offset,
            "text": e.text.rstrip("\n") if e.text else "",
        }
    except Exception as e:
        return {
            "ok": False,
            "error_type": e.__class__.__name__,
            "message": str(e),
            "line": None,
            "offset": None,
            "text": "",
        }
    return {"ok": True, "message": "Python syntax OK"}


@router.get("/api/submissions")
def api_list_submissions(
    problem_id: str | None = None,
    limit: int = Query(100, ge=1, le=500),
):
    return {"submissions": list_submissions(problem_id=problem_id, limit=limit)}


@router.get("/api/submissions/{submission_id}")
def api_get_submission(submission_id: int):
    submission = get_submission(submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission


@router.get("/api/wrong-problems")
def api_wrong_problems():
    return {"wrong_problems": list_wrong_problems()}
