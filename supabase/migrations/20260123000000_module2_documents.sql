CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    storage_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_chunks_user_id ON chunks(user_id);
CREATE INDEX idx_chunks_embedding ON chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- RLS
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_own_documents" ON documents FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "users_own_chunks" ON chunks FOR ALL USING (auth.uid() = user_id);

-- Realtime for ingestion status
ALTER PUBLICATION supabase_realtime ADD TABLE documents;

-- Vector search function
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding vector(1536),
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
