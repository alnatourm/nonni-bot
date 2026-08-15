from openai import AsyncOpenAI

from .config import settings


class GroqProvider:

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
        )

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:

        response = await self.client.chat.completions.create(
            model=model or settings.groq_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if not response.choices:
            raise RuntimeError("AI returned no choices.")

        content = response.choices[0].message.content

        return content or ""


ai_provider = GroqProvider()
