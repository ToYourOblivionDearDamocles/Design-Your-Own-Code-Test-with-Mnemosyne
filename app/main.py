from __future__ import annotations

import subprocess

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.database import get_submission, init_db, list_submissions, list_wrong_problems, save_submission
from app.dependencies import check_problem_requirements
from app.judge import generate_expected_output, judge_code
from app.llm_authoring import (
    build_repair_hint_report,
    edit_problem_draft,
    generate_problem_draft,
    generate_test_drafts,
    llm_status,
    repair_problem_draft,
)
from app.package_manager import install_dependency_requirements, install_requirements, runtime_status
from app.problem_authoring import (
    AUTHORING_API_SCHEMA,
    AUTHORING_PROMPT,
    PROBLEM_TEMPLATE,
    create_problem_collection_from_content,
    create_problem_from_content,
    parse_problem_content,
    parse_problem_collection,
    validate_problem_collection,
    validate_problem_spec,
)
from app.problem_store import append_test_case, delete_problem, get_problem, list_problems, list_tags, problem_solution, public_problem, save_problem
from app.ui import APP_HTML

app = FastAPI(title="Mnemosyne")


class SubmitRequest(BaseModel):
    problem_id: str
    code: str
    mode: str = "run"  # run = visible tests, submit = visible + hidden tests


class CheckCodeRequest(BaseModel):
    code: str


class InstallRequirementsRequest(BaseModel):
    scope: str
    problem_id: str | None = None


class AuthorProblemRequest(BaseModel):
    content: str
    overwrite: bool = False


class SaveProblemRequest(BaseModel):
    content: str


class AddTestCaseRequest(BaseModel):
    group: str
    test_case: dict


class AddGeneratedTestCaseRequest(BaseModel):
    group: str
    name: str = "new test"
    args: list


class GenerateExpectedRequest(BaseModel):
    args: list


class AuthorExpectedRequest(BaseModel):
    content: str
    args: list


class LlmProblemDraftRequest(BaseModel):
    request: str
    provider: str | None = None
    api_key: str | None = None
    count: int = 1
    model: str | None = None
    max_attempts: int = 2
    attachments: list[dict] = Field(default_factory=list)
    timeout_seconds: int | None = None


class LlmRepairDraftRequest(BaseModel):
    content: str
    request: str = ""
    provider: str | None = None
    api_key: str | None = None
    model: str | None = None
    max_attempts: int = 2


class LlmProblemEditRequest(BaseModel):
    request: str
    provider: str | None = None
    api_key: str | None = None
    model: str | None = None
    max_attempts: int = 2


class LlmTestDraftRequest(BaseModel):
    request: str
    group: str = "hidden_tests"
    count: int = 3
    provider: str | None = None
    api_key: str | None = None
    model: str | None = None


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return APP_HTML


def _with_repair_hints(result: dict) -> dict:
    if result.get("ok"):
        return result
    report = build_repair_hint_report(result.get("errors", []), result.get("warnings", []))
    return {
        **result,
        "repair_report": report,
        "repair_hints": report["hints"],
    }


@app.get("/api/problems")
def api_list_problems(tag: str | None = None):
    problems = list_problems()
    if tag:
        problems = [p for p in problems if tag in p.get("tags", [])]
    return {"problems": problems, "tag": tag}


@app.get("/api/tags")
def api_list_tags():
    return {"tags": list_tags()}


@app.get("/api/authoring/template")
def api_authoring_template():
    return {"template": PROBLEM_TEMPLATE}


@app.get("/api/authoring/prompt")
def api_authoring_prompt():
    return {"prompt": AUTHORING_PROMPT}


@app.get("/api/authoring/schema")
def api_authoring_schema():
    return {"schema": AUTHORING_API_SCHEMA}


@app.post("/api/authoring/validate")
def api_authoring_validate(req: AuthorProblemRequest):
    parse_warnings: list[str] = []
    try:
        problems = parse_problem_collection(req.content, warnings=parse_warnings)
    except ValueError as e:
        return _with_repair_hints({"ok": False, "errors": [str(e)], "warnings": parse_warnings, "problem": None, "problems": []})
    validation = validate_problem_collection(problems)
    validation["warnings"] = parse_warnings + validation["warnings"]
    return _with_repair_hints(validation)


