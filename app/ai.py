import asyncio
import logging
import random

from openai import (
    APIConnectionError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)

from .config import settings


logger = logging.getLogger("nonni.ai")


class GroqProvider:

    def __init__(self):
        self.client: AsyncOpenAI | None = None

    def get_client(self) -> AsyncOpenAI:
        if self.client is None:
            self.client = AsyncOpenAI(
                api_key=settings.groq_api_key,
                base_url=settings.groq_base_url,
                timeout=settings.ai_timeout_seconds,
                max_retries=0,
            )
        return self.client

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:

        retryable = (RateLimitError, APITimeoutError, APIConnectionError)
        client = self.get_client()
        for attempt in range(settings.ai_max_retries + 1):
            try:
                response = await client.chat.completions.create(
                    model=model or settings.groq_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                break
            except retryable:
                if attempt >= settings.ai_max_retries:
                    raise
                delay = (2 ** attempt) + random.uniform(0, 0.5)
                logger.warning("Temporary AI error; retrying in %.1fs", delay)
                await asyncio.sleep(delay)

        if not response.choices:
            raise RuntimeError("AI returned no choices.")

        content = response.choices[0].message.content

        return content or ""


ai_provider = GroqProvider()
