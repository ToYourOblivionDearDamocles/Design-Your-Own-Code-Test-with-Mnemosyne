from __future__ import annotations

import base64
import binascii
import copy
import json
import re
from typing import Any

from mnemosyne.runtime.judge import generate_expected_output
from mnemosyne.prompts import render_prompt
from mnemosyne.chat_models.providers import (
    DeepSeekClient,
    GeminiClient,
    JsonGeneratingClient,
    LLMNotConfigured,
    LLMRequestError,
    OllamaChatClient,
    OpenAICompatibleClient,
    OpenAIResponsesClient,
    _gemini_request_timeout,
    _urlopen_json,
    client_generate_json as _client_generate_json,
    client_supports_multimodal_attachments as _client_supports_multimodal_attachments,
    llm_status,
    make_llm_client,
)
from mnemosyne.verifier.repair_hints import build_repair_hint_report, repair_hint_report as _repair_hint_report
from mnemosyne.problem_authoring import (
    AUTHORING_API_SCHEMA,
    format_problem_json,
    parse_problem_collection,
    prepare_problem_content,
    validate_problem_collection,
    validate_problem_spec,
)


DEFAULT_MAX_ATTEMPTS = 2
MAX_BATCH_COUNT = 10
MAX_TEST_COUNT = 8
MAX_ATTACHMENT_COUNT = 8
MAX_ATTACHMENT_BYTES = 8 * 1024 * 1024
MAX_TOTAL_TEXT_ATTACHMENT_CHARS = 60_000
TEXT_ATTACHMENT_EXTENSIONS = {".md", ".markdown", ".txt", ".json", ".csv", ".tsv", ".py", ".yaml", ".yml"}
TEXT_ATTACHMENT_MIME_PREFIXES = ("text/",)
TEXT_ATTACHMENT_MIME_TYPES = {
    "application/json",
    "application/x-yaml",
    "application/yaml",
}
MULTIMODAL_ATTACHMENT_MIME_TYPES = {"application/pdf"}
MULTIMODAL_ATTACHMENT_MIME_PREFIXES = ("image/",)


