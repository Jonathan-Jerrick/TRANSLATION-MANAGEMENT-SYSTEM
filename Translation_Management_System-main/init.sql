-- Initialize TMS Database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_segments_project_id ON segments(project_id);
CREATE INDEX IF NOT EXISTS idx_tm_entries_source_target ON translation_memory(source_locale, target_locale);
CREATE INDEX IF NOT EXISTS idx_tm_entries_text_search ON translation_memory USING gin(to_tsvector('english', source_text));

-- Create full-text search indexes
CREATE INDEX IF NOT EXISTS idx_projects_name_search ON projects USING gin(to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_segments_source_search ON segments USING gin(to_tsvector('english', source_text));
