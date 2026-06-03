from __future__ import annotations

from typing import Any

from mnemosyne.verifier.contract import AUTHORING_API_SCHEMA
from mnemosyne.chat_models.providers import client_generate_json, llm_status, make_llm_client


def status() -> dict[str, Any]:
    """Return configured provider/model status without coupling callers to authoring logic."""
    return llm_status()


def generate_json(
    *,
    messages: list[dict[str, str]],
    response_schema: dict[str, Any] | None = None,
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    """Generate raw JSON text from a provider.

    This is intentionally provider-level only: it does not validate, repair,
    or save problems. Higher-level agent workflows should call this service,
    then pass output to `app.verifier`.
    """
    schema = response_schema or AUTHORING_API_SCHEMA
    client = make_llm_client(provider=provider, api_key=api_key, timeout_seconds=timeout_seconds)
    text = client_generate_json(
        client,
        messages,
        schema,
        model=model,
        attachments=attachments or [],
    )
    return {"ok": True, "text": text, "provider": provider, "model": model}
