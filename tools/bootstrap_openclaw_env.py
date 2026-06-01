#!/usr/bin/env python3
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


PROVIDERS = [
    ("openai", "OPENAI_API_KEY", "https://api.openai.com/v1/chat/completions", "gpt-4o-mini"),
    ("openrouter", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/chat/completions", "openai/gpt-4o-mini"),
    ("deepseek", "DEEPSEEK_API_KEY", "https://api.deepseek.com/chat/completions", "deepseek-chat"),
    ("kimi", "KIMI_API_KEY", "https://api.moonshot.cn/v1/chat/completions", "moonshot-v1-128k"),
    ("custom", "LLM_API_KEY", os.environ.get("LLM_API_URL", ""), os.environ.get("LLM_MODEL", "")),
]


def parse_env(path: Path) -> dict[str, str]:
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.strip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> int:
    existing = parse_env(ENV_PATH)
    if existing.get("LLM_API_KEY"):
        print(".env already has LLM_API_KEY; nothing changed.")
        return 0

    selected = None
    for provider, env_var, api_url, model in PROVIDERS:
        key = os.environ.get(env_var, "").strip()
        if key:
            selected = (provider, key, api_url, model)
            break

    if not selected:
        print("No supported API key found in environment. Set OPENAI_API_KEY, OPENROUTER_API_KEY, DEEPSEEK_API_KEY, KIMI_API_KEY, or LLM_API_KEY.")
        return 1

    provider, key, api_url, model = selected
    existing.update({
        "LLM_PROVIDER": provider,
        "LLM_API_KEY": key,
        "LLM_API_URL": os.environ.get("LLM_API_URL", api_url),
        "LLM_MODEL": os.environ.get("LLM_MODEL", model),
        "LLM_TIMEOUT": existing.get("LLM_TIMEOUT", "60"),
        "APP_HOST": existing.get("APP_HOST", "127.0.0.1"),
        "APP_PORT": existing.get("APP_PORT", "8080"),
    })

    order = ["LLM_PROVIDER", "LLM_API_KEY", "LLM_API_URL", "LLM_MODEL", "LLM_TIMEOUT", "APP_HOST", "APP_PORT"]
    lines = [f"{key_name}={quote(existing[key_name])}" for key_name in order if key_name in existing]
    for key_name in sorted(existing):
        if key_name not in order:
            lines.append(f"{key_name}={quote(existing[key_name])}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote .env for provider: {provider}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
