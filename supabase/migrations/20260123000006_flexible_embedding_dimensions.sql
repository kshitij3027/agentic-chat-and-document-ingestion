-- Allow flexible embedding dimensions instead of hardcoded 1536
-- This enables users to configure different embedding models with varying dimensions

-- 1. Drop the existing index (it depends on the column type)
DROP INDEX IF EXISTS idx_chunks_embedding;

-- 2. Alter the column to use flexible vector type (no dimension constraint)
ALTER TABLE chunks ALTER COLUMN embedding TYPE vector USING embedding::vector;

-- 3. Recreate the match_chunks function with flexible vector parameter
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding vector,
    match_threshold float,
    match_count int,
    p_user_id uuid
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
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 4. Vector indexes require fixed dimensions, so we skip index creation here.
-- For production with high query volume, standardize on a dimension and add:
-- CREATE INDEX idx_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops);
-- Queries will still work via sequential scan, which is fine for moderate data sizes.
