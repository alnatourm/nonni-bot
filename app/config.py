import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    groq_api_key: str
    groq_base_url: str
    groq_model: str
    groq_web_model: str
    groq_vision_model: str

    database_url: str

    default_language: str
    max_history: int
    max_memory_items: int
    max_message_length: int
    max_file_size_mb: int
    max_document_chars: int
    enable_memory: bool
    enable_web_search: bool
    enable_documents: bool
    enable_vision: bool
    requests_per_minute: int
    ai_timeout_seconds: float
    ai_max_retries: int
    allowed_user_ids: frozenset[int]

    log_level: str


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def env_int(name: str, default: int, minimum: int = 1) -> int:
    value = int(os.getenv(name, str(default)))
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def env_user_ids(name: str) -> frozenset[int]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return frozenset()
    try:
        return frozenset(int(item.strip()) for item in raw.split(",") if item.strip())
    except ValueError as exc:
        raise ValueError(f"{name} must contain comma-separated Telegram user IDs") from exc


settings = Settings(
    telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
    groq_api_key=os.getenv("GROQ_API_KEY", ""),
    groq_base_url=os.getenv(
        "GROQ_BASE_URL",
        "https://api.groq.com/openai/v1",
    ),
    groq_model=os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-120b",
    ),
    groq_web_model=os.getenv("GROQ_WEB_MODEL", "groq/compound"),
    groq_vision_model=os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.6-27b"),
    database_url=os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./data/nonni.db",
    ),
    default_language=os.getenv(
        "DEFAULT_LANGUAGE",
        "auto",
    ),
    max_history=env_int("MAX_HISTORY", 20),
    max_memory_items=env_int("MAX_MEMORY_ITEMS", 50),
    max_message_length=env_int("MAX_MESSAGE_LENGTH", 12000),
    max_file_size_mb=env_int("MAX_FILE_SIZE_MB", 10),
    max_document_chars=env_int("MAX_DOCUMENT_CHARS", 50000),
    enable_memory=env_bool("ENABLE_MEMORY", True),
    enable_web_search=env_bool("ENABLE_WEB_SEARCH", True),
    enable_documents=env_bool("ENABLE_DOCUMENTS", True),
    enable_vision=env_bool("ENABLE_VISION", True),
    requests_per_minute=env_int("REQUESTS_PER_MINUTE", 10),
    ai_timeout_seconds=float(os.getenv("AI_TIMEOUT_SECONDS", "75")),
    ai_max_retries=env_int("AI_MAX_RETRIES", 3, minimum=0),
    allowed_user_ids=env_user_ids("ALLOWED_USER_IDS"),
    log_level=os.getenv("LOG_LEVEL", "INFO"),
)


def validate_settings() -> None:
    missing = []

    if not settings.telegram_bot_token:
        missing.append("TELEGRAM_BOT_TOKEN")

    if not settings.groq_api_key:
        missing.append("GROQ_API_KEY")

    if missing:
        raise RuntimeError(
            "Missing environment variables: "
            + ", ".join(missing)
        )
