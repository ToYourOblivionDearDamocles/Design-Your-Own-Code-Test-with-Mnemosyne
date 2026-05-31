from __future__ import annotations

import base64
import binascii
import copy
import json
import os
import re
import urllib.error
import urllib.request
from urllib.parse import quote
from typing import Any, Protocol

from app.judge import generate_expected_output
from app.problem_authoring import (
    AUTHORING_API_SCHEMA,
    format_problem_json,
    parse_problem_collection,
    prepare_problem_content,
    validate_problem_collection,
    validate_problem_spec,
)


DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_MAX_ATTEMPTS = 2
MAX_BATCH_COUNT = 10
MAX_TEST_COUNT = 8
MAX_ATTACHMENT_COUNT = 8
MAX_ATTACHMENT_BYTES = 8 * 1024 * 1024
MAX_TOTAL_TEXT_ATTACHMENT_CHARS = 60_000
PROVIDERS = {"openai", "ollama", "gemini", "deepseek", "openai_compatible"}
GEMINI_MODEL_OPTIONS = [
    "gemini-3.5-flash",
    "gemini-3.1-pro-preview",
    "gemini-3.1-pro-preview-customtools",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-2.5-flash-preview-09-2025",
    "gemini-2.5-flash-lite-preview-09-2025",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]
TEXT_ATTACHMENT_EXTENSIONS = {".md", ".markdown", ".txt", ".json", ".csv", ".tsv", ".py", ".yaml", ".yml"}
TEXT_ATTACHMENT_MIME_PREFIXES = ("text/",)
TEXT_ATTACHMENT_MIME_TYPES = {
    "application/json",
    "application/x-yaml",
    "application/yaml",
}
MULTIMODAL_ATTACHMENT_MIME_TYPES = {"application/pdf"}
MULTIMODAL_ATTACHMENT_MIME_PREFIXES = ("image/",)
PROVIDER_PROFILES: dict[str, dict[str, Any]] = {
    "ollama": {
        "strategy": "schema",
        "supports_json_schema": True,
        "supports_json_mode": False,
        "supports_multimodal_attachments": False,
        "supports_thinking_off": "flash_only",
        "preferred_count": 1,
        "max_recommended_count": 2,
        "notes": "Local model quality varies; sequential generation is strongly recommended.",
    },
    "gemini": {
        "strategy": "json mode + prompt -> prompt fallback",
        "supports_json_schema": False,
        "supports_json_mode": True,
        "supports_multimodal_attachments": True,
        "supports_thinking_off": True,
        "preferred_count": 1,
        "max_recommended_count": 5,
        "notes": "Gemini avoids full JSON schema by default and can receive PDF/image attachments. Thinking can be disabled on Flash/Flash-Lite, but Pro thinking models keep thinking enabled.",
    },
    "deepseek": {
        "strategy": "json_object + prompt -> prompt fallback",
        "supports_json_schema": False,
        "supports_json_mode": True,
        "supports_multimodal_attachments": False,
        "supports_thinking_off": False,
        "preferred_count": 1,
        "max_recommended_count": 5,
        "notes": "DeepSeek uses OpenAI-compatible chat completions; text/markdown attachments are folded into the prompt.",
    },
    "openai": {
        "strategy": "strict json schema",
        "supports_json_schema": True,
        "supports_json_mode": True,
        "supports_multimodal_attachments": False,
        "supports_thinking_off": False,
        "preferred_count": 1,
        "max_recommended_count": 5,
        "notes": "Uses strict structured output through the Responses API; text/markdown attachments are folded into the prompt.",
    },
    "openai_compatible": {
        "strategy": "json schema when endpoint supports it",
        "supports_json_schema": True,
        "supports_json_mode": True,
        "supports_multimodal_attachments": False,
        "supports_thinking_off": False,
        "preferred_count": 1,
        "max_recommended_count": 3,
        "notes": "Compatibility depends on the selected endpoint and model; text/markdown attachments are folded into the prompt.",
    },
}


class LLMNotConfigured(RuntimeError):
    pass


class LLMRequestError(RuntimeError):
    pass


class JsonGeneratingClient(Protocol):
    def generate_json(
        self,
        messages: list[dict[str, str]],
        response_schema: dict[str, Any],
        model: str | None = None,
    ) -> str:
        ...


class OpenAIResponsesClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "").strip()
        self.model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.timeout_seconds = timeout_seconds or int(os.getenv("OPENAI_TIMEOUT_SECONDS", "60"))

    def generate_json(
        self,
        messages: list[dict[str, str]],
        response_schema: dict[str, Any],
        model: str | None = None,
    ) -> str:
        if not self.api_key:
            raise LLMNotConfigured("OPENAI_API_KEY is not set.")

        payload = {
            "model": (model or self.model).strip(),
            "input": messages,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": response_schema["name"],
                    "schema": response_schema["schema"],
                    "strict": True,
                }
            },
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/responses",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LLMRequestError(f"OpenAI API request failed ({exc.code}): {detail[:2000]}") from exc
        except urllib.error.URLError as exc:
            raise LLMRequestError(f"OpenAI API request failed: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise LLMRequestError(f"OpenAI API returned non-JSON response: {exc}") from exc

        text = _extract_response_text(data)
        if not text:
            raise LLMRequestError("OpenAI API response did not contain output text.")
        return text


class OpenAICompatibleClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_COMPATIBLE_API_KEY", "").strip()
        self.model = model or os.getenv("OPENAI_COMPATIBLE_MODEL", "").strip()
        self.base_url = (base_url or os.getenv("OPENAI_COMPATIBLE_BASE_URL", "")).rstrip("/")
        self.timeout_seconds = timeout_seconds or int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))

    def generate_json(
        self,
        messages: list[dict[str, str]],
        response_schema: dict[str, Any],
        model: str | None = None,
    ) -> str:
        selected_model = (model or self.model).strip()
        if not self.base_url:
            raise LLMNotConfigured("OPENAI_COMPATIBLE_BASE_URL is not set.")
        if not selected_model:
            raise LLMNotConfigured("Set OPENAI_COMPATIBLE_MODEL or enter a model name.")

        payload = {
            "model": selected_model,
            "messages": messages,
            "temperature": 0,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_schema["name"],
                    "schema": response_schema["schema"],
                    "strict": True,
                },
            },
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        data = _urlopen_json(request, self.timeout_seconds, "OpenAI-compatible API")
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMRequestError("OpenAI-compatible response did not contain choices[0].message.content.") from exc
        if not isinstance(content, str) or not content.strip():
            raise LLMRequestError("OpenAI-compatible response content was empty.")
        return content


class DeepSeekClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("DEEPSEEK_API_KEY", "").strip()
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash").strip()
        self.base_url = (base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).rstrip("/")
        self.timeout_seconds = timeout_seconds or int(os.getenv("LLM_TIMEOUT_SECONDS", "90"))
        self.max_tokens = int(os.getenv("DEEPSEEK_MAX_TOKENS", "8192"))

    def generate_json(
        self,
        messages: list[dict[str, str]],
        response_schema: dict[str, Any],
        model: str | None = None,
    ) -> str:
        if not self.api_key:
            raise LLMNotConfigured("DEEPSEEK_API_KEY is not set.")
        selected_model = (model or self.model).strip()
        if not selected_model:
            raise LLMNotConfigured("Set DEEPSEEK_MODEL or enter a DeepSeek model name.")

        try:
            return self._request_json(
                messages=messages,
                response_schema=response_schema,
                model=selected_model,
                json_mode=True,
            )
        except LLMRequestError as exc:
            if _is_response_format_error(str(exc)):
                return self._request_json(
                    messages=messages,
                    response_schema=response_schema,
                    model=selected_model,
                    json_mode=False,
                )
            raise

    def _request_json(
        self,
        *,
        messages: list[dict[str, str]],
        response_schema: dict[str, Any],
        model: str,
        json_mode: bool,
    ) -> str:
        prepared_messages = _messages_with_prompt_contract(messages, response_schema)
        payload: dict[str, Any] = {
            "model": model,
            "messages": prepared_messages,
            "temperature": 0,
            "max_tokens": self.max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        data = _urlopen_json(request, self.timeout_seconds, "DeepSeek API")
        try:
            message = data["choices"][0]["message"]
            content = message.get("content", "")
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise LLMRequestError("DeepSeek response did not contain choices[0].message.content.") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMRequestError("DeepSeek response content was empty.")
        return _strip_thinking_text(content)


class OllamaChatClient:
    def __init__(
        self,
        *,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
        think: bool | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "").strip()
        self.timeout_seconds = timeout_seconds or int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
        if think is None:
            think = os.getenv("OLLAMA_THINK", "false").strip().lower() in {"1", "true", "yes", "on"}
        self.think = think

    def generate_json(
        self,
        messages: list[dict[str, str]],
        response_schema: dict[str, Any],
        model: str | None = None,
    ) -> str:
        selected_model = (model or self.model or _first_ollama_model(self.base_url)).strip()
        if not selected_model:
            raise LLMNotConfigured("Set OLLAMA_MODEL or enter an installed Ollama model name.")

        payload = {
            "model": selected_model,
            "messages": messages,
            "stream": False,
            "format": response_schema["schema"],
            "think": self.think,
            "options": {"temperature": 0},
        }
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        data = _urlopen_json(request, self.timeout_seconds, "Ollama")
        try:
            content = data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise LLMRequestError("Ollama response did not contain message.content.") from exc
        if not isinstance(content, str) or not content.strip():
            raise LLMRequestError("Ollama response content was empty.")
        return _strip_thinking_text(content)


class GeminiClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        self.base_url = (base_url or os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")).rstrip("/")
        self.timeout_seconds = timeout_seconds or int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))

    def generate_json(
        self,
        messages: list[dict[str, str]],
        response_schema: dict[str, Any],
        model: str | None = None,
    ) -> str:
        if not self.api_key:
            raise LLMNotConfigured("GEMINI_API_KEY is not set.")
        selected_model = (model or self.model).strip().removeprefix("models/")
        if not selected_model:
            raise LLMNotConfigured("Set GEMINI_MODEL or enter a Gemini model name.")

        system_text = "\n\n".join(msg["content"] for msg in messages if msg.get("role") == "system")
        user_text = "\n\n".join(msg["content"] for msg in messages if msg.get("role") != "system")
        mode = "schema" if os.getenv("GEMINI_USE_SCHEMA", "").strip().lower() in {"1", "true", "yes", "on"} else "json"
        content = self._request_json(
            selected_model=selected_model,
            system_text=system_text,
            user_text=user_text,
            response_schema=response_schema,
            mode=mode,
            attachments=[],
        )
        return _strip_thinking_text(content)

    def generate_json_with_attachments(
        self,
        messages: list[dict[str, str]],
        response_schema: dict[str, Any],
        model: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> str:
        if not self.api_key:
            raise LLMNotConfigured("GEMINI_API_KEY is not set.")
        selected_model = (model or self.model).strip().removeprefix("models/")
        if not selected_model:
            raise LLMNotConfigured("Set GEMINI_MODEL or enter a Gemini model name.")

        system_text = "\n\n".join(msg["content"] for msg in messages if msg.get("role") == "system")
        user_text = "\n\n".join(msg["content"] for msg in messages if msg.get("role") != "system")
        mode = "schema" if os.getenv("GEMINI_USE_SCHEMA", "").strip().lower() in {"1", "true", "yes", "on"} else "json"
        content = self._request_json(
            selected_model=selected_model,
            system_text=system_text,
            user_text=user_text,
            response_schema=response_schema,
            mode=mode,
            attachments=attachments or [],
        )
        return _strip_thinking_text(content)

    def _request_json(
        self,
        *,
        selected_model: str,
        system_text: str,
        user_text: str,
        response_schema: dict[str, Any],
        mode: str,
        attachments: list[dict[str, Any]],
        omit_thinking_config: bool = False,
    ) -> str:
        generation_config: dict[str, Any] = {
            "temperature": 0,
        }
        if mode == "schema":
            generation_config["responseMimeType"] = "application/json"
            generation_config["responseJsonSchema"] = response_schema["schema"]
        elif mode == "json":
            generation_config["responseMimeType"] = "application/json"

        thinking_config = {} if omit_thinking_config else _gemini_thinking_config(selected_model)
        if thinking_config:
            generation_config["thinkingConfig"] = thinking_config

        request_text = user_text
        if mode in {"json", "plain"}:
            request_text = (
                f"{user_text}\n\n"
                f"{_prompt_only_contract(response_schema)}\n\n"
                "Return ONLY valid JSON. Do not wrap it in markdown. Do not include commentary."
            )

        parts: list[dict[str, Any]] = [{"text": request_text}]
        for attachment in attachments:
            parts.append(
                {
                    "inlineData": {
                        "mimeType": attachment["mime_type"],
                        "data": attachment["content_base64"],
                    }
                }
            )

        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": generation_config,
        }
        if system_text:
            payload["systemInstruction"] = {"parts": [{"text": system_text}]}

        model_path = quote(selected_model, safe="")
        request = urllib.request.Request(
            f"{self.base_url}/models/{model_path}:generateContent",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )
        try:
            request_timeout = _gemini_request_timeout(self.timeout_seconds, selected_model, attachments)
            data = _urlopen_json(request, request_timeout, "Gemini API")
        except LLMRequestError as exc:
            if not omit_thinking_config and thinking_config and _is_gemini_thinking_config_error(str(exc)):
                return self._request_json(
                    selected_model=selected_model,
                    system_text=system_text,
                    user_text=user_text,
                    response_schema=response_schema,
                    mode=mode,
                    attachments=attachments,
                    omit_thinking_config=True,
                )
            if mode == "schema" and _is_gemini_structured_output_error(str(exc)):
                return self._request_json(
                    selected_model=selected_model,
                    system_text=system_text,
                    user_text=user_text,
                    response_schema=response_schema,
                    mode="json",
                    attachments=attachments,
                    omit_thinking_config=omit_thinking_config,
                )
            if mode == "json" and _is_gemini_structured_output_error(str(exc)):
                return self._request_json(
                    selected_model=selected_model,
                    system_text=system_text,
                    user_text=user_text,
                    response_schema=response_schema,
                    mode="plain",
                    attachments=attachments,
                    omit_thinking_config=omit_thinking_config,
                )
            raise

        try:
            parts = data["candidates"][0]["content"]["parts"]
            content = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMRequestError("Gemini response did not contain candidates[0].content.parts text.") from exc
        if not content.strip():
            raise LLMRequestError("Gemini response content was empty.")
        return content


