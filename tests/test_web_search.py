import unittest

from app.web_search import format_results, parse_rss


class WebSearchTests(unittest.TestCase):
    def test_bing_rss_is_parsed(self):
        xml = """<rss><channel><item><title>AI News</title><link>https://example.com/news</link><description>Latest update</description></item></channel></rss>"""
        results = parse_rss(xml)
        self.assertEqual(results[0]["title"], "AI News")
        self.assertEqual(results[0]["url"], "https://example.com/news")

    def test_formatted_results_include_url(self):
        text = format_results([{"title": "Example", "url": "https://example.com", "snippet": "Result"}])
        self.assertIn("https://example.com", text)


if __name__ == "__main__":
    unittest.main()
