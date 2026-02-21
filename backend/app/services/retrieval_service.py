"""Vector search via match_chunks RPC."""
from app.db.supabase import get_supabase_client
from app.services.embedding_service import get_embeddings


async def search_documents(query: str, user_id: str, top_k: int = 5, threshold: float = 0.5) -> list[dict]:
    """
    Search user's documents for relevant chunks using vector similarity.

    Args:
        query: Search query text
        user_id: The user's ID for RLS filtering
        top_k: Maximum number of results
        threshold: Minimum similarity threshold

    Returns:
        List of matching chunks with similarity scores
    """
    query_embedding = await get_embeddings([query], user_id=user_id)

    supabase = get_supabase_client()
    result = supabase.rpc("match_chunks", {
        "query_embedding": query_embedding[0],
        "match_threshold": threshold,
        "match_count": top_k,
        "p_user_id": user_id,
    }).execute()

    return result.data or []
