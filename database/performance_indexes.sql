-- Performance Optimization Indexes for Serbian Vocabulary App
-- These indexes will significantly improve query performance
-- Run this script after the main init.sql

-- Critical missing indexes identified in performance analysis

-- User vocabulary optimizations (most critical)
CREATE INDEX IF NOT EXISTS idx_user_vocabulary_user_id ON user_vocabulary(user_id);
CREATE INDEX IF NOT EXISTS idx_user_vocabulary_mastery ON user_vocabulary(user_id, mastery_level);
CREATE INDEX IF NOT EXISTS idx_user_vocabulary_last_practiced ON user_vocabulary(last_practiced);
CREATE INDEX IF NOT EXISTS idx_user_vocabulary_user_word ON user_vocabulary(user_id, word_id);

-- Words table optimizations
CREATE INDEX IF NOT EXISTS idx_words_is_top_100 ON words(is_top_100, category_id);
CREATE INDEX IF NOT EXISTS idx_words_difficulty ON words(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_words_english_translation ON words(english_translation);
CREATE INDEX IF NOT EXISTS idx_words_created_at ON words(created_at);

-- Practice session optimizations (missing user_id foreign key in schema)
-- Note: Need to add user_id column to practice_sessions table first
-- ALTER TABLE practice_sessions ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
-- CREATE INDEX IF NOT EXISTS idx_practice_sessions_user_date ON practice_sessions(user_id, session_date);

-- Practice results optimizations
CREATE INDEX IF NOT EXISTS idx_practice_results_created_at ON practice_results(created_at);
CREATE INDEX IF NOT EXISTS idx_practice_results_was_correct ON practice_results(was_correct);

-- Categories optimization (for frequent lookups)
CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_words_category_top100 ON words(category_id, is_top_100);
CREATE INDEX IF NOT EXISTS idx_user_vocab_mastery_practiced ON user_vocabulary(user_id, mastery_level, last_practiced);

-- Performance statistics
-- Check index usage with these queries:
-- SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
-- FROM pg_stat_user_indexes ORDER BY idx_scan DESC;

-- Check table sizes:
-- SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
-- FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
