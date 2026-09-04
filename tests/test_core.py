import unittest
from unittest.mock import AsyncMock, patch

from app.memory import detect_language
from app.router import detect_intent, generate_response
from app.telegram_bot import split_message


class CoreTests(unittest.TestCase):
    def test_language_detection(self):
        self.assertEqual(detect_language("مرحبا"), "ar")
        self.assertEqual(detect_language("hello"), "en")

    def test_intent_detection(self):
        self.assertEqual(detect_intent("Fix my Python code"), "coding")
        self.assertEqual(detect_intent("خطة تسويق لشركة"), "business")
        self.assertEqual(detect_intent("طريقة طبخ الأرز"), "cooking")

    def test_message_split_respects_limit(self):
        chunks = split_message(("word " * 2000).strip(), limit=100)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(0 < len(chunk) <= 100 for chunk in chunks))
        self.assertEqual(" ".join(chunks), ("word " * 2000).strip())

    def test_current_message_is_sent_once(self):
        async def run_test():
            with (
                patch("app.router.get_history", new=AsyncMock(return_value=[])),
                patch(
                    "app.router.get_user_memory_context",
                    new=AsyncMock(return_value=""),
                ),
                patch("app.router.ai_provider.chat", new=AsyncMock(return_value="ok")) as chat,
            ):
                await generate_response(1, "hello once")
                messages = chat.await_args.kwargs["messages"]
                occurrences = sum(
                    message.get("content") == "hello once" for message in messages
                )
                self.assertEqual(occurrences, 1)

        import asyncio

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
