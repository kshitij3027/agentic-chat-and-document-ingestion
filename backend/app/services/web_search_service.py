"""Web search service using Tavily API."""
import logging
import httpx
from postgrest.exceptions import APIError

from app.db.supabase import get_supabase_client
from app.routers.settings import decrypt_value

logger = logging.getLogger(__name__)


def get_web_search_settings() -> dict | None:
    """
    Get web search settings from global_settings.

    Returns dict with 'provider', 'api_key', 'enabled' or None if disabled/unconfigured.
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("global_settings").select(
            "web_search_provider, web_search_api_key, web_search_enabled"
        ).limit(1).maybe_single().execute()
        data = result.data if result else None
    except APIError:
        return None

    if not data:
        return None

    if not data.get("web_search_enabled"):
        return None

    api_key = decrypt_value(data.get("web_search_api_key"))
    if not api_key:
        return None

    return {
        "provider": data.get("web_search_provider") or "tavily",
        "api_key": api_key,
        "enabled": True,
    }


async def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web using Tavily API.

    Returns list of dicts with 'title', 'url', 'content' keys.
    """
    settings = get_web_search_settings()
    if not settings:
        return [{"title": "Error", "url": "", "content": "Web search is not configured."}]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings["api_key"],
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "basic",
                    "include_answer": False,
                    "include_raw_content": False,
                },
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
            })
        return results

    except Exception as e:
        logger.exception("Web search error")
        return [{"title": "Error", "url": "", "content": f"Web search failed: {e}"}]


def format_search_results(results: list[dict]) -> str:
    """Format web search results for LLM context."""
    if not results:
        return "No web search results found."

    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        if r.get("url"):
            lines.append(f"   URL: {r['url']}")
        lines.append(f"   {r['content']}")
        lines.append("")

    return "\n".join(lines)