def llm_status() -> dict[str, Any]:
    selected = default_provider()
    providers = [
        _provider_status("ollama"),
        _provider_status("gemini"),
        _provider_status("deepseek"),
        _provider_status("openai"),
        _provider_status("openai_compatible"),
    ]
    current = next((provider for provider in providers if provider["id"] == selected), providers[0])
    return {
        "configured": bool(current["configured"]),
        "provider": selected,
        "default_provider": selected,
        "providers": providers,
        "api_key_env": current.get("api_key_env", ""),
        "model_env": current.get("model_env", ""),
        "default_model": current.get("default_model", ""),
        "base_url": current.get("base_url", ""),
        "profile": current.get("profile", {}),
        "message": (
            current["message"]
            if current.get("configured")
            else "Choose a configured provider, paste a browser-session API key, or start Ollama with an installed model."
        ),
    }


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


def _client_generate_json(
    client: JsonGeneratingClient,
    messages: list[dict[str, str]],
    response_schema: dict[str, Any],
    *,
    model: str | None,
    attachments: list[dict[str, Any]],
) -> str:
    if attachments:
        generate_with_attachments = getattr(client, "generate_json_with_attachments", None)
        if not callable(generate_with_attachments):
            raise LLMRequestError(
                "The selected provider does not support PDF/image attachments in this app yet. "
                "Use Gemini for PDF/images, or attach text/markdown files for text-only providers."
            )
        return generate_with_attachments(messages, response_schema, model=model, attachments=attachments)
    return client.generate_json(messages, response_schema, model=model)


def _client_supports_multimodal_attachments(client: JsonGeneratingClient) -> bool:
    return callable(getattr(client, "generate_json_with_attachments", None))


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


def _prompt_only_contract(response_schema: dict[str, Any]) -> str:
    name = str(response_schema.get("name") or "")
    if name in {"mnemosyne_problem_collection", "local_leetcode_problem_collection"}:
        return (
            "Required JSON contract:\n"
            "{\"problems\":[problem_object,...]}\n\n"
            "Each function problem_object must include: id, title, difficulty, entry_kind, function_name, tags, "
            "requirements, constraints, checker, timeout_seconds, statement, starter_code, reference_solution, "
            "solution_explanation, complexity, visible_tests, hidden_tests.\n"
            "Optional fields arg_types and return_type declare the runtime interface. Use them when the user-facing function should receive numpy.ndarray, torch.Tensor, pandas.DataFrame, pandas.Series, SimpleNamespace-style objects, or other non-JSON objects.\n"
            "For function tests, every item must be exactly like: "
            "{\"name\":\"basic\",\"args\":[positional_arg_1],\"expected\":expected_return_value}. "
            "For def f(nums), use {\"args\":[[1,2,3]],\"expected\":6}. "
            "For def f(a,b), use {\"args\":[1,2],\"expected\":3}. "
            "Never output empty test objects. Never use input/output/result fields.\n"
            "Keep test arrays compact in JSON, such as {\"name\":\"negative\",\"args\":[[-2,4]],\"expected\":20}, not stair-step expanded lists.\n"
            "For math-heavy problems, prefer display math using $$...$$ for important standalone equations, losses, matrix formulas, probabilities, or optimization objectives.\n"
            "Short inline equations are valid, such as $A = LU$, $i = j$, or $\\lambda_i > 0$. Use display math for long or multi-line formulas.\n"
            "Every function problem statement must include an Input / Output section naming each parameter and return data structure.\n"
            "For function problems, starter_code must type-annotate every parameter and include a return type annotation, such as def solve(nums: list[int]) -> int.\n"
            "For NumPy/PyTorch/pandas/object-interface problems, do not force the function interface to be list-only. If starter_code expects np.ndarray/torch.Tensor/pd.DataFrame or an object-like config, set arg_types and return_type so the judge converts JSON test values before calling the function. If arg_types is omitted, reference_solution must convert lists itself.\n"
            "If a function returns a simple object/dataclass/namedtuple, set return_type to \"object\" and write expected as a JSON object matching the public fields.\n"
            "Within this strict JSON contract, use creative freedom: choose a useful learning goal, original context, meaningful constraints, and edge cases.\n"
            "If the user request is broad, make a thoughtful concrete problem instead of a generic toy task. Thank you for helping create useful practice problems; do not include this thanks in the JSON.\n"
            "Use {\"checker\":{\"type\":\"unordered_nested\"}} for grouped unordered nested-list outputs, such as group_anagrams.\n"
            "For unit_tests problems, tests must be {\"name\":\"basic\",\"code\":\"from user_solution import ...\\nassert ...\"}.\n\n"
            f"{_problem_few_shot_examples()}"
        )
    if name in {"mnemosyne_test_drafts", "local_leetcode_test_drafts"}:
        return (
            "Required JSON contract:\n"
            "{\"tests\":[{\"name\":\"basic\",\"args\":[positional_arg_1]}]}\n"
            "For function tests, do not include expected outputs; the app computes them. "
            "Keep args compact, such as {\"name\":\"negative\",\"args\":[[-2,4]]}. "
            "For unit-test drafts, use {\"tests\":[{\"name\":\"basic\",\"code\":\"from user_solution import ...\\nassert ...\"}]}."
        )
    if name in {"mnemosyne_source_digest", "local_leetcode_source_digest"}:
        return (
            "Required JSON contract:\n"
            "{\"summary\":\"short source summary\",\"key_concepts\":[\"concept\"],"
            "\"problem_briefs\":[{\"id_hint\":\"snake_case_hint\",\"title\":\"Problem title\","
            "\"learning_goal\":\"what this problem teaches\",\"interface\":\"suggested Python function interface\","
            "\"packages\":[\"numpy\"],\"edge_cases\":[\"edge case\"],\"source_notes\":\"short source reference\"}]}\n"
            "Return a compact digest only. Do not create full problem JSON in this step."
        )
    return "Return JSON matching the requested object shape."


def _messages_with_prompt_contract(
    messages: list[dict[str, str]],
    response_schema: dict[str, Any],
) -> list[dict[str, str]]:
    contract = _prompt_only_contract(response_schema)
    prepared = [dict(message) for message in messages]
    contract_text = (
        f"\n\n{contract}\n\n"
        "Return ONLY valid JSON. Do not wrap it in markdown. Do not include commentary."
    )
    for message in reversed(prepared):
        if message.get("role") == "user":
            message["content"] = f"{message.get('content', '')}{contract_text}"
            return prepared
    prepared.append({"role": "user", "content": contract_text.strip()})
    return prepared


