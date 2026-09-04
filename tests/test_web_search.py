import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.web_search import _is_news_query, format_results, search_web


class WebSearchTests(unittest.TestCase):
    def test_news_query_detection(self):
        self.assertTrue(_is_news_query("latest AI news"))
        self.assertTrue(_is_news_query("آخر أخبار التقنية"))
        self.assertFalse(_is_news_query("Python tutorial"))

    def test_formatted_results_include_url(self):
        text = format_results([{"title": "Example", "url": "https://example.com", "snippet": "Result"}])
        self.assertIn("https://example.com", text)

    def test_tavily_response_is_normalized(self):
        async def run_test():
            response = AsyncMock()
            response.raise_for_status = lambda: None
            response.json = lambda: {
                "results": [{"title": "AI News", "url": "https://example.com/ai", "content": "Update"}]
            }
            client = AsyncMock()
            client.post.return_value = response
            context = AsyncMock()
            context.__aenter__.return_value = client
            with patch("app.web_search.httpx.AsyncClient", return_value=context):
                results = await search_web("latest AI news", "test-key")
                request = client.post.await_args
                self.assertEqual(request.kwargs["json"]["topic"], "news")
                self.assertTrue(request.kwargs["json"]["safe_search"])
                self.assertEqual(results[0]["title"], "AI News")

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
