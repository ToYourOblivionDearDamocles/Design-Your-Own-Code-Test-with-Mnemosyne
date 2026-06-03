from __future__ import annotations

import inspect
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mnemosyne import main
from mnemosyne.chat_models import service as chat_model_service
from mnemosyne.problem_authoring import AUTHORING_API_SCHEMA, AUTHORING_PROMPT, format_problem_json
from mnemosyne.storage.problems import get_problem
from mnemosyne.prompts import PROMPT_DIR, prompt_only_contract, render_prompt
from mnemosyne.verifier import service as verifier_service
from mnemosyne.verifier.repair_hints import build_repair_hint_report

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


def main_check() -> int:
    direct_prompt_path = PROMPT_DIR / "direct_json_authoring_prompt.json"
    system_prompt_path = PROMPT_DIR / "problem_agent_system.json"
    check("prompt JSON folder exists", PROMPT_DIR.exists(), PROMPT_DIR)
    check("Direct JSON prompt is externalized", direct_prompt_path.exists(), direct_prompt_path)
    check("agent system prompt is externalized", system_prompt_path.exists(), system_prompt_path)

    direct_prompt = render_prompt("direct_json_authoring_prompt")
    system_prompt = render_prompt("problem_agent_system")
    check("AUTHORING_PROMPT is loaded from prompt JSON", AUTHORING_PROMPT == direct_prompt)
    check("Direct JSON prompt explains final User request placement", "User request:" in direct_prompt)
    check("agent prompt requires explicit learning modules", "Theory" in system_prompt and "Example" in system_prompt)

    contract = prompt_only_contract({"name": "mnemosyne_problem_collection", "schema": AUTHORING_API_SCHEMA["schema"]})
    check("fallback contract comes from prompt module", "Required JSON contract" in contract and "Few-shot examples" in contract)

    problem = get_problem("two_sum")
    content = format_problem_json({"problems": [problem]})
    validation = verifier_service.validate_content(content)
    check("verifier service validates existing problem", validation.get("ok"), validation.get("errors"))
    check("verifier service returns layer report", {layer.get("id") for layer in validation.get("layers", [])} >= {"json", "schema", "content", "code"})

    bad_report = build_repair_hint_report(["visible_tests[0].args must be a list of positional arguments."], [])
    check("repair hints are available outside LLM authoring", bad_report["hints"][0]["code"] == "function_test_shape", bad_report)

    route_paths = {route.path for route in main.app.routes}
    check("FastAPI exposes verifier validate API", "/api/verifier/validate" in route_paths)
    check("FastAPI exposes verifier schema API", "/api/verifier/schema" in route_paths)
    check("FastAPI exposes chat model status API", "/api/chat-models/status" in route_paths)
    check("FastAPI exposes chat model generation API", "/api/chat-models/generate-json" in route_paths)

    check("chat model service has provider-level generate_json", callable(chat_model_service.generate_json))
    signature = inspect.signature(chat_model_service.generate_json)
    check("chat model service accepts messages and provider", "messages" in signature.parameters and "provider" in signature.parameters)

    chat_provider_path = ROOT / "mnemosyne/chat_models/providers.py"
    verifier_layers_path = ROOT / "mnemosyne/verifier/layers.py"
    storage_problems_path = ROOT / "mnemosyne/storage/problems.py"
    storage_submissions_path = ROOT / "mnemosyne/storage/submissions.py"
    runtime_judge_path = ROOT / "mnemosyne/runtime/judge.py"
    runtime_dependencies_path = ROOT / "mnemosyne/runtime/dependencies.py"
    check("chat model providers are separated", chat_provider_path.exists(), chat_provider_path)
    check("verifier layers are separated", verifier_layers_path.exists(), verifier_layers_path)
    check("problem storage is separated", storage_problems_path.exists(), storage_problems_path)
    check("submission storage is separated", storage_submissions_path.exists(), storage_submissions_path)
    check("judge runtime is separated", runtime_judge_path.exists(), runtime_judge_path)
    check("dependency runtime is separated", runtime_dependencies_path.exists(), runtime_dependencies_path)
    check("old top-level storage/runtime files removed", not any((ROOT / f"mnemosyne/{name}.py").exists() for name in ["database", "problem_store", "dependencies", "package_manager", "judge", "json_format"]))

    chat_service_source = (ROOT / "mnemosyne/chat_models/service.py").read_text(encoding="utf-8")
    chat_provider_source = chat_provider_path.read_text(encoding="utf-8") if chat_provider_path.exists() else ""
    check("chat model service does not import llm_authoring", "llm_authoring" not in chat_service_source)
    check("chat model providers do not import llm_authoring", "llm_authoring" not in chat_provider_source)

    problem_authoring_source = (ROOT / "mnemosyne/problem_authoring.py").read_text(encoding="utf-8")
    llm_authoring_source = (ROOT / "mnemosyne/llm_authoring.py").read_text(encoding="utf-8")
    check("problem_authoring has no embedded Direct JSON prompt block", 'AUTHORING_PROMPT = """' not in problem_authoring_source)
    check("llm_authoring system prompt is loaded from prompt JSON", 'return render_prompt("problem_agent_system")' in llm_authoring_source)
    check("llm_authoring repair prompt is loaded from prompt JSON", '"repair_problem_user_message"' in llm_authoring_source)

    print(f"\nSummary: {CHECKS_RUN - len(FAILURES)}/{CHECKS_RUN} checks passed")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main_check())
