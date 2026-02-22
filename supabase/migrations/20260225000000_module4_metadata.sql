-- Module 4: Metadata extraction support
-- Adds metadata JSONB columns and GIN indexes for containment filtering

-- 1. Add metadata column to documents table
ALTER TABLE documents ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT NULL;

-- 2. Create GIN indexes for @> containment queries
CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON chunks USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN (metadata);

-- 3. Replace match_chunks function with optional metadata filter
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding vector,
    match_threshold float,
    match_count int,
    p_user_id uuid,
    p_metadata_filter jsonb DEFAULT NULL
) RETURNS TABLE (
    id uuid, document_id uuid, content text,
    chunk_index int, metadata jsonb, similarity float
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.document_id, c.content, c.chunk_index, c.metadata,
           1 - (c.embedding <=> query_embedding) AS similarity
    FROM chunks c
    WHERE c.user_id = p_user_id
      AND 1 - (c.embedding <=> query_embedding) > match_threshold
      AND (p_metadata_filter IS NULL OR c.metadata @> p_metadata_filter)
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
