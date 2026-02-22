"""Tool execution dispatcher."""
import json
import logging
from app.services.retrieval_service import search_documents

logger = logging.getLogger(__name__)


async def execute_tool_call(tool_call: dict, user_id: str) -> dict:
    """
    Execute a tool call and return text for the LLM plus source metadata.

    Args:
        tool_call: Dict with 'name' and 'arguments' keys
        user_id: The user's ID for context

    Returns:
        Dict with 'text' (str for LLM) and 'sources' (list of source docs)
    """
    name = tool_call["name"]
    arguments = json.loads(tool_call["arguments"])

    if name == "search_documents":
        query = arguments.get("query", "")
        metadata_filter = {}
        if arguments.get("document_type"):
            metadata_filter["document_type"] = arguments["document_type"]
        if arguments.get("topic"):
            metadata_filter["topic"] = arguments["topic"]

        results = await search_documents(
            query, user_id,
            metadata_filter=metadata_filter if metadata_filter else None,
        )

        if not results:
            return {"text": "No relevant documents found.", "sources": []}

        # Collect unique source documents
        sources = []
        seen = set()
        for r in results:
            doc_id = r.get("document_id", "")
            if doc_id and doc_id not in seen:
                seen.add(doc_id)
                sources.append({
                    "filename": r.get("metadata", {}).get("filename", "unknown"),
                    "document_id": doc_id,
                })

        # Format results for LLM context
        formatted = []
        for r in results:
            # Pick best available score: relevance (reranker) > rrf > similarity
            if "relevance_score" in r:
                score_label = f"relevance: {r['relevance_score']:.3f}"
            elif "rrf_score" in r:
                score_label = f"score: {r['rrf_score']:.4f}"
            else:
                score_label = f"similarity: {r['similarity']:.2f}"
            formatted.append(
                f"[Source: {r.get('metadata', {}).get('filename', 'unknown')}] "
                f"({score_label})\n{r['content']}"
            )

        return {"text": "\n\n---\n\n".join(formatted), "sources": sources}

    logger.warning(f"Unknown tool: {name}")
    return {"text": f"Error: Unknown tool '{name}'", "sources": []}
