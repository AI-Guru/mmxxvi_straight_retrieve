-- Enable pgvector extension (required by LangGraph store)
CREATE EXTENSION IF NOT EXISTS vector;

-- Note: LangGraph's AsyncPostgresStore creates its own tables automatically
-- via store.setup(). No custom table definitions needed here.
