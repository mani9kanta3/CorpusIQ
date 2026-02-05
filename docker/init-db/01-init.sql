-- =============================================================================
-- DocuMind Database Initialization
-- =============================================================================
-- This script runs automatically when PostgreSQL container starts for the first time.
-- It sets up necessary extensions and initial configurations.

-- Enable UUID generation (for document/user IDs)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable full-text search (for document content search)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable vector operations (if using pgvector instead of Qdrant)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Create audit log function for tracking changes
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Grant all privileges to documind user (safety check)
GRANT ALL PRIVILEGES ON DATABASE documind TO documind;
