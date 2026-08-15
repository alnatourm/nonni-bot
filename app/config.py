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

    database_url: str

    default_language: str
    max_history: int
    max_memory_items: int
    max_message_length: int
    max_file_size_mb: int

    enable_memory: bool
    enable_web_search: bool
    enable_documents: bool
    enable_vision: bool

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


settings = Settings(
    telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
    groq_api_key=os.getenv("GROQ_API_KEY", ""),
    groq_base_url=os.getenv(
        "GROQ_BASE_URL",
        "https://api.groq.com/openai/v1",
    ),
    groq_model=os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile",
    ),
    database_url=os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./data/nonni.db",
    ),
    default_language=os.getenv(
        "DEFAULT_LANGUAGE",
        "auto",
    ),
    max_history=int(
        os.getenv("MAX_HISTORY", "20")
    ),
    max_memory_items=int(
        os.getenv("MAX_MEMORY_ITEMS", "50")
    ),
    max_message_length=int(
        os.getenv("MAX_MESSAGE_LENGTH", "12000")
    ),
    max_file_size_mb=int(
        os.getenv("MAX_FILE_SIZE_MB", "10")
    ),
    enable_memory=env_bool("ENABLE_MEMORY", True),
    enable_web_search=env_bool("ENABLE_WEB_SEARCH", True),
    enable_documents=env_bool("ENABLE_DOCUMENTS", True),
    enable_vision=env_bool("ENABLE_VISION", True),
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
