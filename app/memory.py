import re

from .config import settings
from .database import get_memories


def detect_language(text: str) -> str:
    arabic = re.search(r"[\u0600-\u06FF]", text)
    if arabic:
        return "ar"
    return "en"


def build_memory_context(memories) -> str:
    if not memories:
        return ""

    lines = []
    for memory in memories:
        lines.append(f"- [{memory.memory_type}] {memory.content}")

    return "\n".join(lines)


async def get_user_memory_context(telegram_user_id: int) -> str:
    if not settings.enable_memory:
        return ""

    memories = await get_memories(
        telegram_user_id,
        settings.max_memory_items,
    )

    return build_memory_context(memories)
