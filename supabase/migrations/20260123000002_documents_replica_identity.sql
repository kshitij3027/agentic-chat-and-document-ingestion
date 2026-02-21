-- Enable full replica identity on documents table
-- This ensures DELETE events include all columns in the old record,
-- allowing Supabase Realtime filters (like user_id=eq.xxx) to work for DELETE events.
ALTER TABLE documents REPLICA IDENTITY FULL;
