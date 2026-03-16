"""Token counting utilities using tiktoken."""
import logging

import tiktoken

logger = logging.getLogger(__name__)


def estimate_tokens(text: str, model: str = "gpt-4o") -> int:
    """Estimate token count for a text string."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def can_fit_in_context(text: str, max_tokens: int = 100_000) -> bool:
    """Check if text fits within the given token limit."""
    return estimate_tokens(text) <= max_tokens