def generate_problem_draft(
    user_request: str,
    *,
    provider: str | None = None,
    api_key: str | None = None,
    count: int = 1,
    model: str | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    client: JsonGeneratingClient | None = None,
    attachments: list[dict[str, Any]] | None = None,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    request_text = user_request.strip()
    if not request_text and attachments:
        request_text = "Create polished Python coding-practice problem(s) from the attached source materials."
    if not request_text:
        return _failure("Describe the problem you want to generate.")

    attachment_bundle = _prepare_llm_attachments(attachments or [])
    if attachment_bundle["errors"]:
        result = _failure("; ".join(attachment_bundle["errors"]))
        result["warnings"] = attachment_bundle["warnings"]
        result["attachments"] = attachment_bundle["summary"]
        return result
    request_text = _augment_request_with_attachments(request_text, attachment_bundle)

    count = _clamp_int(count, 1, MAX_BATCH_COUNT)
    timeout_seconds = _clamp_optional_int(timeout_seconds, 10, 600)
    if count > 1 and attachment_bundle["multimodal"]:
        attachment_bundle["warnings"].append(
            "PDF/image attachments make LLM calls much slower because each generated problem may need to read the material. "
            "Use a longer timeout, a faster Gemini model, or a smaller problem count if requests time out."
        )
    if count > 1:
        result = _run_sequential_problem_generation(
            user_request=request_text,
            count=count,
            provider=provider,
            api_key=api_key,
            model=model,
            max_attempts=max_attempts,
            client=client,
            attachments=attachment_bundle["multimodal"],
            timeout_seconds=timeout_seconds,
        )
        return _with_attachment_metadata(result, attachment_bundle)

    result = _run_problem_agent_loop(
        user_request=request_text,
        first_messages=_create_problem_messages(request_text, count),
        count=count,
        provider=provider,
        api_key=api_key,
        model=model,
        max_attempts=max_attempts,
        client=client,
        attachments=attachment_bundle["multimodal"],
        timeout_seconds=timeout_seconds,
    )
    return _with_attachment_metadata(result, attachment_bundle)


def _run_sequential_problem_generation(
    *,
    user_request: str,
    count: int,
    provider: str | None,
    api_key: str | None,
    model: str | None,
    max_attempts: int,
    client: JsonGeneratingClient | None,
    attachments: list[dict[str, Any]] | None = None,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    try:
        llm_client = client or make_llm_client(provider=provider, api_key=api_key, timeout_seconds=timeout_seconds)
    except (LLMNotConfigured, LLMRequestError) as exc:
        return _failure(str(exc), attempts=[])

    problems: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    problem_results: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    agent_plan: dict[str, Any] | None = None
    item_attachments = attachments or []

    if item_attachments:
        digest = _create_source_digest(
            llm_client=llm_client,
            user_request=user_request,
            count=count,
            model=model,
            attachments=item_attachments,
        )
        digest_attempt = {
            "stage": "source_digest",
            "ok": digest["ok"],
            "errors": digest.get("errors", []),
            "warnings": digest.get("warnings", []),
            "raw_text": str(digest.get("raw_text", ""))[:4000],
        }
        attempts.append(digest_attempt)
        if digest["ok"]:
            agent_plan = digest["digest"]
            user_request = _augment_request_with_source_digest(user_request, agent_plan)
            item_attachments = []
            warnings.append(
                "Agent speedup: read PDF/image attachments once into a source digest; "
                "problem generation and repair now use text-only context."
            )
        else:
            warnings.append(
                "Could not create a source digest, so each problem will use the original PDF/image attachments. "
                "This is slower and may time out."
            )
            warnings.extend(digest.get("warnings", []))

    for index in range(1, count + 1):
        request_for_item = _sequential_problem_request(user_request, index, count, problems)
        result = _run_problem_agent_loop(
            user_request=request_for_item,
            first_messages=_create_problem_messages(request_for_item, 1),
            count=1,
            provider=provider,
            api_key=api_key,
            model=model,
            max_attempts=max_attempts,
            client=llm_client,
            attachments=item_attachments,
            timeout_seconds=timeout_seconds,
        )

        item_attempts = result.get("attempts") or []
        for attempt in item_attempts:
            tagged_attempt = dict(attempt)
            tagged_attempt["problem_index"] = index
            attempts.append(tagged_attempt)

        if result.get("ok") and result.get("problem"):
            problem = result["problem"]
            problems.append(problem)
            problem_results.append(
                {
                    "index": index,
                    "ok": True,
                    "problem_id": problem.get("id"),
                    "title": problem.get("title"),
                    "attempts": len(item_attempts),
                    "errors": [],
                    "warnings": result.get("warnings", []),
                }
            )
            warnings.extend(f"problem {index}: {warning}" for warning in result.get("warnings", []))
            continue

        item_errors = result.get("errors") or ["LLM draft did not pass validation."]
        item_warnings = result.get("warnings") or []
        errors.extend(f"problem {index}: {error}" for error in item_errors)
        warnings.extend(f"problem {index}: {warning}" for warning in item_warnings)
        problem_results.append(
            {
                "index": index,
                "ok": False,
                "problem_id": None,
                "title": None,
                "attempts": len(item_attempts),
                "errors": item_errors,
                "warnings": item_warnings,
                "repair_hints": result.get("repair_hints", []),
            }
        )

    validation = validate_problem_collection(problems) if problems else {
        "ok": False,
        "errors": ["No valid problems were generated."],
        "warnings": [],
        "problems": [],
        "problem": None,
        "count": 0,
    }
    if not validation["ok"]:
        errors.extend(validation["errors"])
    warnings.extend(validation["warnings"])
    normalized_problems = validation.get("problems") or problems

    content_value: Any = normalized_problems[0] if len(normalized_problems) == 1 else normalized_problems
    generated = len(normalized_problems)
    ok = generated == count and not errors and validation["ok"]
    repair_report = _repair_hint_report(errors, warnings) if not ok else {}
    return {
        "ok": ok,
        "errors": errors,
        "warnings": warnings,
        "problem": normalized_problems[0] if len(normalized_problems) == 1 else None,
        "problems": normalized_problems,
        "count": generated,
        "requested_count": count,
        "content": format_problem_json(content_value),
        "attempts": attempts,
        "problem_results": problem_results,
        "repair_report": repair_report,
        "repair_hints": repair_report.get("hints", []),
        "used_llm": True,
        "sequential": True,
        "agent_plan": agent_plan,
        "message": f"Generated {generated}/{count} problem(s) one at a time.",
    }


def _sequential_problem_request(user_request: str, index: int, count: int, previous_problems: list[dict[str, Any]]) -> str:
    previous_ids = [str(problem.get("id")) for problem in previous_problems if problem.get("id")]
    previous_text = ", ".join(previous_ids) if previous_ids else "none"
    return (
        f"{user_request}\n\n"
        f"Generate item {index} of {count}. Return exactly one distinct problem. "
        f"Do not reuse these previous problem ids: {previous_text}."
    )


def _create_source_digest(
    *,
    llm_client: JsonGeneratingClient,
    user_request: str,
    count: int,
    model: str | None,
    attachments: list[dict[str, Any]],
) -> dict[str, Any]:
    if not _client_supports_multimodal_attachments(llm_client):
        return {
            "ok": False,
            "errors": ["The selected provider cannot create a multimodal source digest."],
            "warnings": [],
            "digest": None,
            "raw_text": "",
        }

    messages = _source_digest_messages(user_request, count, attachments)
    try:
        raw_text = _client_generate_json(
            llm_client,
            messages,
            _source_digest_schema(count),
            model=model,
            attachments=attachments,
        )
    except (LLMNotConfigured, LLMRequestError) as exc:
        return {
            "ok": False,
            "errors": [str(exc)],
            "warnings": [],
            "digest": None,
            "raw_text": "",
        }

    try:
        data = _loads_llm_json(raw_text)
    except ValueError as exc:
        return {
            "ok": False,
            "errors": [str(exc)],
            "warnings": [],
            "digest": None,
            "raw_text": raw_text,
        }

    normalized = _normalize_source_digest(data, count)
    if normalized["errors"]:
        return {**normalized, "ok": False, "raw_text": raw_text}
    return {**normalized, "ok": True, "raw_text": raw_text}


def _source_digest_messages(user_request: str, count: int, attachments: list[dict[str, Any]]) -> list[dict[str, str]]:
    attachment_names = ", ".join(f"{item['name']} ({item['mime_type']})" for item in attachments)
    return [
        {
            "role": "system",
            "content": (
                "You are a fast curriculum extraction agent for a local coding-practice app. "
                "Read the attached source material once and produce a compact JSON source digest. "
                "Do not create full problem JSON yet. Focus on concepts, formulas, data structures, "
                "and concrete programming exercises that can later become verifier-friendly Python problems."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Original user request:\n{user_request}\n\n"
                f"Attached source materials: {attachment_names}\n\n"
                f"Create a compact source digest and exactly {count} distinct problem briefs. "
                "Each brief should name the learning objective, expected Python interface idea, likely package dependencies, "
                "and 2-4 edge cases. Keep it short enough that another model call can use it without the attachments."
            ),
        },
    ]


def _source_digest_schema(count: int) -> dict[str, Any]:
    count = _clamp_int(count, 1, MAX_BATCH_COUNT)
    return {
        "name": "mnemosyne_source_digest",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["summary", "key_concepts", "problem_briefs"],
            "properties": {
                "summary": {"type": "string"},
                "key_concepts": {"type": "array", "items": {"type": "string"}},
                "problem_briefs": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": count,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["id_hint", "title", "learning_goal", "interface", "edge_cases"],
                        "properties": {
                            "id_hint": {"type": "string"},
                            "title": {"type": "string"},
                            "learning_goal": {"type": "string"},
                            "interface": {"type": "string"},
                            "packages": {"type": "array", "items": {"type": "string"}},
                            "edge_cases": {"type": "array", "items": {"type": "string"}},
                            "source_notes": {"type": "string"},
                        },
                    },
                },
            },
        },
    }


