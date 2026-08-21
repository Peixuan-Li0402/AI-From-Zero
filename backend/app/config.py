import os
from pathlib import Path
from pydantic import BaseModel


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
DATA_DIR = ROOT_DIR / "data"
ENV_PATH = ROOT_DIR / ".env"


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


_DOTENV = _parse_env_file(ENV_PATH)


def _get_env(name: str, default: str = "", *fallbacks: str) -> str:
    for key in (name, *fallbacks):
        value = os.environ.get(key)
        if value is None:
            value = _DOTENV.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def _get_int(name: str, default: int) -> int:
    raw = _get_env(name, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    raw = _get_env(name, str(default))
    try:
        return float(raw)
    except ValueError:
        return default


def _get_csv(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in _get_env(name, default).split(",") if item.strip()]


def _get_bool(name: str, default: bool = False) -> bool:
    value = _get_env(name, "true" if default else "false").lower()
    return value in {"1", "true", "yes", "on"}


class ProviderPreset(BaseModel):
    id: str
    label: str
    api_url: str
    model: str
    env_var: str
    requires_key: bool = True


PROVIDER_PRESETS = [
    ProviderPreset(
        id="kimi",
        label="Kimi / Moonshot",
        api_url="https://api.moonshot.cn/v1/chat/completions",
        model="moonshot-v1-128k",
        env_var="KIMI_API_KEY",
    ),
    ProviderPreset(
        id="openai",
        label="OpenAI",
        api_url="https://api.openai.com/v1/chat/completions",
        model="gpt-4o-mini",
        env_var="OPENAI_API_KEY",
    ),
    ProviderPreset(
        id="openrouter",
        label="OpenRouter",
        api_url="https://openrouter.ai/api/v1/chat/completions",
        model="openai/gpt-4o-mini",
        env_var="OPENROUTER_API_KEY",
    ),
    ProviderPreset(
        id="deepseek",
        label="DeepSeek",
        api_url="https://api.deepseek.com/chat/completions",
        model="deepseek-chat",
        env_var="DEEPSEEK_API_KEY",
    ),
    ProviderPreset(
        id="ollama",
        label="Ollama Local",
        api_url="http://localhost:11434/v1/chat/completions",
        model="llama3.1",
        env_var="",
        requires_key=False,
    ),
    ProviderPreset(
        id="custom",
        label="Custom OpenAI-Compatible",
        api_url="",
        model="",
        env_var="LLM_API_KEY",
    ),
]


def provider_by_id(provider_id: str) -> ProviderPreset:
    for preset in PROVIDER_PRESETS:
        if preset.id == provider_id:
            return preset
    return PROVIDER_PRESETS[0]


def _discover_provider() -> str:
    configured = _get_env("LLM_PROVIDER", "")
    if configured:
        return configured
    if _get_env("KIMI_API_KEY", ""):
        return "kimi"
    if _get_env("OPENAI_API_KEY", ""):
        return "openai"
    if _get_env("OPENROUTER_API_KEY", ""):
        return "openrouter"
    if _get_env("DEEPSEEK_API_KEY", ""):
        return "deepseek"
    return "kimi"


class Settings:
    app_name = "AI From Zero"
    app_version = "0.7.0"

    def __init__(self):
        self.reload()

    def reload(self) -> None:
        global _DOTENV
        _DOTENV = _parse_env_file(ENV_PATH)
        provider = _discover_provider()
        preset = provider_by_id(provider)
        self.app_host = _get_env("APP_HOST", "127.0.0.1")
        self.app_port = _get_int("APP_PORT", _get_int("PORT", 8080))
        self.llm_provider = provider
        self.llm_api_key = _get_env("LLM_API_KEY", "", preset.env_var, "KIMI_API_KEY")
        self.llm_api_url = _get_env("LLM_API_URL", preset.api_url, "KIMI_API_URL")
        self.llm_model = _get_env("LLM_MODEL", preset.model, "KIMI_MODEL")
        self.llm_timeout = _get_float("LLM_TIMEOUT", _get_float("KIMI_TIMEOUT", 60.0))

        self.kimi_api_key = self.llm_api_key
        self.kimi_api_url = self.llm_api_url
        self.kimi_model = self.llm_model
        self.kimi_timeout = self.llm_timeout
        self.wechat_webhook_url = _get_env("WECHAT_WEBHOOK_URL", "")
        self.qq_bot_webhook_url = _get_env("QQ_BOT_WEBHOOK_URL", "")
        self.message_bridge_token = _get_env("MESSAGE_BRIDGE_TOKEN", "")
        self.qxd_api_key = _get_env("QXD_API_KEY", "")
        self.public_base_url = _get_env("PUBLIC_BASE_URL", "").rstrip("/")
        self.qxd_model_id = _get_env("QXD_MODEL_ID", "ai-from-zero-agent")
        self.qxd_attachment_allowed_hosts = _get_csv("QXD_ATTACHMENT_ALLOWED_HOSTS")
        self.qxd_max_attachment_mb = max(1, _get_int("QXD_MAX_ATTACHMENT_MB", 25))
        self.qxd_max_concurrency = max(1, _get_int("QXD_MAX_CONCURRENCY", 4))
        self.qxd_request_timeout = min(115.0, max(5.0, _get_float("QXD_REQUEST_TIMEOUT", 105.0)))
        self.agent_llm_timeout = min(45.0, max(8.0, _get_float("AGENT_LLM_TIMEOUT", 28.0)))
        self.agent_max_tokens = min(1800, max(256, _get_int("AGENT_MAX_TOKENS", 1000)))
        self.agent_search_timeout = min(8.0, max(1.0, _get_float("AGENT_SEARCH_TIMEOUT", 4.5)))
        self.agent_search_cache_ttl = max(30, _get_int("AGENT_SEARCH_CACHE_TTL", 600))
        self.agent_realtime_search = _get_bool("AGENT_REALTIME_SEARCH", True)
        self.qxd_artifact_ttl = max(300, _get_int("QXD_ARTIFACT_TTL", 1800))
        self.qxd_workspace_ttl = max(1800, _get_int("QXD_WORKSPACE_TTL", 604800))
        self.qxd_workspace_limit = min(500, max(12, _get_int("QXD_WORKSPACE_LIMIT", 100)))
        self.qxd_allow_private_dns_proxy = _get_bool("QXD_ALLOW_PRIVATE_DNS_PROXY", False)
        self.cors_allowed_origins = _get_csv(
            "CORS_ALLOWED_ORIGINS",
            (
                "http://127.0.0.1:8080,http://localhost:8080,"
                "https://www.xiaoda.tsinghua.edu.cn,https://xiaoda.tsinghua.edu.cn"
            ),
        )

    @property
    def llm_configured(self) -> bool:
        if self.llm_provider == "ollama":
            return bool(self.llm_api_url and self.llm_model)
        return bool(self.llm_api_key and self.llm_api_key != "REPLACE_WITH_YOUR_KEY")

    @property
    def config_writable(self) -> bool:
        return os.access(ROOT_DIR, os.W_OK)

    @property
    def qxd_configured(self) -> bool:
        return bool(self.qxd_api_key and self.qxd_api_key != "REPLACE_WITH_A_RANDOM_SECRET")

    def masked_key(self) -> str:
        key = self.llm_api_key
        if not key:
            return ""
        if len(key) <= 8:
            return "*" * len(key)
        return f"{key[:4]}...{key[-4:]}"

    @staticmethod
    def mask_secret(value: str) -> str:
        if not value:
            return ""
        if len(value) <= 12:
            return "*" * len(value)
        return f"{value[:6]}...{value[-6:]}"


def quote_env_value(value: str) -> str:
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def save_env_updates(updates: dict[str, str]) -> None:
    existing = _parse_env_file(ENV_PATH)
    existing.update({key: str(value) for key, value in updates.items() if value is not None})
    ordered_keys = [
        "LLM_PROVIDER",
        "LLM_API_KEY",
        "LLM_API_URL",
        "LLM_MODEL",
        "LLM_TIMEOUT",
        "APP_HOST",
        "APP_PORT",
    ]
    lines = []
    for key in ordered_keys:
        if key in existing:
            lines.append(f"{key}={quote_env_value(existing[key])}")
    for key in sorted(existing):
        if key not in ordered_keys:
            lines.append(f"{key}={quote_env_value(existing[key])}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    settings.reload()


settings = Settings()
