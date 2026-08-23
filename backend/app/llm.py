import json
from typing import Any

import httpx

from .config import settings


def _sanitize_error(message: str, *extra_secrets: str) -> str:
    for secret in [settings.llm_api_key, settings.kimi_api_key, *extra_secrets]:
        if secret:
            message = message.replace(secret, "[redacted]")
    return message


def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    *,
    api_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    timeout: float | None = None,
    max_tokens: int = 8192,
) -> str:
    return call_llm_messages(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        api_url=api_url,
        api_key=api_key,
        model=model,
        timeout=timeout,
        max_tokens=max_tokens,
    )


def call_llm_messages(
    messages: list[dict[str, Any]],
    temperature: float = 0.3,
    *,
    api_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    timeout: float | None = None,
    max_tokens: int = 8192,
) -> str:
    target_url = api_url or settings.llm_api_url
    target_key = api_key if api_key is not None else settings.llm_api_key
    target_model = model or settings.llm_model
    target_timeout = timeout or settings.llm_timeout

    requires_key = not (settings.llm_provider == "ollama" or target_url.startswith("http://localhost"))
    if requires_key and not target_key:
        return json.dumps({"error": "missing_key", "fallback": True})

    try:
        headers = {"Content-Type": "application/json"}
        if target_key:
            headers["Authorization"] = f"Bearer {target_key}"
        resp = httpx.post(
            target_url,
            headers=headers,
            json={
                "model": target_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max(1, min(max_tokens, 8192)),
            },
            timeout=target_timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return json.dumps({"error": _sanitize_error(str(e), target_key), "fallback": True})


def call_kimi(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    *,
    timeout: float | None = None,
    max_tokens: int = 8192,
) -> str:
    return call_llm(
        system_prompt,
        user_prompt,
        temperature,
        timeout=timeout,
        max_tokens=max_tokens,
    )


def test_llm_config(provider: str, api_url: str, api_key: str, model: str, timeout: float) -> dict:
    result = call_llm(
        "You are a connection test. Reply with OK.",
        "Reply with OK only.",
        temperature=0,
        api_url=api_url,
        api_key=api_key,
        model=model,
        timeout=timeout,
    )
    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        parsed = {}
    if parsed.get("error"):
        return {"ok": False, "provider": provider, "message": _sanitize_error(str(parsed["error"]), api_key)}
    return {"ok": True, "provider": provider, "model": model, "message": "连接成功"}
