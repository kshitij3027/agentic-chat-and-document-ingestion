-- Module 6: Hybrid Search & Reranking
-- Adds full-text search (tsvector/tsquery) alongside existing vector search

-- 1. Add tsvector column to chunks
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- 2. Create GIN index for full-text search
CREATE INDEX IF NOT EXISTS idx_chunks_search_vector ON chunks USING GIN (search_vector);

-- 3. Create trigger to auto-populate search_vector on INSERT/UPDATE
CREATE OR REPLACE FUNCTION chunks_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_chunks_search_vector ON chunks;
CREATE TRIGGER trg_chunks_search_vector
    BEFORE INSERT OR UPDATE OF content ON chunks
    FOR EACH ROW EXECUTE FUNCTION chunks_search_vector_update();

-- 4. Backfill existing rows
UPDATE chunks SET search_vector = to_tsvector('english', COALESCE(content, ''))
WHERE search_vector IS NULL;

-- 5. Create keyword_search_chunks RPC function
CREATE OR REPLACE FUNCTION keyword_search_chunks(
    p_query text,
    p_match_count int,
    p_user_id uuid,
    p_metadata_filter jsonb DEFAULT NULL
) RETURNS TABLE (
    id uuid, document_id uuid, content text,
    chunk_index int, metadata jsonb, rank float
) LANGUAGE plpgsql AS $$
DECLARE
    tsq tsquery;
BEGIN
    tsq := websearch_to_tsquery('english', p_query);

    -- Return empty if query produces no tsquery tokens
    IF tsq IS NULL OR tsq = ''::tsquery THEN
        RETURN;
    END IF;

    RETURN QUERY
    SELECT c.id, c.document_id, c.content, c.chunk_index, c.metadata,
           ts_rank_cd(c.search_vector, tsq)::float AS rank
    FROM chunks c
    WHERE c.user_id = p_user_id
      AND c.search_vector @@ tsq
      AND (p_metadata_filter IS NULL OR c.metadata @> p_metadata_filter)
    ORDER BY rank DESC
    LIMIT p_match_count;
END;
$$;

-- 6. Add reranker settings columns to global_settings
ALTER TABLE global_settings ADD COLUMN IF NOT EXISTS reranker_api_key TEXT;
ALTER TABLE global_settings ADD COLUMN IF NOT EXISTS reranker_model TEXT;
