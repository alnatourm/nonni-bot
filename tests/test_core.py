import unittest
from unittest.mock import AsyncMock, patch

from app.memory import detect_language
from app.router import (
    detect_intent,
    generate_response,
    needs_web_search,
    runtime_identity,
    web_search_for_turn,
)
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

    def test_runtime_identity_uses_configuration(self):
        identity = runtime_identity()
        self.assertIn("openai/gpt-oss-120b", identity)
        self.assertIn("Groq", identity)

    def test_live_information_routes_to_web(self):
        self.assertTrue(needs_web_search("weather in Amman tomorrow"))
        self.assertTrue(needs_web_search("latest AI news"))
        self.assertTrue(needs_web_search("طقس عمان غدا"))
        self.assertFalse(needs_web_search("write a Python function"))

    def test_weather_location_follow_up_uses_web(self):
        history = [
            {"role": "user", "content": "what is the weather tomorrow?"},
            {"role": "assistant", "content": "Which city?"},
        ]
        self.assertTrue(web_search_for_turn("Amman", history))

    def test_unrelated_follow_up_does_not_use_web(self):
        history = [{"role": "user", "content": "write a Python function"}]
        self.assertFalse(web_search_for_turn("Amman", history))


if __name__ == "__main__":
    unittest.main()
