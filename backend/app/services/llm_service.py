"""LLM service using ChatCompletions API with provider abstraction."""
from typing import AsyncGenerator, Any

from fastapi import HTTPException, status
from postgrest.exceptions import APIError

from app.db.supabase import get_supabase_client
from app.services.langsmith import get_traced_async_openai_client
from app.routers.settings import decrypt_value

SYSTEM_PROMPT = """You are a helpful assistant for the RAG Masterclass application.
You can answer questions and help users with their queries.
When relevant, search through the uploaded documents to provide accurate information.
Always cite your sources when using information from documents.

You have optional filters on the search tool: document_type and topic. ONLY use them when the user
explicitly names a document type (e.g., "search my meeting notes", "look in my tutorials", "check my reports").
For general questions like "what do my documents say about X", do NOT use filters — let vector similarity
find the best matches across all documents.
Available document_type values: meeting_notes, technical_doc, tutorial, report, email, notes, article, other."""

RAG_TOOLS = [{
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": "Search the user's uploaded documents for relevant information. Use this when the user asks questions that might be answered by their documents. You can optionally filter by document_type or topic to narrow results.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant document content"
                },
                "document_type": {
                    "type": "string",
                    "description": "Filter by document type. One of: meeting_notes, technical_doc, tutorial, report, email, notes, article, other",
                    "enum": ["meeting_notes", "technical_doc", "tutorial", "report", "email", "notes", "article", "other"]
                },
                "topic": {
                    "type": "string",
                    "description": "Filter by topic (e.g., 'Kubernetes deployment', 'Q4 financials')"
                }
            },
            "required": ["query"]
        }
    }
}]


def get_global_llm_settings() -> dict[str, Any]:
    """
    Get global LLM settings from the global_settings table.

    Returns dict with keys: model, base_url, api_key
    Raises HTTPException(503) if no API key is configured.
    """
    supabase = get_supabase_client()
    try:
        result = supabase.table("global_settings").select(
            "llm_model, llm_base_url, llm_api_key"
        ).limit(1).maybe_single().execute()
        data = result.data if result else None
    except APIError:
        data = None

    api_key = decrypt_value(data.get("llm_api_key")) if data else None
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM not configured. An admin must configure LLM settings."
        )

    return {
        "model": data.get("llm_model") or "gpt-4o",
        "base_url": data.get("llm_base_url") or None,
        "api_key": api_key,
    }


async def astream_chat_response(
    messages: list[dict],
    tools: list[dict] | None = None,
    user_id: str | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Stream a chat response using the ChatCompletions API.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        tools: Optional list of tool definitions for function calling
        user_id: Unused, kept for API compatibility

    Yields:
        Event dicts with 'type' and additional data
    """
    llm_settings = get_global_llm_settings()
    model = llm_settings["model"]
    client = get_traced_async_openai_client(
        base_url=llm_settings["base_url"],
        api_key=llm_settings["api_key"],
    )

    request_kwargs: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *messages],
        "stream": True,
    }
    if tools:
        request_kwargs["tools"] = tools

    try:
        stream = await client.chat.completions.create(**request_kwargs)

        full_response = ""
        tool_calls_buffer: dict[int, dict] = {}

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            finish_reason = chunk.choices[0].finish_reason if chunk.choices else None

            if delta and delta.content:
                full_response += delta.content
                yield {"type": "text_delta", "content": delta.content}

            if delta and delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_buffer:
                        tool_calls_buffer[idx] = {
                            "id": tc.id,
                            "name": tc.function.name if tc.function else None,
                            "arguments": "",
                        }
                    else:
                        if tc.id:
                            tool_calls_buffer[idx]["id"] = tc.id
                        if tc.function and tc.function.name:
                            tool_calls_buffer[idx]["name"] = tc.function.name
                    if tc.function and tc.function.arguments:
                        tool_calls_buffer[idx]["arguments"] += tc.function.arguments

            if finish_reason == "tool_calls":
                yield {"type": "tool_calls", "tool_calls": list(tool_calls_buffer.values())}

            if finish_reason == "stop":
                yield {"type": "response_completed", "content": full_response}

    except HTTPException:
        raise
    except Exception as e:
        yield {"type": "error", "error": str(e)}
