import httpx


def _is_news_query(query: str) -> bool:
    value = query.lower()
    return any(term in value for term in ("news", "latest", "أخبار", "اخبار", "آخر"))


async def search_web(
    query: str,
    api_key: str,
    limit: int = 5,
) -> list[dict[str, str]]:
    """Retrieve structured Tavily results for the hybrid search pipeline."""
    if not api_key:
        return []
    try:
        async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "query": query,
                    "topic": "news" if _is_news_query(query) else "general",
                    "search_depth": "basic",
                    "max_results": limit,
                    "include_answer": False,
                    "include_raw_content": False,
                    "include_images": False,
                    "safe_search": True,
                },
            )
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError):
        return []

    results = []
    for item in payload.get("results", []):
        title = str(item.get("title", "")).strip()
        url = str(item.get("url", "")).strip()
        content = str(item.get("content", "")).strip()
        if title and url.startswith(("http://", "https://")):
            results.append({"title": title, "url": url, "snippet": content[:2000]})
    return results[:limit]


def format_results(results: list[dict[str, str]]) -> str:
    return "\n\n".join(
        f"[{index}] {item['title']}\nURL: {item['url']}\n{item['snippet']}"
        for index, item in enumerate(results, start=1)
    )
