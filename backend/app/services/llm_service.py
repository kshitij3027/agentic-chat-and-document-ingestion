"""LLM service using ChatCompletions API with provider abstraction."""
from typing import AsyncGenerator, Any

from fastapi import HTTPException, status
from postgrest.exceptions import APIError

from app.db.supabase import get_supabase_client
from app.services.langsmith import get_traced_async_openai_client
from app.routers.settings import decrypt_value

_BASE_SYSTEM_PROMPT = """You are a helpful assistant for the RAG Masterclass application.
You can answer questions and help users with their queries.
When relevant, search through the uploaded documents to provide accurate information.
Always cite your sources when using information from documents.

You have optional filters on the search tool: document_type and topic. ONLY use them when the user
explicitly names a document type (e.g., "search my meeting notes", "look in my tutorials", "check my reports").
For general questions like "what do my documents say about X", do NOT use filters — let vector similarity
find the best matches across all documents.
Available document_type values: meeting_notes, technical_doc, tutorial, report, email, notes, article, other."""


def get_system_prompt(include_sql: bool = False, include_web_search: bool = False) -> str:
    parts = [_BASE_SYSTEM_PROMPT]

    if include_sql:
        from app.services.sql_agent_service import SALES_DATA_SCHEMA
        parts.append(f"""
You also have access to a SQL database with structured sales data. Use the query_sales_database tool
to answer questions about orders, revenue, customers, products, and regions.
Write standard PostgreSQL queries. Only SELECT queries are allowed.

{SALES_DATA_SCHEMA}""")

    if include_web_search:
        parts.append("""
You also have access to web search. Use the web_search tool when the user's question cannot be
answered from their uploaded documents, or when they explicitly ask for current/online information.
Always cite the URLs from search results in your response.""")

    parts.append("\nYou have up to 10 tool-calling rounds.")
    return "\n".join(parts)


_SEARCH_DOCUMENTS_TOOL = {
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
}

_QUERY_SQL_TOOL = {
    "type": "function",
    "function": {
        "name": "query_sales_database",
        "description": "Query the sales database using SQL. Use this for questions about orders, revenue, customers, products, categories, and regions. Write a PostgreSQL SELECT query.",
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "A PostgreSQL SELECT query to run against the sales_data table"
                }
            },
            "required": ["sql"]
        }
    }
}

_WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for current information. Use this when the user's documents don't contain the answer, or when they ask about recent events or online information.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
}


def build_rag_tools(
    include_search: bool = True,
    include_sql: bool = False,
    include_web_search: bool = False,
) -> list[dict] | None:
    tools = []
    if include_search:
        tools.append(_SEARCH_DOCUMENTS_TOOL)
    if include_sql:
        tools.append(_QUERY_SQL_TOOL)
    if include_web_search:
        tools.append(_WEB_SEARCH_TOOL)
    return tools if tools else None


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
    system_prompt: str | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Stream a chat response using the ChatCompletions API.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        tools: Optional list of tool definitions for function calling
        user_id: Unused, kept for API compatibility
        system_prompt: Optional system prompt override; defaults to _BASE_SYSTEM_PROMPT

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
        "messages": [{"role": "system", "content": system_prompt or _BASE_SYSTEM_PROMPT}, *messages],
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
