-- Create sql_reader role and grant minimal privileges for Text-to-SQL tool
-- The backend connects as postgres via the pooler, then SET ROLE sql_reader
-- to restrict queries to SELECT-only on sales_data.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sql_reader') THEN
        CREATE ROLE sql_reader NOLOGIN;
    END IF;
END
$$;

-- Allow postgres to assume the sql_reader role
GRANT sql_reader TO postgres;

-- sql_reader can only SELECT from sales_data
GRANT USAGE ON SCHEMA public TO sql_reader;
GRANT SELECT ON sales_data TO sql_reader;
