-- Drop OpenAI Assistants API columns
-- These columns were used by the old Assistants API but are no longer needed.
-- The app now uses the stateless Responses API and manages conversation history directly.
-- This migration cleans up any existing data from earlier deployments.

ALTER TABLE threads
DROP COLUMN IF EXISTS openai_thread_id;

ALTER TABLE messages
DROP COLUMN IF EXISTS openai_message_id;
