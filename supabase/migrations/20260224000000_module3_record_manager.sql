-- Module 3: Record Manager
-- Add content hashing for duplicate detection and document replacement

ALTER TABLE documents ADD COLUMN content_hash TEXT;

CREATE INDEX idx_documents_user_filename ON documents(user_id, filename);