def _normalize_source_digest(data: Any, count: int) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return {"errors": ["Source digest response must be a JSON object."], "warnings": [], "digest": None}

    summary = str(data.get("summary") or "").strip()
    if not summary:
        errors.append("Source digest summary is required.")

    concepts = data.get("key_concepts")
    if not isinstance(concepts, list):
        concepts = []
        warnings.append("Source digest key_concepts was missing or invalid.")
    concepts = [str(item).strip() for item in concepts if str(item).strip()][:12]

    raw_briefs = data.get("problem_briefs")
    if not isinstance(raw_briefs, list) or not raw_briefs:
        errors.append("Source digest must contain at least one problem_brief.")
        raw_briefs = []

    briefs: list[dict[str, Any]] = []
    for idx, raw in enumerate(raw_briefs[:count]):
        if not isinstance(raw, dict):
            warnings.append(f"Skipped invalid source digest problem_briefs[{idx}].")
            continue
        title = str(raw.get("title") or f"Problem {idx + 1}").strip()
        learning_goal = str(raw.get("learning_goal") or raw.get("goal") or "").strip()
        interface = str(raw.get("interface") or "").strip()
        edge_cases = raw.get("edge_cases")
        packages = raw.get("packages")
        briefs.append(
            {
                "id_hint": str(raw.get("id_hint") or _snake_hint(title)).strip() or f"problem_{idx + 1}",
                "title": title,
                "learning_goal": learning_goal or title,
                "interface": interface or "Choose an appropriate Python function interface.",
                "packages": [str(item).strip() for item in packages if str(item).strip()] if isinstance(packages, list) else [],
                "edge_cases": [str(item).strip() for item in edge_cases if str(item).strip()] if isinstance(edge_cases, list) else [],
                "source_notes": str(raw.get("source_notes") or "").strip(),
            }
        )

    if not briefs:
        errors.append("Source digest did not contain any usable problem briefs.")

    return {
        "errors": errors,
        "warnings": warnings,
        "digest": {
            "summary": summary[:4000],
            "key_concepts": concepts,
            "problem_briefs": briefs,
        },
    }


