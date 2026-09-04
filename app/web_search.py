import html
import re
from xml.etree import ElementTree

import httpx


def _plain_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(value))).strip()


def parse_rss(xml_text: str, limit: int = 5) -> list[dict[str, str]]:
    root = ElementTree.fromstring(xml_text)
    results = []
    for item in root.findall(".//item"):
        title = _plain_text(item.findtext("title", ""))
        url = item.findtext("link", "").strip()
        snippet = _plain_text(item.findtext("description", ""))
        if title and url.startswith(("http://", "https://")):
            results.append({"title": title, "url": url, "snippet": snippet})
        if len(results) >= limit:
            break
    return results


async def search_web(query: str, limit: int = 5) -> list[dict[str, str]]:
    """Retrieve live Bing RSS results without an API key."""
    try:
        async with httpx.AsyncClient(
            timeout=20,
            follow_redirects=True,
            trust_env=False,
            headers={"User-Agent": "Mozilla/5.0 NonniBot/2.2"},
        ) as client:
            response = await client.get(
                "https://www.bing.com/search",
                params={"q": query, "format": "rss"},
            )
            response.raise_for_status()
        return parse_rss(response.text, limit)
    except (httpx.HTTPError, ElementTree.ParseError):
        return []


def format_results(results: list[dict[str, str]]) -> str:
    return "\n\n".join(
        f"[{index}] {item['title']}\nURL: {item['url']}\n{item['snippet']}"
        for index, item in enumerate(results, start=1)
    )