@app.post("/api/authoring/run-reference")
def api_authoring_run_reference(req: AuthorProblemRequest):
    parse_warnings: list[str] = []
    try:
        problems = parse_problem_collection(req.content, warnings=parse_warnings)
    except ValueError as e:
        return _with_repair_hints({"ok": False, "errors": [str(e)], "warnings": parse_warnings, "problem": None, "problems": []})
    if len(problems) != 1:
        return _with_repair_hints(
            {
                "ok": False,
                "errors": ["Run reference expects exactly one problem."],
                "warnings": parse_warnings,
                "problem": None,
                "problems": problems,
            }
        )

    validation = validate_problem_spec(problems[0], verify_reference=False)
    validation["warnings"] = parse_warnings + validation["warnings"]
    if not validation["ok"]:
        return _with_repair_hints({**validation, "result": None})

    problem = validation["problem"]
    result = judge_code(problem, problem.get("reference_solution", ""), "submit").as_dict()
    return {
        "ok": result["status"] == "Accepted",
        "errors": [] if result["status"] == "Accepted" else [result.get("error") or result["status"]],
        "warnings": validation["warnings"],
        "problem": problem,
        "problems": [problem],
        "result": result,
    }


@app.post("/api/authoring/problems")
def api_authoring_create_problem(req: AuthorProblemRequest):
    try:
        return _with_repair_hints(create_problem_collection_from_content(req.content, overwrite=req.overwrite))
    except ValueError as e:
        return _with_repair_hints({"ok": False, "created": False, "created_count": 0, "errors": [str(e)], "warnings": [], "problem": None, "problems": []})


@app.post("/api/authoring/install-dependencies")
def api_authoring_install_dependencies(req: AuthorProblemRequest):
    parse_warnings: list[str] = []
    try:
        problems = parse_problem_collection(req.content, warnings=parse_warnings)
    except ValueError as e:
        return _with_repair_hints(
            {
                "ok": False,
                "installed": [],
                "errors": [str(e)],
                "warnings": parse_warnings,
                "problem": None,
                "problems": [],
            }
        )

    validation = validate_problem_collection(problems, verify_reference=False)
    validation["warnings"] = parse_warnings + validation["warnings"]
    requirements = _collect_problem_requirements(validation.get("problems", []))
    if validation["errors"] and not requirements:
        return _with_repair_hints(
            {
                "ok": False,
                "installed": [],
                "errors": validation["errors"],
                "warnings": validation["warnings"],
                "problem": validation.get("problem"),
                "problems": validation.get("problems", []),
            }
        )

    install_result = install_dependency_requirements(requirements)
    return {
        **install_result,
        "validation_ok": validation["ok"],
        "validation_errors": validation["errors"],
        "warnings": validation["warnings"],
        "problem": validation.get("problem"),
        "problems": validation.get("problems", []),
    }


def _collect_problem_requirements(problems: list[dict]) -> list[dict]:
    seen: set[tuple[str, str, str]] = set()
    requirements: list[dict] = []
    for problem in problems:
        for req in problem.get("requirements", []):
            if not isinstance(req, dict):
                continue
            key = (
                str(req.get("package") or ""),
                str(req.get("pip") or ""),
                str(req.get("import_name") or ""),
            )
            if key in seen:
                continue
            seen.add(key)
            requirements.append(req)
    return requirements


@app.post("/api/authoring/expected")
def api_authoring_generate_expected(req: AuthorExpectedRequest):
    parse_warnings: list[str] = []
    try:
        problem = parse_problem_content(req.content, warnings=parse_warnings)
    except ValueError as e:
        return {"ok": False, "errors": [str(e)], "warnings": [], "expected": None}

    validation = validate_problem_spec(problem)
    warnings = parse_warnings + validation["warnings"]
    if not validation["ok"]:
        return {"ok": False, "errors": validation["errors"], "warnings": warnings, "expected": None}

    result = generate_expected_output(validation["problem"], req.args)
    return {**result, "warnings": warnings}


@app.get("/api/llm/status")
def api_llm_status():
    return llm_status()


@app.post("/api/llm/author/problems")
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


@app.post("/api/llm/author/repair")
def api_llm_repair_problem(req: LlmRepairDraftRequest):
    return repair_problem_draft(
        req.content,
        user_request=req.request,
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        max_attempts=req.max_attempts,
    )


@app.post("/api/llm/problems/{problem_id}/edit")
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


@app.post("/api/llm/problems/{problem_id}/tests")
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


