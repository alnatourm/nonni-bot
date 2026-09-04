import unittest

from app.web_search import _real_url, format_results


class WebSearchTests(unittest.TestCase):
    def test_redirect_is_unwrapped(self):
        url = "//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fnews"
        self.assertEqual(_real_url(url), "https://example.com/news")

    def test_formatted_results_include_url(self):
        text = format_results([{"title": "Example", "url": "https://example.com", "snippet": "Result"}])
        self.assertIn("https://example.com", text)


if __name__ == "__main__":
    unittest.main()
