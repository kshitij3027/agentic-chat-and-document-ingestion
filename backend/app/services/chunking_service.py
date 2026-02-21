"""Recursive character text splitter - no external dependencies."""


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: list[str] | None = None,
) -> list[str]:
    """
    Split text into chunks using recursive character splitting.

    Args:
        text: The text to split
        chunk_size: Maximum characters per chunk
        chunk_overlap: Overlap between chunks
        separators: List of separators to try, in order

    Returns:
        List of text chunks
    """
    if separators is None:
        separators = ["\n\n", "\n", ". ", " "]

    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    # Find the best separator
    separator = separators[-1]
    for sep in separators:
        if sep in text:
            separator = sep
            break

    # Split by the chosen separator
    splits = text.split(separator)

    # Merge splits into chunks
    chunks = []
    current_chunk = ""

    for split in splits:
        piece = split if not current_chunk else separator + split

        if len(current_chunk) + len(piece) <= chunk_size:
            current_chunk += piece
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            # Start new chunk with overlap from previous
            if chunk_overlap > 0 and current_chunk:
                overlap_text = current_chunk[-chunk_overlap:]
                current_chunk = overlap_text + separator + split
            else:
                current_chunk = split

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Recursively split any chunks that are still too large
    final_chunks = []
    remaining_separators = separators[separators.index(separator) + 1:] if separator in separators else []

    for chunk in chunks:
        if len(chunk) > chunk_size and remaining_separators:
            final_chunks.extend(chunk_text(chunk, chunk_size, chunk_overlap, remaining_separators))
        else:
            final_chunks.append(chunk)

    return final_chunks
