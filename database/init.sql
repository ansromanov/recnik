-- Create categories table
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create words table
CREATE TABLE words (
    id SERIAL PRIMARY KEY,
    serbian_word VARCHAR(255) NOT NULL,
    english_translation VARCHAR(255) NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    context TEXT,
    notes TEXT,
    difficulty_level INTEGER DEFAULT 1 CHECK (difficulty_level >= 1 AND difficulty_level <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(serbian_word, english_translation)
);

-- Create user_vocabulary table to track user's learned words
CREATE TABLE user_vocabulary (
    id SERIAL PRIMARY KEY,
    word_id INTEGER REFERENCES words(id) ON DELETE CASCADE,
    times_practiced INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    last_practiced TIMESTAMP,
    mastery_level INTEGER DEFAULT 0 CHECK (mastery_level >= 0 AND mastery_level <= 100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(word_id)
);

-- Create practice_sessions table
CREATE TABLE practice_sessions (
    id SERIAL PRIMARY KEY,
    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    duration_seconds INTEGER
);

-- Create practice_results table
CREATE TABLE practice_results (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES practice_sessions(id) ON DELETE CASCADE,
    word_id INTEGER REFERENCES words(id) ON DELETE CASCADE,
    was_correct BOOLEAN NOT NULL,
    response_time_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default categories
INSERT INTO categories (name, description) VALUES 
    ('Common Words', 'Frequently used everyday words'),
    ('Verbs', 'Action words'),
    ('Nouns', 'People, places, things'),
    ('Adjectives', 'Descriptive words'),
    ('Food & Drink', 'Food and beverage related vocabulary'),
    ('Numbers', 'Numbers and counting'),
    ('Time', 'Time-related expressions'),
    ('Family', 'Family and relationships'),
    ('Colors', 'Color vocabulary'),
    ('Greetings', 'Common greetings and phrases');

-- Create indexes for better performance
CREATE INDEX idx_words_serbian ON words(serbian_word);
CREATE INDEX idx_words_category ON words(category_id);
CREATE INDEX idx_user_vocab_word ON user_vocabulary(word_id);
CREATE INDEX idx_practice_results_session ON practice_results(session_id);
CREATE INDEX idx_practice_results_word ON practice_results(word_id);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_words_updated_at BEFORE UPDATE ON words
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
