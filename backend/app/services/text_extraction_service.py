"""Text extraction and element-based partitioning for multiple document formats."""
import io
import logging

logger = logging.getLogger(__name__)


def partition_document(file_bytes: bytes, file_type: str):
    """
    Partition a document into structural elements based on file type.

    Returns a list of unstructured Elements for rich formats (PDF, DOCX, HTML),
    or None for plain text formats (signals caller to use existing text pipeline).
    """
    if file_type in ("text/plain", "text/markdown"):
        return None

    if file_type == "application/pdf":
        from unstructured.partition.pdf import partition_pdf
        return partition_pdf(file=io.BytesIO(file_bytes), strategy="fast")

    if file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        from unstructured.partition.docx import partition_docx
        return partition_docx(file=io.BytesIO(file_bytes))

    if file_type == "text/html":
        from unstructured.partition.html import partition_html
        return partition_html(file=io.BytesIO(file_bytes))

    return None


def chunk_elements(elements, max_characters: int = 1000, overlap: int = 200) -> list[str]:
    """
    Chunk structural elements by title/section boundaries.

    Uses unstructured's chunk_by_title for section-aware splitting
    instead of naive character-based chunking.
    """
    from unstructured.chunking.title import chunk_by_title

    chunked = chunk_by_title(
        elements,
        max_characters=max_characters,
        overlap=overlap,
        combine_text_under_n_chars=200,
    )
    return [str(chunk) for chunk in chunked]


def extract_text(file_bytes: bytes, file_type: str) -> str:
    """Extract plain text from file bytes (for .txt and .md formats)."""
    if file_type in ("text/plain", "text/markdown"):
        return file_bytes.decode("utf-8")

    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError(f"Unsupported file type: {file_type}")