def _augment_request_with_source_digest(user_request: str, digest: dict[str, Any]) -> str:
    return (
        f"{user_request}\n\n"
        "Use this source digest instead of rereading the original PDF/image attachments. "
        "The digest was extracted once by an earlier agent step:\n"
        f"{json.dumps(digest, ensure_ascii=False, indent=2)}"
    )


def _snake_hint(value: str) -> str:
    lowered = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    if not lowered:
        return "generated_problem"
    if not lowered[0].isalpha():
        lowered = f"problem_{lowered}"
    return lowered[:80]


def _prepare_llm_attachments(raw_attachments: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    text_blocks: list[str] = []
    multimodal: list[dict[str, Any]] = []
    summary: list[dict[str, Any]] = []

    if len(raw_attachments) > MAX_ATTACHMENT_COUNT:
        errors.append(f"Attach at most {MAX_ATTACHMENT_COUNT} files.")
        raw_attachments = raw_attachments[:MAX_ATTACHMENT_COUNT]

    text_budget = MAX_TOTAL_TEXT_ATTACHMENT_CHARS
    for idx, raw in enumerate(raw_attachments):
        if not isinstance(raw, dict):
            errors.append(f"attachments[{idx}] must be an object.")
            continue
        name = _safe_attachment_name(raw.get("name") or f"attachment_{idx + 1}")
        mime_type = _normalize_attachment_mime(raw.get("mime_type") or raw.get("type"), name)
        text = raw.get("text")
        content_base64 = raw.get("content_base64") or raw.get("data")
        size_bytes = _safe_int(raw.get("size_bytes"), 0)

        if isinstance(text, str):
            clipped = text[:max(text_budget, 0)]
            if len(text) > len(clipped):
                warnings.append(f"Truncated text attachment `{name}` to fit the prompt context budget.")
            text_budget -= len(clipped)
            text_blocks.append(
                f"<attachment name=\"{name}\" mime_type=\"{mime_type}\">\n{clipped}\n</attachment>"
            )
            summary.append({"name": name, "mime_type": mime_type, "kind": "text", "size_bytes": size_bytes})
            continue

        if not isinstance(content_base64, str) or not content_base64.strip():
            errors.append(f"attachments[{idx}] `{name}` must include text or content_base64.")
            continue

        decoded = _decode_attachment_base64(content_base64)
        if decoded is None:
            errors.append(f"attachments[{idx}] `{name}` has invalid base64 content.")
            continue
        if len(decoded) > MAX_ATTACHMENT_BYTES:
            errors.append(f"attachments[{idx}] `{name}` is larger than {MAX_ATTACHMENT_BYTES // (1024 * 1024)} MB.")
            continue

        if _is_text_attachment(name, mime_type):
            try:
                decoded_text = decoded.decode("utf-8")
            except UnicodeDecodeError:
                errors.append(f"attachments[{idx}] `{name}` looks like text but is not valid UTF-8.")
                continue
            clipped = decoded_text[:max(text_budget, 0)]
            if len(decoded_text) > len(clipped):
                warnings.append(f"Truncated text attachment `{name}` to fit the prompt context budget.")
            text_budget -= len(clipped)
            text_blocks.append(
                f"<attachment name=\"{name}\" mime_type=\"{mime_type}\">\n{clipped}\n</attachment>"
            )
            summary.append({"name": name, "mime_type": mime_type, "kind": "text", "size_bytes": len(decoded)})
            continue

        if not _is_multimodal_attachment(mime_type):
            errors.append(
                f"attachments[{idx}] `{name}` has unsupported type `{mime_type}`. "
                "Use .md/.txt/.json/.py/.csv text, PDF, or image files."
            )
            continue

        multimodal.append(
            {
                "name": name,
                "mime_type": mime_type,
                "content_base64": content_base64.strip(),
                "size_bytes": len(decoded),
            }
        )
        summary.append({"name": name, "mime_type": mime_type, "kind": "multimodal", "size_bytes": len(decoded)})

    return {
        "errors": errors,
        "warnings": warnings,
        "text_context": "\n\n".join(text_blocks),
        "multimodal": multimodal,
        "summary": summary,
    }


def _augment_request_with_attachments(user_request: str, attachment_bundle: dict[str, Any]) -> str:
    text_context = str(attachment_bundle.get("text_context") or "").strip()
    multimodal = attachment_bundle.get("multimodal") or []
    if not text_context and not multimodal:
        return user_request

    parts = [user_request]
    if text_context:
        parts.append(
            "Attached text source materials are below. Use them as inspiration and source context, "
            "but still return only valid problem JSON.\n\n"
            f"{text_context}"
        )
    if multimodal:
        names = ", ".join(f"{item['name']} ({item['mime_type']})" for item in multimodal)
        parts.append(
            "Additional PDF/image source materials are attached as multimodal input: "
            f"{names}. Read them and create coding-practice problems from the useful concepts, examples, formulas, or diagrams."
        )
    return "\n\n".join(parts)


def _with_attachment_metadata(result: dict[str, Any], attachment_bundle: dict[str, Any]) -> dict[str, Any]:
    warnings = list(attachment_bundle.get("warnings") or []) + list(result.get("warnings") or [])
    return {
        **result,
        "warnings": warnings,
        "attachments": attachment_bundle.get("summary") or [],
    }


def _safe_attachment_name(value: Any) -> str:
    name = str(value or "attachment").strip().replace("\x00", "")
    return name[-180:] or "attachment"


def _normalize_attachment_mime(value: Any, name: str) -> str:
    mime_type = str(value or "").strip().lower()
    if mime_type:
        return mime_type
    lower_name = name.lower()
    if lower_name.endswith(".pdf"):
        return "application/pdf"
    if lower_name.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower_name.endswith(".png"):
        return "image/png"
    if lower_name.endswith(".webp"):
        return "image/webp"
    if lower_name.endswith(".gif"):
        return "image/gif"
    if lower_name.endswith((".md", ".markdown")):
        return "text/markdown"
    if lower_name.endswith(".json"):
        return "application/json"
    if lower_name.endswith(".csv"):
        return "text/csv"
    if lower_name.endswith(".py"):
        return "text/x-python"
    return "application/octet-stream"


def _safe_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _decode_attachment_base64(value: str) -> bytes | None:
    cleaned = value.strip()
    if "," in cleaned and cleaned.lower().startswith("data:"):
        cleaned = cleaned.split(",", 1)[1]
    try:
        return base64.b64decode(cleaned, validate=True)
    except (binascii.Error, ValueError):
        return None


def _is_text_attachment(name: str, mime_type: str) -> bool:
    lower_name = name.lower()
    return (
        any(lower_name.endswith(ext) for ext in TEXT_ATTACHMENT_EXTENSIONS)
        or mime_type in TEXT_ATTACHMENT_MIME_TYPES
        or any(mime_type.startswith(prefix) for prefix in TEXT_ATTACHMENT_MIME_PREFIXES)
    )


def _is_multimodal_attachment(mime_type: str) -> bool:
    return (
        mime_type in MULTIMODAL_ATTACHMENT_MIME_TYPES
        or any(mime_type.startswith(prefix) for prefix in MULTIMODAL_ATTACHMENT_MIME_PREFIXES)
    )


def repair_problem_draft(
    content: str,
    *,
    user_request: str = "",
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    client: JsonGeneratingClient | None = None,
) -> dict[str, Any]:
    current = _validate_problem_content(content)
    if current["ok"]:
        return {
            **_draft_response(current["problems"], current, attempts=[]),
            "used_llm": False,
            "message": "Current JSON is already valid.",
        }

    context = user_request.strip() or "Repair this draft so it becomes a valid Mnemosyne coding-practice problem."
    return _run_problem_agent_loop(
        user_request=context,
        first_messages=_repair_problem_messages(context, content, current["errors"], current["warnings"]),
        count=max(1, current.get("count") or 1),
        provider=provider,
        api_key=api_key,
        model=model,
        max_attempts=max_attempts,
        client=client,
    )


def edit_problem_draft(
    problem: dict[str, Any],
    user_request: str,
    *,
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    client: JsonGeneratingClient | None = None,
) -> dict[str, Any]:
    request_text = user_request.strip()
    if not request_text:
        return _failure("Describe how you want to change this problem.")

    problem_id = str(problem.get("id", "")).strip()
    first_messages = _edit_problem_messages(problem, request_text)
    result = _run_problem_agent_loop(
        user_request=request_text,
        first_messages=first_messages,
        count=1,
        provider=provider,
        api_key=api_key,
        model=model,
        max_attempts=max_attempts,
        client=client,
        required_problem_id=problem_id,
    )
    if result.get("problem") and result["problem"].get("id") != problem_id:
        result["ok"] = False
        result.setdefault("errors", []).append("The edited draft changed the problem id. Keep the original id.")
    return result


def generate_test_drafts(
    problem: dict[str, Any],
    user_request: str,
    *,
    group: str = "hidden_tests",
    count: int = 3,
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    client: JsonGeneratingClient | None = None,
) -> dict[str, Any]:
    request_text = user_request.strip()
    if not request_text:
        return _failure("Describe what kind of tests to add.")
    if group not in {"visible_tests", "hidden_tests"}:
        return _failure("group must be visible_tests or hidden_tests.")

    count = _clamp_int(count, 1, MAX_TEST_COUNT)
    entry_kind = problem.get("entry_kind", "function")
    if entry_kind not in {"function", "unit_tests"}:
        return _failure("Only function and unit_tests problems can receive generated test drafts.")

    schema = _test_draft_schema(entry_kind)
    messages = _test_draft_messages(problem, request_text, group, count)
    attempts: list[dict[str, Any]] = []

    try:
        raw_text = (client or make_llm_client(provider=provider, api_key=api_key)).generate_json(messages, schema, model=model)
    except (LLMNotConfigured, LLMRequestError) as exc:
        return _failure(str(exc), attempts=attempts)

    try:
        data = _loads_llm_json(raw_text)
    except ValueError as exc:
        return _failure(str(exc), attempts=[{"ok": False, "errors": [str(exc)], "raw_text": raw_text[:4000]}])

    tests = data.get("tests") if isinstance(data, dict) else None
    if not isinstance(tests, list) or not tests:
        return _failure("LLM response must contain a non-empty tests array.", attempts=attempts)

    test_cases: list[dict[str, Any]] = []
    errors: list[str] = []
    for idx, draft in enumerate(tests[:count]):
        if not isinstance(draft, dict):
            errors.append(f"tests[{idx}] must be an object.")
            continue
        name = str(draft.get("name") or f"generated_{idx + 1}").strip() or f"generated_{idx + 1}"
        if entry_kind == "function":
            args = draft.get("args")
            if not isinstance(args, list):
                errors.append(f"tests[{idx}].args must be a list.")
                continue
            expected = generate_expected_output(problem, args)
            if not expected.get("ok"):
                errors.append(f"tests[{idx}] could not generate expected output: {expected.get('error')}")
                continue
            test_case = {"name": name, "args": args, "expected": expected.get("expected")}
        else:
            code = draft.get("code")
            if not isinstance(code, str) or not code.strip():
                errors.append(f"tests[{idx}].code must be a non-empty Python test string.")
                continue
            test_case = {"name": name, "code": code}

        candidate = copy.deepcopy(problem)
        candidate_tests = list(candidate.get(group, []))
        candidate_tests.append(test_case)
        candidate[group] = candidate_tests
        validation = validate_problem_spec(candidate)
        if not validation["ok"]:
            errors.extend(f"tests[{idx}]: {error}" for error in validation["errors"])
            continue
        test_cases.append(test_case)

    attempts.append({"ok": not errors, "errors": errors, "raw_text": raw_text[:4000]})
    return {
        "ok": not errors and bool(test_cases),
        "errors": errors,
        "warnings": [],
        "group": group,
        "test_cases": test_cases,
        "raw_text": raw_text,
        "attempts": attempts,
    }


def _run_problem_agent_loop(
    *,
    user_request: str,
    first_messages: list[dict[str, str]],
    count: int,
    provider: str | None,
    api_key: str | None,
    model: str | None,
    max_attempts: int,
    client: JsonGeneratingClient | None,
    required_problem_id: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    try:
        llm_client = client or make_llm_client(provider=provider, api_key=api_key, timeout_seconds=timeout_seconds)
    except (LLMNotConfigured, LLMRequestError) as exc:
        return _failure(str(exc), attempts=[])
    multimodal_attachments = attachments or []
    if multimodal_attachments and not _client_supports_multimodal_attachments(llm_client):
        return _failure(
            "The selected provider does not support PDF/image attachments in this app yet. "
            "Use Gemini for PDF/images, or attach text/markdown files for text-only providers.",
            attempts=[],
        )
    attempts: list[dict[str, Any]] = []
    messages = first_messages
    last_raw = ""
    last_errors: list[str] = []
    last_warnings: list[str] = []
    max_attempts = _clamp_int(max_attempts, 1, 4)

    for attempt_idx in range(max_attempts):
        try:
            raw_text = _client_generate_json(
                llm_client,
                messages,
                _problem_collection_schema(count),
                model=model,
                attachments=multimodal_attachments,
            )
        except (LLMNotConfigured, LLMRequestError) as exc:
            return _failure(str(exc), attempts=attempts)

        validation = _validate_llm_problem_text(raw_text)
        if validation.get("problems") and len(validation["problems"]) != count:
            validation["ok"] = False
            validation.setdefault("errors", []).append(f"LLM returned {len(validation['problems'])} problem(s), expected {count}.")
        if required_problem_id and validation.get("problems"):
            for problem in validation["problems"]:
                if problem.get("id") != required_problem_id:
                    validation["ok"] = False
                    validation.setdefault("errors", []).append(
                        f"Edited problem id must stay `{required_problem_id}`."
                    )

        repair_report = _repair_hint_report(validation["errors"], validation["warnings"]) if not validation["ok"] else {}
        attempt = {
            "ok": validation["ok"],
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "raw_text": raw_text[:4000],
        }
        if repair_report.get("hints"):
            attempt["repair_report"] = repair_report
            attempt["repair_hints"] = repair_report["hints"]
        attempts.append(attempt)
        if validation["ok"]:
            return {
                **_draft_response(validation["problems"], validation, attempts=attempts),
                "used_llm": True,
            }

        last_raw = raw_text
        last_errors = validation["errors"]
        last_warnings = validation["warnings"]
        messages = _repair_problem_messages(user_request, last_raw, last_errors, last_warnings)

    repair_report = _repair_hint_report(last_errors, last_warnings)
    return {
        "ok": False,
        "errors": last_errors or ["LLM draft did not pass validation."],
        "warnings": last_warnings,
        "problem": None,
        "problems": [],
        "content": last_raw,
        "attempts": attempts,
        "repair_report": repair_report,
        "repair_hints": repair_report["hints"],
        "used_llm": True,
    }


def _draft_response(problems: list[dict[str, Any]], validation: dict[str, Any], attempts: list[dict[str, Any]]) -> dict[str, Any]:
    content_value: Any = problems[0] if len(problems) == 1 else problems
    return {
        "ok": validation["ok"],
        "errors": validation["errors"],
        "warnings": validation["warnings"],
        "problem": problems[0] if len(problems) == 1 else None,
        "problems": problems,
        "count": len(problems),
        "content": format_problem_json(content_value),
        "attempts": attempts,
    }


def _validate_problem_content(content: str) -> dict[str, Any]:
    parse_warnings: list[str] = []
    try:
        problems = parse_problem_collection(content, warnings=parse_warnings)
    except ValueError as exc:
        return {
            "ok": False,
            "errors": [str(exc)],
            "warnings": parse_warnings,
            "problems": [],
            "problem": None,
            "count": 0,
        }
    validation = validate_problem_collection(problems)
    validation["warnings"] = parse_warnings + validation["warnings"]
    return validation


def _validate_llm_problem_text(raw_text: str) -> dict[str, Any]:
    parse_warnings: list[str] = []
    try:
        data = _loads_llm_json(raw_text, warnings=parse_warnings)
        if isinstance(data, dict) and isinstance(data.get("problems"), list):
            problems = data["problems"]
            if not problems:
                raise ValueError("LLM response problems array is empty.")
            if not all(isinstance(item, dict) for item in problems):
                raise ValueError("Every item in LLM response problems array must be an object.")
        else:
            problems = parse_problem_collection(raw_text, warnings=parse_warnings)
    except ValueError as exc:
        return {
            "ok": False,
            "errors": [str(exc)],
            "warnings": parse_warnings,
            "problems": [],
            "problem": None,
            "count": 0,
        }

    validation = validate_problem_collection(problems)
    validation["warnings"] = parse_warnings + validation["warnings"]
    return validation


def _loads_llm_json(raw_text: str, warnings: list[str] | None = None) -> Any:
    cleaned = prepare_problem_content(raw_text, warnings=warnings)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON from LLM: {exc.msg} at line {exc.lineno}, column {exc.colno}.") from exc


def _problem_collection_schema(count: int) -> dict[str, Any]:
    count = _clamp_int(count, 1, MAX_BATCH_COUNT)
    problem_schema = copy.deepcopy(AUTHORING_API_SCHEMA["schema"])
    return {
        "name": "mnemosyne_problem_collection",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["problems"],
            "properties": {
                "problems": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": count,
                    "items": problem_schema,
                }
            },
        },
    }


