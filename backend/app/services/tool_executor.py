"""Tool execution dispatcher."""
import json
import logging
from app.services.retrieval_service import search_documents

logger = logging.getLogger(__name__)


async def execute_tool_call(tool_call: dict, user_id: str) -> str:
    """
    Execute a tool call and return the result as a string.

    Args:
        tool_call: Dict with 'name' and 'arguments' keys
        user_id: The user's ID for context

    Returns:
        Tool result as a string
    """
    name = tool_call["name"]
    arguments = json.loads(tool_call["arguments"])

    if name == "search_documents":
        query = arguments.get("query", "")
        results = await search_documents(query, user_id)

        if not results:
            return "No relevant documents found."

        # Format results for LLM context
        formatted = []
        for r in results:
            formatted.append(
                f"[Source: {r.get('metadata', {}).get('filename', 'unknown')}] "
                f"(similarity: {r['similarity']:.2f})\n{r['content']}"
            )

        return "\n\n---\n\n".join(formatted)

    logger.warning(f"Unknown tool: {name}")
    return f"Error: Unknown tool '{name}'"
