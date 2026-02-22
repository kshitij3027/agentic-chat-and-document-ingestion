"""Optional reranking via Cohere API."""
import logging
import time

import httpx
from postgrest.exceptions import APIError

from app.db.supabase import get_supabase_client
from app.routers.settings import decrypt_value

logger = logging.getLogger(__name__)

DEFAULT_RERANKER_MODEL = "rerank-v3.5"


def get_reranker_settings() -> dict | None:
    """Read reranker_api_key and reranker_model from global_settings.

    Returns dict with 'api_key' and 'model', or None if not configured.
    """
    supabase = get_supabase_client()
    try:
        result = (
            supabase.table("global_settings")
            .select("reranker_api_key, reranker_model")
            .limit(1)
            .maybe_single()
            .execute()
        )
        data = result.data if result else None
    except APIError:
        return None

    if not data:
        return None

    api_key = decrypt_value(data.get("reranker_api_key"))
    if not api_key:
        return None

    return {
        "api_key": api_key,
        "model": data.get("reranker_model") or DEFAULT_RERANKER_MODEL,
    }


async def rerank_results(
    query: str,
    documents: list[dict],
    top_n: int,
) -> list[dict]:
    """Rerank documents via Cohere v2 rerank API.

    Falls back to original order if reranker is not configured or on error.
    Each document dict must have a 'content' key.
    Returns documents with 'relevance_score' added.
    """
    if not documents:
        return documents

    settings = get_reranker_settings()
    if not settings:
        logger.info("Reranker not configured, skipping")
        return documents[:top_n]

    doc_texts = [d.get("content", "") for d in documents]

    logger.info(f"Reranking {len(documents)} documents with model={settings['model']}")

    try:
        t0 = time.perf_counter()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.cohere.com/v2/rerank",
                headers={
                    "Authorization": f"Bearer {settings['api_key']}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings["model"],
                    "query": query,
                    "documents": doc_texts,
                    "top_n": top_n,
                },
            )
            response.raise_for_status()
            data = response.json()
        elapsed = time.perf_counter() - t0

        reranked = []
        for result in data.get("results", []):
            idx = result["index"]
            doc = {**documents[idx], "relevance_score": result["relevance_score"]}
            reranked.append(doc)

        if reranked:
            logger.info(
                f"Rerank complete in {elapsed:.1f}s — "
                f"top score: {reranked[0]['relevance_score']:.3f}, "
                f"bottom score: {reranked[-1]['relevance_score']:.3f}"
            )

        return reranked

    except Exception as e:
        logger.warning(f"Reranker failed, returning original order: {e}")
        return documents[:top_n]
