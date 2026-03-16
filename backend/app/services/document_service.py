"""Document content retrieval for sub-agent analysis."""
import logging

from app.db.supabase import get_supabase_client
from app.services.token_service import estimate_tokens, can_fit_in_context

logger = logging.getLogger(__name__)


async def get_full_document_content(
    document_id: str,
    user_id: str,
    max_tokens: int = 100_000,
) -> dict | None:
    """
    Fetch and reassemble a full document from its chunks.

    Returns dict with {id, filename, content, token_count, chunk_count, metadata, fits_context}
    or None if document not found / not owned / not completed.
    """
    supabase = get_supabase_client()

    # Fetch document with ownership check
    result = supabase.table("documents").select("*").eq(
        "id", document_id
    ).eq("user_id", user_id).limit(1).execute()

    if not result.data:
        logger.warning(f"Document {document_id} not found for user {user_id}")
        return None

    doc = result.data[0]

    if doc["status"] != "completed":
        logger.warning(f"Document {document_id} status is '{doc['status']}', not completed")
        return None

    # Fetch chunks ordered by index
    chunks_result = supabase.table("chunks").select(
        "content, chunk_index"
    ).eq("document_id", document_id).order("chunk_index").execute()

    if not chunks_result.data:
        logger.warning(f"Document {document_id} has no chunks")
        return None

    content = "\n\n---\n\n".join(chunk["content"] for chunk in chunks_result.data)
    token_count = estimate_tokens(content)

    return {
        "id": doc["id"],
        "filename": doc["filename"],
        "content": content,
        "token_count": token_count,
        "chunk_count": len(chunks_result.data),
        "metadata": doc.get("metadata"),
        "fits_context": can_fit_in_context(content, max_tokens),
    }