def _problem_few_shot_examples() -> str:
    return (
        "Few-shot examples of valid test formatting:\n"
        "1. Single list argument function:\n"
        "{\"id\":\"sum_values\",\"title\":\"Sum Values\",\"difficulty\":\"easy\",\"entry_kind\":\"function\","
        "\"function_name\":\"sum_values\",\"tags\":[\"python\",\"array\"],\"requirements\":[],"
        "\"constraints\":[\"Return 0 for an empty list.\"],\"checker\":{\"type\":\"exact\"},"
        "\"timeout_seconds\":3,\"statement\":\"Return the sum of `nums`.\\n\\n## Input / Output\\n\\n- `nums`: `list[int]`.\\n- Return: `int`, the sum of all values.\","
        "\"starter_code\":\"def sum_values(nums: list[int]) -> int:\\n    pass\\n\","
        "\"reference_solution\":\"def sum_values(nums):\\n    return sum(nums)\\n\","
        "\"solution_explanation\":\"Use Python's sum over the input list.\","
        "\"complexity\":{\"time\":\"O(n)\",\"space\":\"O(1)\"},"
        "\"visible_tests\":[{\"name\":\"basic\",\"args\":[[1,2,3]],\"expected\":6}],"
        "\"hidden_tests\":[{\"name\":\"empty\",\"args\":[[]],\"expected\":0}]}\n"
        "2. Multi-argument function:\n"
        "{\"id\":\"clamp_value\",\"title\":\"Clamp Value\",\"difficulty\":\"easy\",\"entry_kind\":\"function\","
        "\"function_name\":\"clamp_value\",\"tags\":[\"python\",\"math\"],\"requirements\":[],"
        "\"constraints\":[],\"checker\":{\"type\":\"exact\"},\"timeout_seconds\":3,"
        "\"statement\":\"Clamp `x` into the inclusive range [`lo`, `hi`].\\n\\n## Input / Output\\n\\n- `x`: `int`.\\n- `lo`: `int`.\\n- `hi`: `int`.\\n- Return: `int`.\","
        "\"starter_code\":\"def clamp_value(x: int, lo: int, hi: int) -> int:\\n    pass\\n\","
        "\"reference_solution\":\"def clamp_value(x, lo, hi):\\n    return max(lo, min(x, hi))\\n\","
        "\"solution_explanation\":\"Apply min then max.\","
        "\"complexity\":{\"time\":\"O(1)\",\"space\":\"O(1)\"},"
        "\"visible_tests\":[{\"name\":\"inside\",\"args\":[5,1,10],\"expected\":5}],"
        "\"hidden_tests\":[{\"name\":\"below\",\"args\":[-2,0,3],\"expected\":0}]}\n"
        "3. NumPy/allclose problem:\n"
        "{\"id\":\"scale_vector\",\"title\":\"Scale Vector\",\"difficulty\":\"easy\",\"entry_kind\":\"function\","
        "\"function_name\":\"scale_vector\",\"tags\":[\"python\",\"numpy\"],"
        "\"requirements\":[{\"package\":\"numpy\",\"pip\":\"numpy>=2.0\",\"import_name\":\"numpy\"}],"
        "\"constraints\":[\"Return a NumPy-compatible numeric vector.\"],"
        "\"checker\":{\"type\":\"allclose\",\"atol\":1e-5,\"rtol\":1e-5},\"timeout_seconds\":3,"
        "\"arg_types\":[\"numpy.ndarray\",\"float\"],\"return_type\":\"numpy.ndarray\","
        "\"statement\":\"Return vector `x` multiplied by scalar `a`.\\n\\n## Input / Output\\n\\n- `x`: `numpy.ndarray`, a one-dimensional numeric array.\\n- `a`: `float`.\\n- Return: `numpy.ndarray`, the scaled vector.\\n\\nThe operation is\\n\\n$$\\ny_i = a x_i\\n$$\","
        "\"starter_code\":\"import numpy as np\\n\\ndef scale_vector(x: np.ndarray, a: float) -> np.ndarray:\\n    pass\\n\","
        "\"reference_solution\":\"import numpy as np\\n\\ndef scale_vector(x, a):\\n    return x * a\\n\","
        "\"solution_explanation\":\"Convert to an array and multiply.\","
        "\"complexity\":{\"time\":\"O(n)\",\"space\":\"O(n)\"},"
        "\"visible_tests\":[{\"name\":\"basic\",\"args\":[[1,2,3],2],\"expected\":[2.0,4.0,6.0]}],"
        "\"hidden_tests\":[{\"name\":\"negative\",\"args\":[[-1,4],0.5],\"expected\":[-0.5,2.0]}]}\n"
        "4. OOP/unit_tests problem:\n"
        "{\"id\":\"counter_class\",\"title\":\"Counter Class\",\"difficulty\":\"easy\",\"entry_kind\":\"unit_tests\","
        "\"tags\":[\"python\",\"oop\"],\"requirements\":[],\"constraints\":[],"
        "\"checker\":{\"type\":\"exact\"},\"timeout_seconds\":3,"
        "\"statement\":\"Implement a `Counter` class with `increment` and `get_value`.\","
        "\"starter_code\":\"class Counter:\\n    pass\\n\","
        "\"reference_solution\":\"class Counter:\\n    def __init__(self):\\n        self.value = 0\\n    def increment(self):\\n        self.value += 1\\n    def get_value(self):\\n        return self.value\\n\","
        "\"solution_explanation\":\"Store instance state on `self`.\","
        "\"complexity\":{\"time\":\"O(1)\",\"space\":\"O(1)\"},"
        "\"visible_tests\":[{\"name\":\"increment\",\"code\":\"from user_solution import Counter\\nc = Counter()\\nc.increment()\\nassert c.get_value() == 1\"}],"
        "\"hidden_tests\":[{\"name\":\"independent instances\",\"code\":\"from user_solution import Counter\\na = Counter(); b = Counter()\\na.increment()\\nassert a.get_value() == 1\\nassert b.get_value() == 0\"}]}"
    )


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
            "content": (
                f"Create exactly {count} Python coding-practice problem(s).\n\n"
                "Within the required schema, you may be creative about the learning objective, scenario, examples, and edge cases. "
                "Aim for problems that feel useful and polished, not generic schema filler. Thank you for helping create good practice material; do not include this thanks in the JSON.\n\n"
                "Return JSON matching this envelope exactly:\n"
                "{\"problems\": [problem_object, ...]}\n\n"
                f"User request:\n{user_request}"
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
            "content": (
                "Repair this draft so it passes the deterministic verifier. Return only the "
                "{\"problems\": [...]} JSON envelope.\n\n"
                "Critical repair rules:\n"
                "- Every function visible_tests/hidden_tests item must include name, args, and expected.\n"
                "- Empty test objects like {} are invalid.\n"
                "- For def f(nums), use {\"name\":\"basic\",\"args\":[[1,2,3]],\"expected\":6}.\n"
                "- For def f(a, b), use {\"name\":\"basic\",\"args\":[1,2],\"expected\":3}.\n"
                "- Keep short test objects on one line and do not stair-step nested test arrays.\n"
                "- Ensure each function statement has an Input / Output section with parameter and return data structures.\n"
                "- If equations appear, prefer display math $$...$$ for long standalone formulas. Short inline equations such as $A = LU$ or $i = j$ are valid.\n"
                "- For NumPy/PyTorch/pandas/object interfaces, prefer declaring arg_types/return_type so the judge converts JSON test values into runtime objects before calling the function. If arg_types is absent, convert inside reference_solution before using .shape, .T, @, tensor methods, or DataFrame methods.\n"
                "- Preserve the draft's good creative content unless a verifier error requires changing it.\n"
                "- Use checker unordered_nested for grouped unordered nested-list outputs, such as group_anagrams.\n"
                "- If a draft has empty tests, replace them with concrete tests derived from reference_solution.\n\n"
                f"{_repair_feedback_summary(errors, warnings)}\n\n"
                "Verifier repair report JSON, for your next edit only. Do not include this report "
                "as a field in the returned problem JSON:\n"
                f"{json.dumps(repair_report, ensure_ascii=False, indent=2)}\n\n"
                f"Original user request:\n{user_request}\n\n"
                f"Verifier errors:\n{json.dumps(errors, ensure_ascii=False, indent=2)}\n\n"
                f"Verifier warnings:\n{json.dumps(warnings, ensure_ascii=False, indent=2)}\n\n"
                f"Draft JSON/text:\n{draft_text}"
            ),
        },
    ]


