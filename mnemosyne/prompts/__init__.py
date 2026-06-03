from __future__ import annotations

from typing import Any

from mnemosyne.prompts.registry import PROMPT_DIR, load_prompt, prompt_text, render_prompt

SCHEMA_CONTRACT_PROMPTS = {
    "mnemosyne_problem_collection": "contract_problem_collection",
    "local_leetcode_problem_collection": "contract_problem_collection",
    "mnemosyne_test_drafts": "contract_test_drafts",
    "local_leetcode_test_drafts": "contract_test_drafts",
    "mnemosyne_source_digest": "contract_source_digest",
    "local_leetcode_source_digest": "contract_source_digest",
}


def prompt_only_contract(response_schema: dict[str, Any]) -> str:
    name = str(response_schema.get("name") or "")
    prompt_id = SCHEMA_CONTRACT_PROMPTS.get(name)
    if prompt_id:
        return render_prompt(prompt_id)
    return "Return JSON matching the requested object shape."


def messages_with_prompt_contract(
    messages: list[dict[str, str]],
    response_schema: dict[str, Any],
) -> list[dict[str, str]]:
    contract = prompt_only_contract(response_schema)
    prepared = [dict(message) for message in messages]
    contract_text = (
        f"{contract}\n\n"
        "Return ONLY valid JSON. Do not wrap it in markdown. Do not include commentary.\n\n"
        "The final User request section below is the authoritative task."
    )
    for message in reversed(prepared):
        if message.get("role") == "user":
            original = message.get("content", "")
            message["content"] = f"{contract_text}\n\n{original}"
            return prepared
    prepared.append({"role": "user", "content": contract_text.strip()})
    return prepared


__all__ = [
    "PROMPT_DIR",
    "load_prompt",
    "messages_with_prompt_contract",
    "prompt_only_contract",
    "prompt_text",
    "render_prompt",
]
