from urllib.parse import parse_qs, unquote, urlparse

import httpx
from bs4 import BeautifulSoup


def _real_url(href: str) -> str:
    parsed = urlparse(href)
    target = parse_qs(parsed.query).get("uddg")
    return unquote(target[0]) if target else href


async def search_web(query: str, limit: int = 5) -> list[dict[str, str]]:
    """Retrieve public search-result titles, links and snippets without an API key."""
    try:
        async with httpx.AsyncClient(
            timeout=20,
            follow_redirects=True,
            trust_env=False,
            headers={"User-Agent": "Mozilla/5.0 NonniBot/2.2"},
        ) as client:
            response = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
            )
            response.raise_for_status()
    except httpx.HTTPError:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for result in soup.select(".result"):
        link = result.select_one(".result__a")
        if not link:
            continue
        url = _real_url(link.get("href", ""))
        if not url.startswith(("http://", "https://")):
            continue
        snippet = result.select_one(".result__snippet")
        results.append(
            {
                "title": link.get_text(" ", strip=True),
                "url": url,
                "snippet": snippet.get_text(" ", strip=True) if snippet else "",
            }
        )
        if len(results) >= limit:
            break
    return results


def format_results(results: list[dict[str, str]]) -> str:
    return "\n\n".join(
        f"[{index}] {item['title']}\nURL: {item['url']}\n{item['snippet']}"
        for index, item in enumerate(results, start=1)
    )
