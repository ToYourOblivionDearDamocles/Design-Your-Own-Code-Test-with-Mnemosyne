from __future__ import annotations

import copy
import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Protocol
from urllib.parse import quote

from mnemosyne.prompts import messages_with_prompt_contract, prompt_only_contract

DEFAULT_MODEL = "gpt-4.1-mini"

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
        "strategy": "json schema + prompt -> json_object + prompt fallback",
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

        prepared_messages = messages_with_prompt_contract(messages, response_schema)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": selected_model,
            "messages": prepared_messages,
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
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            data = _urlopen_json(request, self.timeout_seconds, "OpenAI-compatible API")
        except LLMRequestError as exc:
            if not _is_response_format_error(str(exc)):
                raise
            fallback_payload = {
                "model": selected_model,
                "messages": prepared_messages,
                "temperature": 0,
                "response_format": {"type": "json_object"},
            }
            fallback_request = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(fallback_payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            data = _urlopen_json(fallback_request, self.timeout_seconds, "OpenAI-compatible API")
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
        prepared_messages = messages_with_prompt_contract(messages, response_schema)
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
            contract = prompt_only_contract(response_schema)
            request_text = (
                f"{contract}\n\n"
                "Return ONLY valid JSON. Do not wrap it in markdown. Do not include commentary.\n\n"
                "The final User request section below is the authoritative task.\n\n"
                f"{user_text}"
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

def client_generate_json(
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


def client_supports_multimodal_attachments(client: JsonGeneratingClient) -> bool:
    return callable(getattr(client, "generate_json_with_attachments", None))