def _test_draft_schema(entry_kind: str) -> dict[str, Any]:
    if entry_kind == "unit_tests":
        item = {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "code"],
            "properties": {
                "name": {"type": "string"},
                "code": {"type": "string"},
            },
        }
    else:
        item = {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "args"],
            "properties": {
                "name": {"type": "string"},
                "args": {
                    "type": "array",
                    "items": _json_value_schema(depth=4),
                },
            },
        }

    return {
        "name": "mnemosyne_test_drafts",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["tests"],
            "properties": {
                "tests": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": MAX_TEST_COUNT,
                    "items": item,
                }
            },
        },
    }



def _json_value_schema(depth: int) -> dict[str, Any]:
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
    child = _json_value_schema(depth - 1)
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


def _create_problem_messages(user_request: str, count: int) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": _system_prompt()},
        {
            "role": "user",
            "content": render_prompt(
                "create_problem_user_message",
                count=count,
                user_request=user_request,
            ),
        },
    ]


def _repair_problem_messages(
    user_request: str,
    draft_text: str,
    errors: list[str],
    warnings: list[str],
) -> list[dict[str, str]]:
    repair_report = _repair_hint_report(errors, warnings)
    return [
        {"role": "system", "content": _system_prompt()},
        {
            "role": "user",
            "content": render_prompt(
                "repair_problem_user_message",
                repair_guidance=_repair_feedback_summary(errors, warnings),
                repair_report_json=json.dumps(repair_report, ensure_ascii=False, indent=2),
                user_request=user_request,
                errors_json=json.dumps(errors, ensure_ascii=False, indent=2),
                warnings_json=json.dumps(warnings, ensure_ascii=False, indent=2),
                draft_text=draft_text,
            ),
        },
    ]


