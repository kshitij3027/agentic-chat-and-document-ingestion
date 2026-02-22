-- Drop the old 4-param match_chunks overload from the flexible_embedding_dimensions migration.
-- The 5-param version (with p_metadata_filter DEFAULT NULL) from module4_metadata handles both
-- filtered and unfiltered searches. Keeping both causes PostgREST PGRST203 ambiguity errors
-- when calling with only 4 params.
DROP FUNCTION IF EXISTS match_chunks(vector, float, int, uuid);
