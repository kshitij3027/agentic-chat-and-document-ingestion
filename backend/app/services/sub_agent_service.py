"""Sub-agent service for in-depth document analysis."""
import logging
from typing import AsyncGenerator

from app.services.document_service import get_full_document_content
from app.services.llm_service import get_global_llm_settings
from app.services.langsmith import get_traced_async_openai_client

logger = logging.getLogger(__name__)

_SUB_AGENT_SYSTEM_PROMPT = """You are a document analysis specialist. Your task is to analyze the provided \
document content and answer the user's question about it.

You have access to the FULL content of a single document. Provide thorough, \
detailed analysis based on what you find in the document.

Guidelines:
- Base your analysis solely on the document content provided
- Be specific and cite relevant sections when appropriate
- If the document doesn't contain information to answer the question, say so clearly
- Structure your response clearly with headings if appropriate for longer analyses"""


async def run_sub_agent(
    document_id: str,
    user_id: str,
    user_query: str,
) -> AsyncGenerator[dict, None]:
    """
    Run a sub-agent that analyzes a full document.

    Yields SSE-compatible event dicts:
      sub_agent_start, sub_agent_reasoning, sub_agent_complete, sub_agent_error
    """
    # Retrieve and validate document
    try:
        doc_info = await get_full_document_content(document_id, user_id)
    except Exception as e:
        logger.error(f"Failed to retrieve document {document_id}: {e}")
        yield {"type": "sub_agent_error", "error": f"Failed to retrieve document: {e}"}
        return

    if doc_info is None:
        yield {"type": "sub_agent_error", "error": "Document not found or access denied."}
        return

    if not doc_info["fits_context"]:
        yield {
            "type": "sub_agent_error",
            "error": f"Document is too large for analysis ({doc_info['token_count']:,} tokens). Maximum is 100,000 tokens.",
        }
        return

    # Signal start
    yield {
        "type": "sub_agent_start",
        "document_id": doc_info["id"],
        "filename": doc_info["filename"],
        "token_count": doc_info["token_count"],
    }

    # Build messages for the sub-agent
    messages = [
        {"role": "system", "content": _SUB_AGENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Document: {doc_info['filename']}\n\n{doc_info['content']}\n\n---\n\nQuestion: {user_query}",
        },
    ]

    # Stream LLM response
    try:
        llm_settings = get_global_llm_settings()
        client = get_traced_async_openai_client(
            base_url=llm_settings["base_url"],
            api_key=llm_settings["api_key"],
        )

        stream = await client.chat.completions.create(
            model=llm_settings["model"],
            messages=messages,
            stream=True,
        )

        full_result = ""
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                full_result += delta.content
                yield {"type": "sub_agent_reasoning", "content": delta.content}

        yield {"type": "sub_agent_complete", "result": full_result}

    except Exception as e:
        logger.error(f"Sub-agent LLM error: {e}")
        yield {"type": "sub_agent_error", "error": str(e)}
