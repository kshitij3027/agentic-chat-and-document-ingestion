"""LLM-based metadata extraction for documents."""
import json
import logging
import re

from pydantic import BaseModel

from app.services.langsmith import get_traced_async_openai_client
from app.services.llm_service import get_global_llm_settings
from app.routers.settings import decrypt_value
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)

MAX_EXTRACTION_CHARS = 10_000

EXTRACTION_PROMPT = """Extract metadata from the following document. Return ONLY valid JSON with these exact fields:

{{
  "topic": "2-5 word topic description",
  "document_type": "one of: meeting_notes, technical_doc, tutorial, report, email, notes, article, other",
  "summary": "1-2 sentence summary of the document",
  "key_entities": ["up to 10 people, organizations, or technologies mentioned"],
  "language": "language of the document, e.g. english"
}}

Filename: {filename}

Document content:
{content}"""


class DocumentMetadata(BaseModel):
    topic: str
    document_type: str
    summary: str
    key_entities: list[str]
    language: str


async def extract_metadata(text: str, filename: str, user_id: str) -> DocumentMetadata | None:
    """
    Extract metadata from document text using an LLM.

    Returns None on any failure (logs error, never raises).
    Only the first 10,000 characters of text are sent to the LLM.
    """
    try:
        # Truncate to first 10K characters
        if len(text) > MAX_EXTRACTION_CHARS:
            content = text[:MAX_EXTRACTION_CHARS] + "\n\n[... remainder omitted ...]"
        else:
            content = text

        llm_settings = get_global_llm_settings()
        client = get_traced_async_openai_client(
            base_url=llm_settings["base_url"],
            api_key=llm_settings["api_key"],
        )

        response = await client.chat.completions.create(
            model=llm_settings["model"],
            messages=[{
                "role": "user",
                "content": EXTRACTION_PROMPT.format(filename=filename, content=content),
            }],
            temperature=0.0,
        )

        raw = response.choices[0].message.content or ""

        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*\n?", "", raw.strip())
        raw = re.sub(r"\n?```\s*$", "", raw.strip())

        metadata = DocumentMetadata.model_validate_json(raw)
        logger.info(f"Extracted metadata for '{filename}': topic={metadata.topic}, type={metadata.document_type}")
        return metadata

    except Exception as e:
        logger.error(f"Metadata extraction failed for '{filename}': {e}")
        return None