def _repair_feedback_summary(errors: list[str], warnings: list[str]) -> str:
    report = _repair_hint_report(errors, warnings)
    hints = [f"[{hint['code']}] {hint['action']}" for hint in report["hints"]]
    return "Repair guidance:\n" + "\n".join(f"- {hint}" for hint in hints)


def build_repair_hint_report(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return _repair_hint_report(errors, warnings)


def _repair_hint_report(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    messages = [str(item) for item in (errors + warnings) if str(item).strip()]
    text = "\n".join(messages).lower()
    hints: list[dict[str, Any]] = []

    def add_hint(
        *,
        code: str,
        problem: str,
        action: str,
        example: Any | None = None,
        evidence_patterns: list[str] | None = None,
        severity: str = "error",
        extra: dict[str, Any] | None = None,
    ) -> None:
        if any(hint["code"] == code for hint in hints):
            return
        hint: dict[str, Any] = {
            "code": code,
            "severity": severity,
            "problem": problem,
            "action": action,
        }
        if example is not None:
            hint["example"] = example
        if extra:
            hint.update(extra)
        evidence = _repair_hint_evidence(messages, evidence_patterns or [code])
        if evidence:
            hint["evidence"] = evidence
        hints.append(hint)

    if "invalid json" in text or "jsondecode" in text or "expecting property name enclosed in double quotes" in text:
        add_hint(
            code="invalid_json",
            problem="The model did not return parseable JSON.",
            action="Return only strict JSON: double quotes, no markdown fences, no comments, no trailing commas, no smart quotes.",
            example={"problems": [{"id": "snake_case_id", "visible_tests": [{"name": "basic", "args": [[1, 2]], "expected": 3}]}]},
            evidence_patterns=["invalid json", "expecting property name", "jsondecode"],
        )

    if "timed out" in text or "timeout" in text:
        add_hint(
            code="llm_timeout",
            problem="The model request timed out before returning a draft.",
            action=(
                "Increase the API timeout, reduce the requested problem count, use a faster model, "
                "or split large PDF/image attachments into smaller source materials. For PDF/image inputs, "
                "generate one or two problems first, then expand from the validated drafts."
            ),
            example={"timeout_seconds": 180, "count": 1, "model": "gemini-2.5-flash"},
            evidence_patterns=["timed out", "timeout"],
        )

    if (
        ".args must be a list" in text
        or ".args must be a list of positional arguments" in text
        or ".expected is required" in text
        or "empty test" in text
        or "empty tests" in text
        or "must contain at least one" in text
    ):
        add_hint(
            code="function_test_shape",
            problem="One or more function tests are missing the required test shape.",
            action=(
                "Rewrite every function visible_tests/hidden_tests item with exactly name, args, and expected. "
                "Do not use input/output/result fields and do not leave {} placeholders."
            ),
            example={"name": "basic", "args": [[1, 2, 3]], "expected": 6},
            evidence_patterns=[".args must be a list", ".expected is required", "empty test", "must contain at least one"],
        )

    if ("args has" in text and "expects 1 positional" in text) or "single-argument function receiving a list" in text:
        add_hint(
            code="single_argument_wrapping",
            problem="A single list/dict/string input was expanded as multiple positional arguments.",
            action="For def f(nums), wrap the whole input as one positional argument: args must be [[...]], not [...].",
            example={"name": "single_list", "args": [[1, 2, 3]], "expected": 6},
            evidence_patterns=["args has", "expects 1 positional", "single-argument"],
        )

    if "reference_solution output mismatch" in text:
        suggested_edits = _reference_mismatch_suggestions(messages)
        add_hint(
            code="expected_mismatch",
            problem="The reference_solution does not produce the declared expected output for at least one test.",
            action=(
                "Replace each failing test.expected with actual_from_reference when the reference solution is correct. "
                "If multiple valid orders are possible, use a checker that matches the semantics."
            ),
            example={"name": "basic", "args": [2], "expected": "actual_from_reference"},
            evidence_patterns=["reference_solution output mismatch", "expected", "actual"],
            extra={"suggested_edits": suggested_edits} if suggested_edits else None,
        )

    if (
        "reference_solution raises an error" in text
        and ("list' object has no attribute 'shape" in text or "list object has no attribute shape" in text)
    ):
        add_hint(
            code="json_list_array_conversion",
            problem="The function interface expects array/tensor behavior but the draft did not declare runtime conversion.",
            action=(
                "Prefer adding arg_types/return_type such as arg_types [\"numpy.ndarray\"] and return_type \"numpy.ndarray\" "
                "so the judge converts JSON test values before calling the function. Otherwise, convert every array-like input inside reference_solution before using .shape, .T, @, tensor methods, or DataFrame methods."
            ),
            example={
                "arg_types": ["numpy.ndarray"],
                "return_type": "numpy.ndarray",
                "starter_code": "import numpy as np\n\ndef cholesky_decomposition(A: np.ndarray) -> np.ndarray:\n    pass\n",
                "reference_solution": "import numpy as np\n\ndef cholesky_decomposition(A):\n    n = A.shape[0]\n    ...\n",
                "tests": {"args": [[[4.0, 2.0], [2.0, 3.0]]], "expected": "JSON-native nested list"},
            },
            evidence_patterns=["reference_solution raises an error", "object has no attribute 'shape", "object has no attribute shape"],
        )

    if "statement has long inline math" in text or "statement has inline math" in text or "use display math" in text and "inline math" in text:
        add_hint(
            code="display_math_preferred",
            problem="The Markdown statement uses long inline math that may be hard to read.",
            action=(
                "Move long equations, matrix formulas, losses, recurrences, and long expressions containing \\sum, \\frac, \\sqrt, or \\int "
                "into display math blocks using $$...$$. Short inline equations like $A = LU$ or $i = j$ are valid."
            ),
            example={"statement": "The update is\n\n$$\nL L^T = A\n$$\n\nwhere $A$ is positive definite."},
            evidence_patterns=["statement has long inline math", "statement has inline math", "use display math", "inline math"],
            severity="warning" if not errors else "error",
        )

    if "anagram" in text or "grouped unordered" in text or "unordered_nested" in text:
        add_hint(
            code="unordered_nested_checker",
            problem="The output is a nested collection where group order or item order should not matter.",
            action="Set checker to {\"type\":\"unordered_nested\"} and keep expected values as nested JSON arrays.",
            example={"checker": {"type": "unordered_nested"}},
            evidence_patterns=["anagram", "grouped unordered", "unordered_nested"],
        )

    if "allclose" in text or "float" in text or "numpy" in text or "tensor" in text:
        add_hint(
            code="numeric_tolerance_checker",
            problem="The problem may return floats, NumPy arrays, or tensors where exact equality is brittle.",
            action="Use checker {\"type\":\"allclose\",\"atol\":1e-5,\"rtol\":1e-5} for approximate numeric outputs.",
            example={"checker": {"type": "allclose", "atol": 1e-5, "rtol": 1e-5}},
            evidence_patterns=["allclose", "float", "numpy", "tensor"],
            severity="warning" if not errors else "error",
        )

    if "requirements[" in text or "looks like a problem instruction" in text or ("requirements" in text and "constraints" in text):
        add_hint(
            code="requirements_vs_constraints",
            problem="requirements contains problem instructions instead of package dependencies.",
            action=(
                "Move instructions such as algorithm rules into constraints. "
                "Keep requirements only for packages with package, pip, and import_name."
            ),
            example={
                "requirements": [{"package": "numpy", "pip": "numpy>=2.0", "import_name": "numpy"}],
                "constraints": ["Use batch gradient descent."],
            },
            evidence_patterns=["requirements[", "looks like a problem instruction", "constraints"],
        )

    if "must define function" in text or "function_name" in text and "define" in text:
        add_hint(
            code="function_name_mismatch",
            problem="The declared function_name does not match starter_code or reference_solution.",
            action="Make function_name, starter_code def name, and reference_solution def name exactly the same.",
            example={
                "function_name": "solve",
                "starter_code": "def solve(nums: list[int]) -> int:\n    pass\n",
                "reference_solution": "def solve(nums):\n    return sum(nums)\n",
            },
            evidence_patterns=["must define function", "function_name", "starter_code", "reference_solution"],
        )

    if "must type-annotate parameter" in text or "must include a return type annotation" in text:
        add_hint(
            code="starter_signature_types",
            problem="The starter_code function signature does not fully describe the input/output types.",
            action=(
                "Add Python type hints to every starter_code parameter and add a return type annotation. "
                "Use clear interface types such as list[int], np.ndarray, torch.Tensor, pd.DataFrame, int, float, str, dict[str,int], tuple[int,int], or object. For non-JSON runtime objects, add arg_types/return_type."
            ),
            example={
                "starter_code": "def solve(nums: list[int], target: int) -> list[int]:\n    pass\n",
            },
            evidence_patterns=["must type-annotate parameter", "must include a return type annotation"],
        )

    if "no module named" in text or "missing dependencies" in text or "name 'np' is not defined" in text or "import_name" in text:
        add_hint(
            code="dependency_or_import_missing",
            problem="A required package or import is missing from the problem definition/code.",
            action=(
                "Add a package object to requirements and include the matching import in starter_code and reference_solution. "
                "Use JSON-serializable test values; set arg_types/return_type or convert to arrays/tensors inside the code."
            ),
            example={
                "requirements": [{"package": "numpy", "pip": "numpy>=2.0", "import_name": "numpy"}],
                "starter_code": "import numpy as np\n\ndef solve(x: list[float]) -> list[float]:\n    pass\n",
            },
            evidence_patterns=["no module named", "missing dependencies", "np is not defined", "import_name"],
        )

    if "problem(s), expected" in text or "returned" in text and "expected" in text and "problem" in text:
        add_hint(
            code="wrong_problem_count",
            problem="The model returned the wrong number of problems.",
            action="Return exactly the requested number of problem objects inside {\"problems\": [...]}.",
            example={"problems": ["exactly_one_problem_object_when_count_is_1"]},
            evidence_patterns=["problem(s), expected", "returned", "expected"],
        )

    if "edited problem id must stay" in text or "changed the problem id" in text:
        add_hint(
            code="problem_id_changed",
            problem="The edit changed the existing problem id.",
            action="Keep the original id when editing an existing problem; only modify requested fields.",
            evidence_patterns=["edited problem id", "changed the problem id"],
        )

    if "already exists" in text or "duplicate problem id" in text:
        add_hint(
            code="duplicate_problem_id",
            problem="The problem id conflicts with another problem.",
            action="Choose a unique snake_case id, or enable overwrite if you intentionally want to replace the existing problem.",
            evidence_patterns=["already exists", "duplicate problem id"],
        )

    if not hints:
        add_hint(
            code="generic_verifier_fix",
            problem="The draft failed deterministic validation.",
            action="Fix the listed verifier errors directly, preserve valid normalized fields, and return only the JSON envelope.",
            evidence_patterns=[],
        )

    return {
        "schema_version": 1,
        "summary": "Use these hints as the checklist for the next draft. Return only the repaired problem JSON.",
        "raw_error_count": len(errors),
        "raw_warning_count": len(warnings),
        "hints": hints,
    }


def _repair_hint_evidence(messages: list[str], patterns: list[str], limit: int = 3) -> list[str]:
    if not patterns:
        return messages[:limit]
    lowered_patterns = [pattern.lower() for pattern in patterns]
    evidence: list[str] = []
    for message in messages:
        lower_message = message.lower()
        if any(pattern in lower_message for pattern in lowered_patterns):
            evidence.append(message)
        if len(evidence) >= limit:
            break
    return evidence


def _reference_mismatch_suggestions(messages: list[str], limit: int = 8) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    marker = "reference_solution output mismatch on "
    for message in messages:
        if marker not in message:
            continue
        tail = message.split(marker, 1)[1]
        label, found, rest = tail.partition(": expected ")
        if not found:
            continue
        expected_text, found, actual_text = rest.rpartition(", actual ")
        if not found:
            continue
        actual_text = actual_text.rstrip(".")
        suggestion = {
            "test": label.strip(),
            "current_expected": _parse_hint_json_value(expected_text.strip()),
            "actual_from_reference": _parse_hint_json_value(actual_text.strip()),
            "action": "Set this test's expected field to actual_from_reference, unless the reference_solution is wrong.",
        }
        suggestions.append(suggestion)
        if len(suggestions) >= limit:
            break
    return suggestions


def _parse_hint_json_value(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


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
    return (
        "You are a careful problem-authoring agent for Mnemosyne, a local Python coding-practice app. "
        "The judge and verifier are deterministic, so every draft must be internally consistent.\n\n"
        "Content style:\n"
        "- Within the required JSON/schema constraints, use creative freedom to design useful, original, well-scoped practice problems.\n"
        "- If the user's request is vague, choose a concrete learning objective, realistic context, and meaningful edge cases.\n"
        "- Prefer problems that teach a Python, AI engineering, data, math, or systems concept over generic toy tasks.\n"
        "- Thank you for helping create thoughtful practice material. Never include this thanks in the returned JSON.\n\n"
        "Rules:\n"
        "- Use Python only.\n"
        "- Prefer entry_kind \"function\" unless the request clearly asks for a class or stateful OOP problem.\n"
        "- requirements is only for package dependencies, e.g. {\"package\":\"numpy\",\"pip\":\"numpy>=2.0\",\"import_name\":\"numpy\"}.\n"
        "- Put problem rules in constraints, not requirements.\n"
        "- If a package is required, include its import in starter_code and reference_solution.\n"
        "- Use checker exact for exact values and allclose for floats, arrays, tensors, or approximate numeric outputs.\n"
        "- Use checker unordered_nested for grouped outputs where group order and item order do not matter, such as group_anagrams.\n"
        "- starter_code and reference_solution must define the declared function_name for function problems.\n"
        "- Function tests use args as positional arguments and expected as the expected return value.\n"
        "- Never use input/output/inputs/result in function tests. Those keys are invalid.\n"
        "- For def f(a, b), a valid function test is {\"name\":\"basic\",\"args\":[value_for_a,value_for_b],\"expected\":answer}.\n"
        "- For def f(nums), a list input must still be wrapped as one positional argument: {\"args\":[[1,2,3]],\"expected\":6}.\n"
        "- Every function statement must include an Input / Output section that names each parameter and return runtime data structure.\n"
        "- For function problems, starter_code must type-annotate every parameter and include a return type annotation.\n"
        "- For NumPy/PyTorch/pandas/object interfaces, use arg_types and return_type to declare runtime conversion, e.g. arg_types [\"numpy.ndarray\"] with def solve(A: np.ndarray) -> np.ndarray.\n"
        "- Keep short JSON test objects on one line and keep nested args/expected arrays compact.\n"
        "- Keep all test args and expected values JSON-serializable. The judge will convert args according to arg_types and normalize outputs for comparison.\n"
        "- If the function returns a simple object/dataclass/namedtuple, use return_type \"object\" and make expected a JSON object containing the public fields.\n"
        "- If arg_types is omitted for NumPy/PyTorch/pandas problems, reference_solution must convert JSON list inputs before using .shape, .T, @, tensor methods, or DataFrame methods.\n"
        "- Include at least one visible test and at least one hidden test.\n"
        "- The reference_solution must pass every visible and hidden test.\n"
        "- Problem statements are Markdown. Prefer display math $$...$$ for important standalone equations in math, ML, optimization, probability, linear algebra, calculus, or statistics problems.\n"
        "- Short inline equations like $A = LU$, $i = j$, or $\\lambda_i > 0$ are valid. Use display math for long or multi-line formulas.\n"
        "- Do not reveal hidden tests in the statement.\n"
    )


def _extract_response_text(data: dict[str, Any]) -> str:
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    texts: list[str] = []
    for item in data.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str):
                texts.append(text)

    if texts:
        return "\n".join(texts)

    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str):
            return content

    return ""


def _gemini_thinking_config(model_name: str) -> dict[str, Any]:
    model = model_name.lower().strip().removeprefix("models/")
    explicitly_configured = any(
        os.getenv(name, "").strip()
        for name in ("GEMINI_THINKING", "GEMINI_THINKING_LEVEL", "GEMINI_THINKING_BUDGET")
    )
    if not explicitly_configured and not (model.startswith("gemini-2.5") or model.startswith("gemini-3")):
        return {}

    thinking_flag = os.getenv("GEMINI_THINKING", "").strip().lower()
    if model.startswith("gemini-3"):
        if thinking_flag in {"1", "true", "yes", "on"}:
            return {"thinkingLevel": "high"}
        if thinking_flag in {"0", "false", "no", "off"}:
            return {} if _gemini_3_pro_model(model) else {"thinkingLevel": "minimal"}

        thinking_level = os.getenv("GEMINI_THINKING_LEVEL", "").strip()
        if thinking_level:
            if thinking_level.lower() == "minimal" and _gemini_3_pro_model(model):
                return {"thinkingLevel": "low"}
            return {"thinkingLevel": thinking_level}

        return {} if _gemini_3_pro_model(model) else {"thinkingLevel": "minimal"}

    if thinking_flag in {"1", "true", "yes", "on"}:
        return {"thinkingBudget": -1}
    if thinking_flag in {"0", "false", "no", "off"}:
        return {"thinkingBudget": 0} if _gemini_can_disable_thinking(model) else {}

    raw_budget = os.getenv("GEMINI_THINKING_BUDGET", "").strip()
    if not raw_budget:
        return {"thinkingBudget": 0} if _gemini_can_disable_thinking(model) else {}

    try:
        budget = int(raw_budget)
    except ValueError:
        return {}
    if budget == 0 and not _gemini_can_disable_thinking(model):
        return {}
    if _gemini_requires_thinking(model) and 0 < budget < 128:
        budget = 128
    return {"thinkingBudget": budget}


def _gemini_requires_thinking(model_name: str) -> bool:
    model = model_name.lower().strip().removeprefix("models/")
    return model.startswith("gemini-2.5-pro")


def _gemini_3_pro_model(model_name: str) -> bool:
    model = model_name.lower().strip().removeprefix("models/")
    return model.startswith("gemini-3") and "-pro" in model


def _gemini_can_disable_thinking(model_name: str) -> bool:
    model = model_name.lower().strip().removeprefix("models/")
    if _gemini_requires_thinking(model):
        return False
    return model.startswith("gemini-2.5") and ("flash" in model or "robotics" in model)


def _is_gemini_thinking_config_error(message: str) -> bool:
    text = message.lower()
    return (
        "thinkingbudget" in text
        or "thinking budget" in text
        or "thinking_config" in text
        or "thinkingconfig" in text
        or "only works in thinking mode" in text
        or "budget 0 is invalid" in text
    )


def _gemini_request_timeout(base_timeout: int, model_name: str, attachments: list[dict[str, Any]]) -> int:
    timeout = int(base_timeout)
    if attachments:
        timeout = max(timeout, 180)
    model = model_name.lower().strip().removeprefix("models/")
    if attachments and ("pro" in model or model.startswith("gemini-3")):
        timeout = max(timeout, 240)
    return timeout


def _is_gemini_structured_output_error(message: str) -> bool:
    text = message.lower()
    return (
        "generation_config.response_format" in text
        or "response_format.text.mime_type" in text
        or "too many states" in text
        or "specified schema produces a constraint" in text
        or "responsemimetype" in text
        or "responsejsonschema" in text
        or "response_mime_type" in text
        or "response_json_schema" in text
    )


def _is_response_format_error(message: str) -> bool:
    text = message.lower()
    return (
        "response_format" in text
        or "json_object" in text
        or "json schema" in text
        or "json_schema" in text
        or "structured output" in text
    )


def make_llm_client(
    provider: str | None = None,
    api_key: str | None = None,
    timeout_seconds: int | None = None,
) -> JsonGeneratingClient:
    normalized = normalize_provider(provider)
    if normalized == "ollama":
        return OllamaChatClient(timeout_seconds=timeout_seconds)
    if normalized == "gemini":
        return GeminiClient(api_key=api_key, timeout_seconds=timeout_seconds)
    if normalized == "deepseek":
        return DeepSeekClient(api_key=api_key, timeout_seconds=timeout_seconds)
    if normalized == "openai_compatible":
        return OpenAICompatibleClient(api_key=api_key, timeout_seconds=timeout_seconds)
    return OpenAIResponsesClient(api_key=api_key, timeout_seconds=timeout_seconds)


def normalize_provider(provider: str | None = None) -> str:
    value = (provider or os.getenv("LLM_PROVIDER", "") or default_provider()).strip().lower().replace("-", "_")
    if value in {"google", "google_gemini"}:
        value = "gemini"
    if value in {"deepseek_api", "deepseek_official"}:
        value = "deepseek"
    if value in {"openai_compat", "compatible"}:
        value = "openai_compatible"
    if value not in PROVIDERS:
        raise LLMNotConfigured(f"Unsupported LLM provider `{value}`. Use one of: {', '.join(sorted(PROVIDERS))}.")
    return value


def default_provider() -> str:
    configured = os.getenv("LLM_PROVIDER", "").strip().lower().replace("-", "_")
    if configured in PROVIDERS:
        return configured
    if os.getenv("GEMINI_API_KEY", "").strip():
        return "gemini"
    if os.getenv("DEEPSEEK_API_KEY", "").strip():
        return "deepseek"
    if os.getenv("OPENAI_API_KEY", "").strip():
        return "openai"
    if os.getenv("OPENAI_COMPATIBLE_BASE_URL", "").strip():
        return "openai_compatible"
    if _ollama_models(os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")):
        return "ollama"
    return "ollama"


def _provider_status(provider: str) -> dict[str, Any]:
    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        models = _ollama_models(base_url)
        default_model = os.getenv("OLLAMA_MODEL", "").strip() or _preferred_ollama_model(models)
        return {
            "id": "ollama",
            "label": "Ollama local",
            "configured": bool(default_model),
            "api_key_env": "",
            "model_env": "OLLAMA_MODEL",
            "default_model": default_model,
            "base_url": base_url,
            "available_models": models,
            "accepts_session_key": False,
            "profile": copy.deepcopy(PROVIDER_PROFILES["ollama"]),
            "message": (
                f"Ollama is reachable with {len(models)} installed model(s)."
                if models
                else "Ollama is not reachable or has no installed models. Start Ollama and run `ollama pull <model>`."
            ),
        }
    if provider == "gemini":
        configured = bool(os.getenv("GEMINI_API_KEY", "").strip())
        return {
            "id": "gemini",
            "label": "Gemini",
            "configured": configured,
            "api_key_env": "GEMINI_API_KEY",
            "model_env": "GEMINI_MODEL",
            "default_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip(),
            "base_url": os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
            "available_models": GEMINI_MODEL_OPTIONS,
            "accepts_session_key": True,
            "profile": copy.deepcopy(PROVIDER_PROFILES["gemini"]),
            "message": (
                "Gemini key is configured."
                if configured
                else "Paste a Gemini API key in the page, or set GEMINI_API_KEY in the shell."
            ),
        }
    if provider == "deepseek":
        configured = bool(os.getenv("DEEPSEEK_API_KEY", "").strip())
        return {
            "id": "deepseek",
            "label": "DeepSeek",
            "configured": configured,
            "api_key_env": "DEEPSEEK_API_KEY",
            "model_env": "DEEPSEEK_MODEL",
            "default_model": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash").strip(),
            "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            "available_models": [
                "deepseek-v4-flash",
                "deepseek-v4-pro",
                "deepseek-chat",
                "deepseek-reasoner",
            ],
            "accepts_session_key": True,
            "profile": copy.deepcopy(PROVIDER_PROFILES["deepseek"]),
            "message": (
                "DeepSeek key is configured."
                if configured
                else "Paste a DeepSeek API key in the page, or set DEEPSEEK_API_KEY in the shell."
            ),
        }
    if provider == "openai_compatible":
        base_url = os.getenv("OPENAI_COMPATIBLE_BASE_URL", "").strip()
        model = os.getenv("OPENAI_COMPATIBLE_MODEL", "").strip()
        return {
            "id": "openai_compatible",
            "label": "OpenAI-compatible",
            "configured": bool(base_url and model),
            "api_key_env": "OPENAI_COMPATIBLE_API_KEY",
            "model_env": "OPENAI_COMPATIBLE_MODEL",
            "default_model": model,
            "base_url": base_url,
            "available_models": [],
            "accepts_session_key": True,
            "profile": copy.deepcopy(PROVIDER_PROFILES["openai_compatible"]),
            "message": (
                "OpenAI-compatible endpoint is configured."
                if base_url and model
                else "Set OPENAI_COMPATIBLE_BASE_URL and OPENAI_COMPATIBLE_MODEL."
            ),
        }

    client = OpenAIResponsesClient()
    configured = bool(client.api_key)
    return {
        "id": "openai",
        "label": "OpenAI",
        "configured": configured,
        "api_key_env": "OPENAI_API_KEY",
        "model_env": "OPENAI_MODEL",
        "default_model": client.model,
        "base_url": client.base_url,
        "available_models": [],
        "accepts_session_key": True,
        "profile": copy.deepcopy(PROVIDER_PROFILES["openai"]),
        "message": "OpenAI key is configured." if configured else "Set OPENAI_API_KEY to use OpenAI.",
    }


def _ollama_models(base_url: str) -> list[str]:
    request = urllib.request.Request(f"{base_url.rstrip('/')}/api/tags", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return []
    models = data.get("models", []) if isinstance(data, dict) else []
    names = [item.get("name") for item in models if isinstance(item, dict) and isinstance(item.get("name"), str)]
    return sorted(names)


def _first_ollama_model(base_url: str) -> str:
    models = _ollama_models(base_url)
    return _preferred_ollama_model(models)


def _preferred_ollama_model(models: list[str]) -> str:
    if not models:
        return ""
    return max(models, key=_ollama_model_score)


def _ollama_model_score(model_name: str) -> float:
    name = model_name.lower()
    if any(token in name for token in ("embed", "bge", "nomic", "minilm")):
        return -100

    score = 0.0
    if "qwen" in name:
        score += 40
    elif "llama" in name:
        score += 32
    elif "mistral" in name:
        score += 30
    elif "gemma" in name:
        score += 28

    size = re.search(r"(\d+(?:\.\d+)?)b", name)
    if size:
        score += float(size.group(1))
    if "instruct" in name:
        score += 4
    if "q8" in name:
        score += 3
    elif "q6" in name:
        score += 2
    elif "q4" in name:
        score += 1
    if any(token in name for token in ("uncensored", "abliterated", "heretic")):
        score -= 6
    return score


def _urlopen_json(request: urllib.request.Request, timeout_seconds: int, label: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMRequestError(f"{label} request failed ({exc.code}): {detail[:2000]}") from exc
    except urllib.error.URLError as exc:
        raise LLMRequestError(f"{label} request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise LLMRequestError(f"{label} request timed out after {timeout_seconds}s.") from exc
    except json.JSONDecodeError as exc:
        raise LLMRequestError(f"{label} returned non-JSON response: {exc}") from exc


def _strip_thinking_text(content: str) -> str:
    text = content.strip()
    if "</think>" in text:
        text = text.split("</think>", 1)[1].strip()
    if text.startswith("<think>"):
        text = text.replace("<think>", "", 1).strip()
    return text


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
