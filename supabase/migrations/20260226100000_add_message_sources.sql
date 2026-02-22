-- Add sources column to messages table for persisting RAG source references.
-- Stores an array of {filename, document_id} objects when the assistant used document search.
ALTER TABLE messages ADD COLUMN IF NOT EXISTS sources JSONB DEFAULT NULL;
