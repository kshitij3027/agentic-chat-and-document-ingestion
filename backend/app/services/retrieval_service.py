"""Vector search via match_chunks RPC."""
from app.db.supabase import get_supabase_client
from app.services.embedding_service import get_embeddings


async def search_documents(
    query: str,
    user_id: str,
    top_k: int = 5,
    threshold: float = 0.3,
    metadata_filter: dict | None = None,
) -> list[dict]:
    """
    Search user's documents for relevant chunks using vector similarity.

    Args:
        query: Search query text
        user_id: The user's ID for RLS filtering
        top_k: Maximum number of results
        threshold: Minimum similarity threshold
        metadata_filter: Optional JSONB filter for @> containment (e.g. {"document_type": "meeting_notes"})

    Returns:
        List of matching chunks with similarity scores
    """
    query_embedding = await get_embeddings([query], user_id=user_id)

    # Convert embedding list to pgvector string format "[0.1,0.2,...]"
    # PostgREST cannot cast a JSON array to the pgvector `vector` type directly.
    embedding_str = "[" + ",".join(str(x) for x in query_embedding[0]) + "]"

    supabase = get_supabase_client()
    rpc_params = {
        "query_embedding": embedding_str,
        "match_threshold": threshold,
        "match_count": top_k,
        "p_user_id": user_id,
    }
    if metadata_filter:
        rpc_params["p_metadata_filter"] = metadata_filter

    result = supabase.rpc("match_chunks", rpc_params).execute()

    return result.data or []