def _repair_feedback_summary(errors: list[str], warnings: list[str]) -> str:
    report = _repair_hint_report(errors, warnings)
    hints = [f"[{hint['code']}] {hint['action']}" for hint in report["hints"]]
    return "Repair guidance:\n" + "\n".join(f"- {hint}" for hint in hints)


def _edit_problem_messages(problem: dict[str, Any], user_request: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": _system_prompt()},
        {
            "role": "user",
            "content": (
                "Modify the existing problem according to the request. Return exactly one problem "
                "inside the {\"problems\": [...]} envelope. Keep the same id unless the request "
                "explicitly says this is a new problem, and even then this API requires the same id.\n\n"
                f"Request:\n{user_request}\n\n"
                f"Existing problem:\n{json.dumps(problem, ensure_ascii=False, indent=2)}"
            ),
        },
    ]


def _test_draft_messages(problem: dict[str, Any], user_request: str, group: str, count: int) -> list[dict[str, str]]:
    entry_kind = problem.get("entry_kind", "function")
    if entry_kind == "unit_tests":
        output_rule = (
            "Return unit test drafts as {\"tests\": [{\"name\": \"...\", \"code\": \"from user_solution import ...\\nassert ...\"}]}."
        )
    else:
        function_name = problem.get("function_name") or problem.get("id") or "solution"
        output_rule = (
            "Return function test drafts as {\"tests\": [{\"name\": \"...\", \"args\": [...]}]}. "
            f"The app will run the reference solution to compute expected outputs. Args must match `{function_name}`."
        )

    public_problem = copy.deepcopy(problem)
    public_problem.pop("hidden_tests", None)
    return [
        {
            "role": "system",
            "content": (
                "You generate focused test-case drafts for a local Python coding-practice app. "
                "Use JSON-native values only. Do not invent expected outputs for function problems. "
                "Within those constraints, choose meaningful edge cases and varied examples that improve the problem. "
                "Thank you for helping create useful tests; do not include this thanks in the returned JSON."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Generate exactly {count} {group} test draft(s).\n"
                f"{output_rule}\n\n"
                f"User request:\n{user_request}\n\n"
                f"Problem:\n{json.dumps(public_problem, ensure_ascii=False, indent=2)}"
            ),
        },
    ]


def _system_prompt() -> str:
    return render_prompt("problem_agent_system")


def _failure(message: str, attempts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "errors": [message],
        "warnings": [],
        "problem": None,
        "problems": [],
        "content": "",
        "attempts": attempts or [],
    }


def _clamp_int(value: int, lower: int, upper: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return lower
    return max(lower, min(upper, parsed))


def _clamp_optional_int(value: int | None, lower: int, upper: int) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return max(lower, min(upper, parsed))
