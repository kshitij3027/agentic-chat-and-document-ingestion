"""Embedding service using configured provider."""
from typing import Any

from fastapi import HTTPException, status
from postgrest.exceptions import APIError

from app.db.supabase import get_supabase_client
from app.services.langsmith import get_traced_async_openai_client
from app.routers.settings import decrypt_value


def get_global_embedding_settings() -> dict[str, Any]:
    """
    Get global embedding settings from the global_settings table.

    Returns dict with keys: model, base_url, api_key, dimensions
    Raises HTTPException(503) if no API key is configured.
    """
    supabase = get_supabase_client()
    try:
        result = supabase.table("global_settings").select(
            "embedding_model, embedding_base_url, embedding_api_key, embedding_dimensions"
        ).limit(1).maybe_single().execute()
        data = result.data if result else None
    except APIError:
        data = None

    api_key = decrypt_value(data.get("embedding_api_key")) if data else None
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding not configured. An admin must configure embedding settings."
        )

    return {
        "model": data.get("embedding_model") or "text-embedding-3-small",
        "base_url": data.get("embedding_base_url") or None,
        "api_key": api_key,
        "dimensions": data.get("embedding_dimensions") or 1536,
    }


async def get_embeddings(texts: list[str], user_id: str | None = None) -> list[list[float]]:
    """Generate embeddings for a list of texts using global settings."""
    emb_settings = get_global_embedding_settings()
    model = emb_settings["model"]
    dimensions = emb_settings["dimensions"]

    client = get_traced_async_openai_client(
        base_url=emb_settings["base_url"],
        api_key=emb_settings["api_key"],
    )

    response = await client.embeddings.create(
        model=model,
        input=texts,
        dimensions=dimensions,
    )
    return [item.embedding for item in response.data]
