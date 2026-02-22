"""Hybrid search: vector + keyword with RRF fusion and optional reranking."""
import logging

from app.db.supabase import get_supabase_client
from app.services.embedding_service import get_embeddings
from app.services.reranker_service import rerank_results

logger = logging.getLogger(__name__)


async def vector_search(
    query: str,
    user_id: str,
    top_k: int,
    threshold: float,
    metadata_filter: dict | None = None,
) -> list[dict]:
    """Search via cosine similarity using match_chunks RPC."""
    query_embedding = await get_embeddings([query], user_id=user_id)
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


async def keyword_search(
    query: str,
    user_id: str,
    top_k: int,
    metadata_filter: dict | None = None,
) -> list[dict]:
    """Search via Postgres full-text search using keyword_search_chunks RPC."""
    supabase = get_supabase_client()
    rpc_params = {
        "p_query": query,
        "p_match_count": top_k,
        "p_user_id": user_id,
    }
    if metadata_filter:
        rpc_params["p_metadata_filter"] = metadata_filter

    result = supabase.rpc("keyword_search_chunks", rpc_params).execute()
    return result.data or []


def reciprocal_rank_fusion(
    result_lists: list[list[dict]],
    id_key: str = "id",
    k: int = 60,
) -> list[dict]:
    """Combine multiple ranked result lists using Reciprocal Rank Fusion.

    RRF score for each document = sum(1 / (k + rank)) across all lists
    where rank is 1-based position in each list.
    """
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}

    for result_list in result_lists:
        for rank, doc in enumerate(result_list, start=1):
            doc_id = doc[id_key]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
            if doc_id not in docs:
                docs[doc_id] = doc

    sorted_ids = sorted(scores, key=lambda did: scores[did], reverse=True)
    return [{**docs[did], "rrf_score": round(scores[did], 6)} for did in sorted_ids]


async def search_documents(
    query: str,
    user_id: str,
    top_k: int = 5,
    threshold: float = 0.3,
    metadata_filter: dict | None = None,
) -> list[dict]:
    """Hybrid search: vector + keyword with RRF fusion and optional reranking.

    Same signature as the original vector-only search_documents.
    """
    candidate_count = 3 * top_k

    # Run both searches -- each wrapped so one failing doesn't kill the other
    try:
        vector_results = await vector_search(
            query, user_id, candidate_count, threshold, metadata_filter
        )
    except Exception as e:
        logger.warning(f"Vector search failed, continuing with keyword only: {e}")
        vector_results = []

    try:
        kw_results = await keyword_search(
            query, user_id, candidate_count, metadata_filter
        )
    except Exception as e:
        logger.warning(f"Keyword search failed, continuing with vector only: {e}")
        kw_results = []

    logger.info(
        f"Hybrid search: {len(vector_results)} vector results, "
        f"{len(kw_results)} keyword results"
    )

    # Fuse results
    if vector_results and kw_results:
        fused = reciprocal_rank_fusion([vector_results, kw_results])
    elif vector_results:
        fused = [{**r, "rrf_score": r.get("similarity", 0.0)} for r in vector_results]
    elif kw_results:
        fused = [{**r, "rrf_score": r.get("rank", 0.0)} for r in kw_results]
    else:
        return []

    logger.info(
        f"RRF fusion: {len(fused)} unique candidates from "
        f"{len(vector_results)} vector + {len(kw_results)} keyword"
    )

    # Rerank (no-op if reranker not configured)
    reranked = await rerank_results(query, fused, top_n=top_k)

    logger.info(f"Final results: {len(reranked[:top_k])} chunks returned")

    return reranked[:top_k]
