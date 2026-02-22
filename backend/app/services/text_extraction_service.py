"""Text extraction and structure-aware chunking for multiple document formats.

Uses pure Python libraries (pdfminer.six, python-docx, beautifulsoup4) —
no heavy ML/vision dependencies required.
"""
import io
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DocumentElement:
    """A structural element extracted from a document."""
    text: str
    element_type: str  # "title", "heading", "paragraph", "list_item"


# ── Extraction ────────────────────────────────────────────────────────


def partition_document(file_bytes: bytes, file_type: str) -> list[DocumentElement] | None:
    """
    Partition a document into structural elements based on file type.

    Returns a list of DocumentElements for rich formats (PDF, DOCX, HTML),
    or None for plain text formats (signals caller to use existing text pipeline).
    """
    if file_type in ("text/plain", "text/markdown"):
        return None

    if file_type == "application/pdf":
        return _extract_pdf(file_bytes)

    if file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return _extract_docx(file_bytes)

    if file_type == "text/html":
        return _extract_html(file_bytes)

    return None


def _extract_pdf(file_bytes: bytes) -> list[DocumentElement]:
    """Extract structural elements from a PDF using pdfminer.six."""
    from pdfminer.high_level import extract_text

    full_text = extract_text(io.BytesIO(file_bytes))
    if not full_text.strip():
        return []

    elements = []
    for para in _split_paragraphs(full_text):
        if _looks_like_heading(para):
            elements.append(DocumentElement(text=para, element_type="heading"))
        else:
            elements.append(DocumentElement(text=para, element_type="paragraph"))
    return elements


def _extract_docx(file_bytes: bytes) -> list[DocumentElement]:
    """Extract structural elements from a DOCX using python-docx."""
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    elements = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        if para.style and para.style.name and para.style.name.startswith("Heading"):
            elements.append(DocumentElement(text=text, element_type="heading"))
        elif para.style and para.style.name and para.style.name.startswith("List"):
            elements.append(DocumentElement(text=text, element_type="list_item"))
        else:
            elements.append(DocumentElement(text=text, element_type="paragraph"))
    return elements


def _extract_html(file_bytes: bytes) -> list[DocumentElement]:
    """Extract structural elements from HTML using BeautifulSoup."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(file_bytes, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    elements = []
    heading_tags = {"h1", "h2", "h3", "h4", "h5", "h6"}

    for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"]):
        text = element.get_text(strip=True)
        if not text:
            continue
        if element.name in heading_tags:
            elements.append(DocumentElement(text=text, element_type="heading"))
        elif element.name == "li":
            elements.append(DocumentElement(text=text, element_type="list_item"))
        else:
            elements.append(DocumentElement(text=text, element_type="paragraph"))
    return elements


# ── Chunking ──────────────────────────────────────────────────────────


def chunk_elements(
    elements: list[DocumentElement],
    max_characters: int = 1000,
    overlap: int = 200,
) -> list[str]:
    """
    Chunk structural elements respecting section boundaries.

    Groups content under headings into sections, then splits sections
    into chunks that fit within max_characters with overlap.
    """
    if not elements:
        return []

    # Group elements into sections (each section starts with a heading)
    sections = _group_into_sections(elements)

    # Build chunks from sections
    chunks = []
    for section in sections:
        section_text = "\n\n".join(
            el.text for el in section
        )

        if len(section_text) <= max_characters:
            chunks.append(section_text)
        else:
            # Section too large — split by paragraphs with overlap
            chunks.extend(
                _split_section(section, max_characters, overlap)
            )

    return [c for c in chunks if c.strip()]


def _group_into_sections(elements: list[DocumentElement]) -> list[list[DocumentElement]]:
    """Group elements into sections. Each heading starts a new section."""
    sections: list[list[DocumentElement]] = []
    current: list[DocumentElement] = []

    for el in elements:
        if el.element_type == "heading" and current:
            sections.append(current)
            current = []
        current.append(el)

    if current:
        sections.append(current)

    return sections


def _split_section(
    section: list[DocumentElement],
    max_characters: int,
    overlap: int,
) -> list[str]:
    """Split an oversized section into chunks with overlap."""
    chunks = []
    current_parts: list[str] = []
    current_len = 0

    for el in section:
        piece_len = len(el.text) + (2 if current_parts else 0)  # +2 for "\n\n" separator

        if current_len + piece_len > max_characters and current_parts:
            chunk_text = "\n\n".join(current_parts)
            chunks.append(chunk_text)

            # Start new chunk with overlap from the end of the previous
            overlap_text = chunk_text[-overlap:] if overlap > 0 else ""
            current_parts = [overlap_text] if overlap_text else []
            current_len = len(overlap_text)

        current_parts.append(el.text)
        current_len += piece_len

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return chunks


# ── Helpers ───────────────────────────────────────────────────────────


def _split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs by blank lines."""
    paragraphs = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _looks_like_heading(text: str) -> bool:
    """Heuristic: short lines without ending punctuation are likely headings."""
    text = text.strip()
    if not text:
        return False
    if len(text) > 100:
        return False
    if text[-1] in ".,:;!?)":
        return False
    if "\n" in text:
        return False
    return True


def extract_text(file_bytes: bytes, file_type: str) -> str:
    """Extract plain text from file bytes (for .txt and .md formats)."""
    if file_type in ("text/plain", "text/markdown"):
        return file_bytes.decode("utf-8")

    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError(f"Unsupported file type: {file_type}")