@app.get("/api/problems/{problem_id}")
def api_get_problem(problem_id: str):
    try:
        problem = get_problem(problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    data = public_problem(problem)
    data["dependency_status"] = check_problem_requirements(problem)
    return data


@app.get("/api/problems/{problem_id}/raw")
def api_get_problem_raw(problem_id: str):
    try:
        problem = get_problem(problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    return {"problem": problem}


@app.put("/api/problems/{problem_id}")
def api_update_problem(problem_id: str, req: SaveProblemRequest):
    try:
        existing = get_problem(problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    parse_warnings: list[str] = []
    try:
        problem = parse_problem_content(req.content, warnings=parse_warnings)
    except ValueError as e:
        return {"ok": False, "saved": False, "errors": [str(e)], "warnings": [], "problem": None}

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


@app.delete("/api/problems/{problem_id}")
def api_delete_problem(problem_id: str):
    try:
        deleted_path = delete_problem(problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    return {"ok": True, "deleted": True, "problem_id": problem_id, "path": str(deleted_path)}


@app.post("/api/problems/{problem_id}/tests")
def api_add_problem_test(problem_id: str, req: AddTestCaseRequest):
    try:
        updated = append_test_case(problem_id, req.group, req.test_case)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    except ValueError as e:
        return {"ok": False, "saved": False, "errors": [str(e)], "warnings": [], "problem": None}

    validation = validate_problem_spec(updated)
    if not validation["ok"]:
        return {"saved": False, **validation}

    save_problem(validation["problem"])
    return {"ok": True, "saved": True, "problem": updated, "warnings": validation["warnings"], "errors": []}


@app.post("/api/problems/{problem_id}/tests/generated")
def api_add_generated_problem_test(problem_id: str, req: AddGeneratedTestCaseRequest):
    if req.group not in {"visible_tests", "hidden_tests"}:
        return {"ok": False, "saved": False, "errors": ["group must be visible_tests or hidden_tests"], "warnings": [], "problem": None}
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
        return {"ok": False, "saved": False, "errors": [str(e)], "warnings": [], "problem": None}

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


@app.post("/api/problems/{problem_id}/expected")
def api_generate_problem_expected(problem_id: str, req: GenerateExpectedRequest):
    try:
        problem = get_problem(problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    return generate_expected_output(problem, req.args)


@app.get("/api/problems/{problem_id}/solution")
def api_get_problem_solution(problem_id: str):
    try:
        problem = get_problem(problem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem_solution(problem)


@app.get("/api/runtime")
def api_runtime(problem_id: str | None = None):
    if problem_id:
        try:
            return runtime_status(problem_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Problem not found")
    return runtime_status(None)


@app.post("/api/runtime/install")
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


@app.post("/api/submit")
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


@app.post("/api/check-code")
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


@app.get("/api/submissions")
def api_list_submissions(
    problem_id: str | None = None,
    limit: int = Query(100, ge=1, le=500),
):
    return {"submissions": list_submissions(problem_id=problem_id, limit=limit)}


@app.get("/api/submissions/{submission_id}")
def api_get_submission(submission_id: int):
    submission = get_submission(submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission


@app.get("/api/wrong-problems")
def api_wrong_problems():
    return {"wrong_problems": list_wrong_problems()}


INDEX_HTML = r'''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Mnemosyne</title>
  <style>
    :root { font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; background: #f7f7f8; color: #111827; }
    header { padding: 16px 24px; background: #111827; color: white; display: flex; align-items: center; justify-content: space-between; }
    header a { color: #dbeafe; text-decoration: none; margin-left: 12px; }
    main { display: grid; grid-template-columns: 42% 58%; gap: 16px; padding: 16px; height: calc(100vh - 74px); box-sizing: border-box; }
    section { background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; overflow: auto; }
    select, button { font-size: 14px; padding: 8px 10px; border-radius: 8px; border: 1px solid #d1d5db; }
    button { cursor: pointer; background: #111827; color: white; margin-right: 8px; }
    button.secondary { background: white; color: #111827; }
    button.small { padding: 5px 8px; font-size: 12px; }
    textarea { width: 100%; height: 42vh; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 14px; line-height: 1.4; border: 1px solid #d1d5db; border-radius: 10px; padding: 12px; box-sizing: border-box; }
    pre { background: #f3f4f6; padding: 12px; border-radius: 10px; overflow: auto; white-space: pre-wrap; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { border-bottom: 1px solid #e5e7eb; padding: 8px; text-align: left; vertical-align: top; }
    th { background: #f9fafb; position: sticky; top: 0; }
    .row { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
    .tag { display: inline-block; background: #eef2ff; color: #3730a3; padding: 2px 8px; border-radius: 999px; margin-right: 6px; font-size: 12px; }
    .accepted { color: #047857; font-weight: 700; }
    .wrong { color: #b91c1c; font-weight: 700; }
    .muted { color: #6b7280; }
    .panel-title { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
    .history-box { max-height: 26vh; overflow: auto; border: 1px solid #e5e7eb; border-radius: 10px; }
    .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    code { background: #f3f4f6; padding: 1px 4px; border-radius: 4px; }
  </style>
</head>
<body>
  <header>
    <div>
      <strong>Mnemosyne</strong>
      <span style="opacity:.75; margin-left: 8px;">Recall, Rebuild, Test Yourself</span>
    </div>
    <nav>
      <a href="#currentHistory" onclick="loadCurrentHistory()">Current problem history</a>
      <a href="#allHistory" onclick="loadAllHistory()">All submissions</a>
      <a href="#wrongProblems" onclick="loadWrongProblems()">Wrong problems</a>
    </nav>
  </header>
  <main>
    <section>
      <div class="row">
        <label for="problemSelect"><strong>Problem</strong></label>
        <select id="problemSelect"></select>
      </div>
      <h2 id="title"></h2>
      <div id="meta"></div>
      <div id="statement"></div>
      <h3>Visible tests</h3>
      <pre id="visibleTests"></pre>
    </section>

    <section>
      <h3>Your code</h3>
      <textarea id="code"></textarea>
      <div style="margin-top: 12px;">
        <button onclick="submitCode('run')">Run visible tests</button>
        <button class="secondary" onclick="submitCode('submit')">Submit hidden tests</button>
      </div>

      <div class="panel-title">
        <h3>Result</h3>
        <span id="status"></span>
      </div>
      <pre id="result">No submission yet.</pre>

      <div class="panel-title" id="currentHistory">
        <h3>Current problem submission history</h3>
        <button class="secondary small" onclick="loadCurrentHistory()">Refresh</button>
      </div>
      <div class="history-box"><table id="currentHistoryTable"></table></div>

      <div class="panel-title" id="allHistory">
        <h3>All submissions</h3>
        <button class="secondary small" onclick="loadAllHistory()">Refresh</button>
      </div>
      <div class="history-box"><table id="allHistoryTable"></table></div>

      <div class="panel-title" id="wrongProblems">
        <h3>Wrong problems</h3>
        <button class="secondary small" onclick="loadWrongProblems()">Refresh</button>
      </div>
      <div class="history-box"><table id="wrongProblemsTable"></table></div>

      <h3>Submission detail</h3>
      <pre id="submissionDetail">Click a history row's Detail button.</pre>
    </section>
  </main>

  <script>
    let currentProblem = null;

    async function loadProblems() {
      const res = await fetch('/api/problems');
      const data = await res.json();
      const select = document.getElementById('problemSelect');
      select.innerHTML = '';
      data.problems.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = `${p.title} (${p.difficulty})`;
        select.appendChild(opt);
      });
      select.onchange = () => loadProblem(select.value);
      if (data.problems.length) await loadProblem(data.problems[0].id);
      await loadAllHistory();
      await loadWrongProblems();
    }

    async function loadProblem(problemId) {
      const res = await fetch(`/api/problems/${problemId}`);
      currentProblem = await res.json();
      document.getElementById('title').textContent = currentProblem.title;
      document.getElementById('meta').innerHTML = [currentProblem.difficulty, currentProblem.entry_kind, ...(currentProblem.tags || [])]
        .map(x => `<span class="tag">${escapeHtml(String(x))}</span>`).join('');
      document.getElementById('statement').innerHTML = markdownLite(currentProblem.statement || '');
      document.getElementById('visibleTests').textContent = JSON.stringify(currentProblem.visible_tests || [], null, 2);
      document.getElementById('code').value = currentProblem.starter_code || '';
      document.getElementById('status').innerHTML = '';
      document.getElementById('result').textContent = 'No submission yet.';
      document.getElementById('submissionDetail').textContent = 'Click a history row\'s Detail button.';
      await loadCurrentHistory();
    }

    async function submitCode(mode) {
      if (!currentProblem) return;
      document.getElementById('status').textContent = 'Running...';
      document.getElementById('result').textContent = '';
      const res = await fetch('/api/submit', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({problem_id: currentProblem.id, code: document.getElementById('code').value, mode})
      });
      const data = await res.json();
      const klass = data.status === 'Accepted' ? 'accepted' : 'wrong';
      document.getElementById('status').innerHTML = `<span class="${klass}">${escapeHtml(data.status)}</span> — ${data.passed}/${data.total} passed — submission #${data.submission_id}`;
      document.getElementById('result').textContent = JSON.stringify(data, null, 2);
      await loadCurrentHistory();
      await loadAllHistory();
      await loadWrongProblems();
    }

    async function loadCurrentHistory() {
      if (!currentProblem) return;
      const res = await fetch(`/api/submissions?problem_id=${encodeURIComponent(currentProblem.id)}&limit=50`);
      const data = await res.json();
      renderSubmissionTable('currentHistoryTable', data.submissions || []);
    }

    async function loadAllHistory() {
      const res = await fetch('/api/submissions?limit=100');
      const data = await res.json();
      renderSubmissionTable('allHistoryTable', data.submissions || []);
    }

    async function loadWrongProblems() {
      const res = await fetch('/api/wrong-problems');
      const data = await res.json();
      renderWrongProblemsTable(data.wrong_problems || []);
    }

    function renderSubmissionTable(tableId, rows) {
      const table = document.getElementById(tableId);
      if (!rows.length) {
        table.innerHTML = '<tr><td class="muted">No submissions yet.</td></tr>';
        return;
      }
      table.innerHTML = `
        <tr>
          <th>ID</th><th>Problem</th><th>Mode</th><th>Status</th><th>Passed</th><th>Time</th><th></th>
        </tr>
        ${rows.map(r => {
          const klass = r.status === 'Accepted' ? 'accepted' : 'wrong';
          return `<tr>
            <td>#${r.id}</td>
            <td>${escapeHtml(r.problem_title)}</td>
            <td>${escapeHtml(r.mode)}</td>
            <td class="${klass}">${escapeHtml(r.status)}</td>
            <td>${r.passed}/${r.total}</td>
            <td>${formatTime(r.created_at)}</td>
            <td><button class="secondary small" onclick="loadSubmissionDetail(${r.id})">Detail</button></td>
          </tr>`;
        }).join('')}
      `;
    }

    function renderWrongProblemsTable(rows) {
      const table = document.getElementById('wrongProblemsTable');
      if (!rows.length) {
        table.innerHTML = '<tr><td class="muted">No wrong submissions yet.</td></tr>';
        return;
      }
      table.innerHTML = `
        <tr>
          <th>Problem</th><th>Wrong count</th><th>Latest status</th><th>Latest result</th><th>Latest time</th><th></th>
        </tr>
        ${rows.map(r => {
          const klass = r.latest_status === 'Accepted' ? 'accepted' : 'wrong';
          return `<tr>
            <td>${escapeHtml(r.problem_title)}</td>
            <td>${r.wrong_count}</td>
            <td class="${klass}">${escapeHtml(r.latest_status)}</td>
            <td>${r.latest_passed}/${r.latest_total}</td>
            <td>${formatTime(r.latest_created_at)}</td>
            <td><button class="secondary small" onclick="loadSubmissionDetail(${r.latest_submission_id})">Latest</button></td>
          </tr>`;
        }).join('')}
      `;
    }

    async function loadSubmissionDetail(id) {
      const res = await fetch(`/api/submissions/${id}`);
      const data = await res.json();
      const failedTests = (data.result?.tests || []).filter(t => !t.passed);
      const view = {
        id: data.id,
        problem_id: data.problem_id,
        problem_title: data.problem_title,
        mode: data.mode,
        status: data.status,
        passed: `${data.passed}/${data.total}`,
        created_at: data.created_at,
        failed_tests: failedTests,
        result: data.result,
        code: data.code,
      };
      document.getElementById('submissionDetail').textContent = JSON.stringify(view, null, 2);
    }

    function markdownLite(s) {
      return escapeHtml(s)
        .replace(/^### (.*)$/gm, '<h3>$1</h3>')
        .replace(/^## (.*)$/gm, '<h2>$1</h2>')
        .replace(/^# (.*)$/gm, '<h1>$1</h1>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br/>');
    }

    function escapeHtml(s) {
      return s
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
    }

    function formatTime(iso) {
      if (!iso) return '';
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return iso;
      return d.toLocaleString();
    }

    loadProblems();
  </script>
</body>
</html>
'''
