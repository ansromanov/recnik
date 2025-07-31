const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const { Pool } = require('pg');
const OpenAI = require('openai');

// Try to load RSS parser, but don't crash if not available
let Parser;
let axios;
try {
    Parser = require('rss-parser');
    axios = require('axios');
} catch (error) {
    console.warn('RSS parser or axios not installed. News feature will use fallback articles.');
}

require('dotenv').config();

const app = express();
const port = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Database connection
const pool = new Pool({
    connectionString: process.env.DATABASE_URL
});

// OpenAI configuration
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
});

// Test database connection
pool.connect((err, client, release) => {
    if (err) {
        return console.error('Error acquiring client', err.stack);
    }
    console.log('Connected to PostgreSQL database');
    release();
});

// Routes
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', message: 'Serbian Vocabulary API is running' });
});

// Get all categories
app.get('/api/categories', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM categories ORDER BY name');
        res.json(result.rows);
    } catch (error) {
        console.error('Error fetching categories:', error);
        res.status(500).json({ error: 'Failed to fetch categories' });
    }
});

// Get all words with optional category filter
app.get('/api/words', async (req, res) => {
    try {
        const { category_id } = req.query;
        let query = `
      SELECT w.*, c.name as category_name, uv.mastery_level, uv.times_practiced
      FROM words w
      LEFT JOIN categories c ON w.category_id = c.id
      LEFT JOIN user_vocabulary uv ON w.id = uv.word_id
    `;

        if (category_id) {
            query += ' WHERE w.category_id = $1';
        }

        query += ' ORDER BY w.serbian_word';

        const result = category_id
            ? await pool.query(query, [category_id])
            : await pool.query(query);

        res.json(result.rows);
    } catch (error) {
        console.error('Error fetching words:', error);
        res.status(500).json({ error: 'Failed to fetch words' });
    }
});

// Process Serbian text and extract new words
app.post('/api/process-text', async (req, res) => {
    try {
        const { text } = req.body;

        if (!text) {
            return res.status(400).json({ error: 'Text is required' });
        }

        // Split text into words (basic tokenization for Serbian)
        const words = text
            .toLowerCase()
            .replace(/[.,!?;:'"«»()[\]{}]/g, ' ')
            .split(/\s+/)
            .filter(word => word.length > 1);

        // Get unique words
        const uniqueWords = [...new Set(words)];

        // Get available categories for categorization
        const categoriesResult = await pool.query('SELECT id, name FROM categories');
        const categories = categoriesResult.rows;
        const categoryNames = categories.map(c => c.name).join(', ');

        // First, process all words to get their infinitive forms
        const processedWords = [];
        const seenInfinitives = new Set();

        for (const word of uniqueWords.slice(0, 50)) { // Limit to 50 words per request
            try {
                const completion = await openai.chat.completions.create({
                    model: "gpt-3.5-turbo",
                    messages: [
                        {
                            role: "system",
                            content: `You are a Serbian-English translator and linguist. For the given Serbian word:
1. If it's a verb, convert it to infinitive form (e.g., "радим" → "радити", "идем" → "ићи")
2. Convert to lowercase UNLESS it's a proper noun (names of people, places, etc.)
3. Translate it to English
4. Categorize it into one of these categories: ${categoryNames}

Respond in JSON format: {"serbian_infinitive": "word in infinitive/base form", "translation": "english word", "category": "category name", "is_proper_noun": true/false}`
                        },
                        {
                            role: "user",
                            content: `Serbian word: "${word}"`
                        }
                    ],
                    temperature: 0.3,
                    max_tokens: 150
                });

                const response = completion.choices[0].message.content.trim();
                try {
                    const parsed = JSON.parse(response);
                    const category = categories.find(c => c.name.toLowerCase() === parsed.category.toLowerCase());

                    // Use the infinitive form provided by AI, or fall back to original word
                    const serbianWord = parsed.serbian_infinitive || word;

                    // Skip if we've already seen this infinitive form
                    if (seenInfinitives.has(serbianWord)) {
                        continue;
                    }
                    seenInfinitives.add(serbianWord);

                    processedWords.push({
                        serbian_word: serbianWord,
                        english_translation: parsed.translation,
                        category_id: category ? category.id : 1, // Default to "Common Words" if category not found
                        category_name: category ? category.name : 'Common Words',
                        original_form: word // Keep track of the original form found in text
                    });
                } catch (parseError) {
                    // Fallback if JSON parsing fails
                    if (!seenInfinitives.has(word)) {
                        seenInfinitives.add(word);
                        processedWords.push({
                            serbian_word: word,
                            english_translation: response,
                            category_id: 1,
                            category_name: 'Common Words'
                        });
                    }
                }
            } catch (error) {
                console.error(`Error translating word "${word}":`, error);
                if (!seenInfinitives.has(word)) {
                    seenInfinitives.add(word);
                    processedWords.push({
                        serbian_word: word,
                        english_translation: 'Translation failed',
                        category_id: 1,
                        category_name: 'Common Words'
                    });
                }
            }
        }

        // Now check which words already exist in database
        const infinitiveForms = processedWords.map(w => w.serbian_word);
        const existingWordsResult = await pool.query(
            'SELECT serbian_word FROM words WHERE serbian_word = ANY($1)',
            [infinitiveForms]
        );

        const existingWords = new Set(existingWordsResult.rows.map(row => row.serbian_word));
        const newWords = processedWords.filter(word => !existingWords.has(word.serbian_word));

        res.json({
            total_words: uniqueWords.length,
            existing_words: existingWords.size,
            new_words: newWords.length,
            translations: newWords
        });
    } catch (error) {
        console.error('Error processing text:', error);
        res.status(500).json({ error: 'Failed to process text' });
    }
});

// Add new words to database
app.post('/api/words', async (req, res) => {
    try {
        const { words } = req.body;

        if (!words || !Array.isArray(words)) {
            return res.status(400).json({ error: 'Words array is required' });
        }

        const insertedWords = [];

        for (const word of words) {
            try {
                const result = await pool.query(
                    `INSERT INTO words (serbian_word, english_translation, category_id, context, notes)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (serbian_word, english_translation) DO NOTHING
           RETURNING *`,
                    [
                        word.serbian_word,
                        word.english_translation,
                        word.category_id || 1, // Default to "Common Words" category
                        word.context || null,
                        word.notes || null
                    ]
                );

                if (result.rows.length > 0) {
                    insertedWords.push(result.rows[0]);

                    // Add to user vocabulary
                    await pool.query(
                        `INSERT INTO user_vocabulary (word_id)
             VALUES ($1)
             ON CONFLICT (word_id) DO NOTHING`,
                        [result.rows[0].id]
                    );
                }
            } catch (error) {
                console.error(`Error inserting word "${word.serbian_word}":`, error);
            }
        }

        res.json({
            inserted: insertedWords.length,
            words: insertedWords
        });
    } catch (error) {
        console.error('Error adding words:', error);
        res.status(500).json({ error: 'Failed to add words' });
    }
});

// Get practice words with multiple choice options
app.get('/api/practice/words', async (req, res) => {
    try {
        const { limit = 10, difficulty } = req.query;

        let query = `
      SELECT w.*, c.name as category_name, uv.mastery_level, uv.times_practiced
      FROM words w
      LEFT JOIN categories c ON w.category_id = c.id
      LEFT JOIN user_vocabulary uv ON w.id = uv.word_id
      WHERE uv.mastery_level < 80
    `;

        if (difficulty) {
            query += ` AND w.difficulty_level = ${difficulty}`;
        }

        query += ` ORDER BY 
      COALESCE(uv.last_practiced, '1900-01-01'::timestamp) ASC,
      uv.mastery_level ASC
      LIMIT $1`;

        const result = await pool.query(query, [limit]);

        // For each word, get 3 random incorrect options
        const practiceWords = [];
        for (const word of result.rows) {
            // Get 3 random words as incorrect options
            const optionsResult = await pool.query(
                `SELECT english_translation FROM words 
                 WHERE id != $1 
                 ORDER BY RANDOM() 
                 LIMIT 3`,
                [word.id]
            );

            const incorrectOptions = optionsResult.rows.map(row => row.english_translation);
            const allOptions = [word.english_translation, ...incorrectOptions];

            // Shuffle options
            for (let i = allOptions.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [allOptions[i], allOptions[j]] = [allOptions[j], allOptions[i]];
            }

            practiceWords.push({
                ...word,
                options: allOptions,
                correct_answer: word.english_translation
            });
        }

        res.json(practiceWords);
    } catch (error) {
        console.error('Error fetching practice words:', error);
        res.status(500).json({ error: 'Failed to fetch practice words' });
    }
});

// Generate example sentence for a word
app.post('/api/practice/example-sentence', async (req, res) => {
    try {
        const { serbian_word, english_translation, category } = req.body;

        const completion = await openai.chat.completions.create({
            model: "gpt-3.5-turbo",
            messages: [
                {
                    role: "system",
                    content: `You are a Serbian language teacher. Create a simple Serbian sentence using the given word. The sentence should be easy to understand and help reinforce the word's meaning.`
                },
                {
                    role: "user",
                    content: `Create a Serbian sentence using the word "${serbian_word}" (${english_translation}). Keep it simple and educational.`
                }
            ],
            temperature: 0.7,
            max_tokens: 100
        });

        const sentence = completion.choices[0].message.content.trim();
        res.json({ sentence });
    } catch (error) {
        console.error('Error generating example sentence:', error);
        res.status(500).json({ error: 'Failed to generate example sentence' });
    }
});

// Start practice session
app.post('/api/practice/start', async (req, res) => {
    try {
        const result = await pool.query(
            'INSERT INTO practice_sessions DEFAULT VALUES RETURNING *'
        );
        res.json(result.rows[0]);
    } catch (error) {
        console.error('Error starting practice session:', error);
        res.status(500).json({ error: 'Failed to start practice session' });
    }
});

// Submit practice result
app.post('/api/practice/submit', async (req, res) => {
    try {
        const { session_id, word_id, was_correct, response_time_seconds } = req.body;

        // Record the result
        await pool.query(
            `INSERT INTO practice_results (session_id, word_id, was_correct, response_time_seconds)
       VALUES ($1, $2, $3, $4)`,
            [session_id, word_id, was_correct, response_time_seconds || null]
        );

        // Update user vocabulary stats
        if (was_correct) {
            await pool.query(
                `UPDATE user_vocabulary 
         SET times_practiced = times_practiced + 1,
             times_correct = times_correct + 1,
             last_practiced = CURRENT_TIMESTAMP,
             mastery_level = LEAST(mastery_level + 10, 100)
         WHERE word_id = $1`,
                [word_id]
            );
        } else {
            await pool.query(
                `UPDATE user_vocabulary 
         SET times_practiced = times_practiced + 1,
             last_practiced = CURRENT_TIMESTAMP,
             mastery_level = GREATEST(mastery_level - 5, 0)
         WHERE word_id = $1`,
                [word_id]
            );
        }

        res.json({ success: true });
    } catch (error) {
        console.error('Error submitting practice result:', error);
        res.status(500).json({ error: 'Failed to submit practice result' });
    }
});

// Complete practice session
app.post('/api/practice/complete', async (req, res) => {
    try {
        const { session_id, duration_seconds } = req.body;

        // Get session statistics
        const statsResult = await pool.query(
            `SELECT 
        COUNT(*) as total_questions,
        SUM(CASE WHEN was_correct THEN 1 ELSE 0 END) as correct_answers
       FROM practice_results
       WHERE session_id = $1`,
            [session_id]
        );

        const stats = statsResult.rows[0];

        // Update session
        await pool.query(
            `UPDATE practice_sessions 
       SET total_questions = $1,
           correct_answers = $2,
           duration_seconds = $3
       WHERE id = $4`,
            [stats.total_questions, stats.correct_answers, duration_seconds, session_id]
        );

        res.json({
            total_questions: parseInt(stats.total_questions),
            correct_answers: parseInt(stats.correct_answers),
            accuracy: stats.total_questions > 0
                ? Math.round((stats.correct_answers / stats.total_questions) * 100)
                : 0
        });
    } catch (error) {
        console.error('Error completing practice session:', error);
        res.status(500).json({ error: 'Failed to complete practice session' });
    }
});

// Get user statistics
app.get('/api/stats', async (req, res) => {
    try {
        const totalWordsResult = await pool.query('SELECT COUNT(*) FROM words');
        const learnedWordsResult = await pool.query('SELECT COUNT(*) FROM user_vocabulary WHERE times_practiced > 0');
        const masteredWordsResult = await pool.query('SELECT COUNT(*) FROM user_vocabulary WHERE mastery_level >= 80');

        const recentSessionsResult = await pool.query(`
      SELECT * FROM practice_sessions 
      WHERE total_questions > 0
      ORDER BY session_date DESC 
      LIMIT 10
    `);

        res.json({
            total_words: parseInt(totalWordsResult.rows[0].count),
            learned_words: parseInt(learnedWordsResult.rows[0].count),
            mastered_words: parseInt(masteredWordsResult.rows[0].count),
            recent_sessions: recentSessionsResult.rows
        });
    } catch (error) {
        console.error('Error fetching statistics:', error);
        res.status(500).json({ error: 'Failed to fetch statistics' });
    }
});

// Helper function to fetch full article content
async function fetchFullArticle(url) {
    if (!axios) return null;

    try {
        const response = await axios.get(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'sr,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            },
            timeout: 10000 // 10 second timeout
        });

        const html = response.data;
        let content = '';

        // N1 Info specific patterns
        const n1Patterns = [
            // N1 Info article body pattern
            /<div[^>]*class="[^"]*rich-text[^"]*"[^>]*>([\s\S]*?)(?=<\/div>(?:\s*<div|$))/gi,
            /<div[^>]*class="[^"]*article__text[^"]*"[^>]*>([\s\S]*?)(?=<\/div>(?:\s*<div|$))/gi,
            /<div[^>]*class="[^"]*text-editor[^"]*"[^>]*>([\s\S]*?)(?=<\/div>(?:\s*<div|$))/gi,
            /<div[^>]*class="[^"]*entry-content[^"]*"[^>]*>([\s\S]*?)(?=<\/div>(?:\s*<div|$))/gi,
            // Look for paragraphs within article containers
            /<article[^>]*>([\s\S]*?)<\/article>/gi,
            /<div[^>]*class="[^"]*content[^"]*"[^>]*>([\s\S]*?)(?=<\/div>(?:\s*<div|$))/gi
        ];

        // Try each pattern
        for (const pattern of n1Patterns) {
            const matches = html.matchAll(pattern);
            for (const match of matches) {
                if (match[1]) {
                    // Extract all paragraph text from the matched content
                    const paragraphs = match[1].match(/<p[^>]*>([\s\S]*?)<\/p>/gi);
                    if (paragraphs && paragraphs.length > 0) {
                        const extractedContent = paragraphs
                            .map(p => p.replace(/<[^>]*>/g, ' ').trim())
                            .filter(text => text.length > 20) // Filter out very short paragraphs
                            .join('\n\n');

                        if (extractedContent.length > content.length) {
                            content = extractedContent;
                        }
                    }
                }
            }
        }

        // If no content found with specific patterns, try a more general approach
        if (!content || content.length < 200) {
            // Extract all paragraphs from the page
            const allParagraphs = html.match(/<p[^>]*>[\s\S]*?<\/p>/gi) || [];
            const paragraphTexts = allParagraphs
                .map(p => p.replace(/<[^>]*>/g, ' ').trim())
                .filter(text => {
                    // Filter out navigation, ads, and very short paragraphs
                    return text.length > 50 &&
                        !text.includes('Cookie') &&
                        !text.includes('cookie') &&
                        !text.includes('Prihvati') &&
                        !text.includes('Saglasnost') &&
                        !text.includes('©');
                });

            // Take the longest consecutive sequence of paragraphs (likely the article body)
            if (paragraphTexts.length > 3) {
                content = paragraphTexts.slice(0, -2).join('\n\n'); // Exclude likely footer paragraphs
            }
        }

        // Clean up the content - remove any embedded JavaScript first
        content = content
            .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '') // Remove script tags and content
            .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '') // Remove style tags and content
            .replace(/window\.addEventListener\s*\([^)]+\)\s*{[^{}]*(?:{[^{}]*(?:{[^{}]*}[^{}]*)*}[^{}]*)*}\s*\)\s*;?/g, '') // Remove window.addEventListener blocks with nested braces
            .replace(/window\.addEventListener[^;]+;/g, '') // Remove any remaining addEventListener
            .replace(/let\s+target\s*=\s*document\.querySelector[^}]+}\s*}\s*\)\s*;?/g, '') // Remove video embed code pattern
            .replace(/const\s+targetClose\s*=\s*document\.createElement[^}]+}\s*}\s*\)\s*;?/g, '') // Remove close button code
            .replace(/\/\/\s*add close button[^}]+}/g, '') // Remove code comments and blocks
            .replace(/\/\/\s*top position of sticky embed[^}]+}\s*\)\s*;?\s*}\s*\)\s*;?/g, '') // Remove sticky embed code
            .replace(/\/\/[^}]*}\s*}\s*\);?/g, '') // Remove any remaining comment with closing braces
            .replace(/}\s*}\s*\);?\s*}/g, '') // Remove orphaned closing braces
            .replace(/}\s*\)\s*;?\s*}/g, '') // Remove more orphaned closures
            .replace(/\bif\s*\([^)]+\)\s*{[^}]*}/g, '') // Remove if statements
            .replace(/\bfunction\s+\w+\s*\([^)]*\)\s*{[^}]*}/g, '') // Remove function declarations
            .replace(/\.\w+\s*\([^)]*\)/g, '') // Remove method calls
            .replace(/Foto:\s*[^/]+\/[^/]+/g, '') // Remove photo credits
            .replace(/&nbsp;/gi, ' ')
            .replace(/&quot;/gi, '"')
            .replace(/&#39;/gi, "'")
            .replace(/&amp;/gi, '&')
            .replace(/&lt;/gi, '<')
            .replace(/&gt;/gi, '>')
            .replace(/&#(\d+);/gi, (match, dec) => String.fromCharCode(dec))
            .replace(/&#x([a-fA-F0-9]+);/gi, (match, hex) => String.fromCharCode(parseInt(hex, 16)))
            .replace(/\s+/g, ' ')
            .replace(/\n\s*\n\s*\n/g, '\n\n') // Remove excessive line breaks
            .trim();

        // Only return content if it's substantial
        return content.length > 300 ? content : null;
    } catch (error) {
        console.error('Error fetching full article:', error.message);
        return null;
    }
}

// Get Serbian news articles
app.get('/api/news', async (req, res) => {
    try {
        // Try to fetch from RSS feed first if parser is available
        if (Parser && axios) {
            try {
                const parser = new Parser({
                    timeout: 10000,
                    headers: {
                        'User-Agent': 'Mozilla/5.0 (compatible; SerbianVocabApp/1.0)'
                    }
                });

                // Try multiple RSS feeds
                const rssFeeds = [
                    'https://n1info.rs/feed/',
                    'https://www.blic.rs/rss/danasnje-vesti',
                    'https://www.b92.net/info/rss/danas.xml'
                ];

                let articles = [];

                for (const feedUrl of rssFeeds) {
                    try {
                        const feed = await parser.parseURL(feedUrl);

                        // Determine source from URL
                        let source = "Serbian News";
                        if (feedUrl.includes('n1info')) source = "N1 Info";
                        else if (feedUrl.includes('blic')) source = "Blic";
                        else if (feedUrl.includes('b92')) source = "B92";

                        // Transform RSS items to our article format
                        const feedArticles = feed.items.slice(0, 5).map(item => {
                            // Try to get the full content from various possible fields
                            let content = '';

                            // RSS feeds often have content in different fields
                            if (item['content:encoded']) {
                                content = item['content:encoded'];
                            } else if (item.content) {
                                content = item.content;
                            } else if (item.description) {
                                content = item.description;
                            } else if (item.contentSnippet) {
                                content = item.contentSnippet;
                            } else if (item.summary) {
                                content = item.summary;
                            }

                            // Remove scripts and their content first
                            content = content
                                .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '') // Remove script tags and content
                                .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '') // Remove style tags and content
                                .replace(/window\.addEventListener\s*\([^)]+\)\s*{[^{}]*(?:{[^{}]*(?:{[^{}]*}[^{}]*)*}[^{}]*)*}\s*\)\s*;?/g, '') // Remove window.addEventListener blocks with nested braces
                                .replace(/window\.addEventListener[^;]+;/g, '') // Remove any remaining addEventListener
                                .replace(/let\s+target\s*=\s*document\.querySelector[^}]+}\s*}\s*\)\s*;?/g, '') // Remove video embed code pattern
                                .replace(/const\s+targetClose\s*=\s*document\.createElement[^}]+}\s*}\s*\)\s*;?/g, '') // Remove close button code
                                .replace(/\/\/\s*add close button[^}]+}/g, '') // Remove code comments and blocks
                                .replace(/\/\/\s*top position of sticky embed[^}]+}\s*\)\s*;?\s*}\s*\)\s*;?/g, '') // Remove sticky embed code
                                .replace(/\/\/[^}]*}\s*}\s*\);?/g, '') // Remove any remaining comment with closing braces
                                .replace(/}\s*}\s*\);?\s*}/g, '') // Remove orphaned closing braces
                                .replace(/}\s*\)\s*;?\s*}/g, '') // Remove more orphaned closures
                                .replace(/\bif\s*\([^)]+\)\s*{[^}]*}/g, '') // Remove if statements
                                .replace(/\bfunction\s+\w+\s*\([^)]*\)\s*{[^}]*}/g, '') // Remove function declarations
                                .replace(/\.\w+\s*\([^)]*\)/g, '') // Remove method calls
                                .replace(/Foto:\s*[^/]+\/[^/]+/g, '') // Remove photo credits
                                .replace(/<[^>]*>/g, '') // Remove remaining HTML tags
                                .replace(/&nbsp;/gi, ' ') // Replace non-breaking spaces
                                .replace(/&quot;/gi, '"') // Replace quotes
                                .replace(/&#39;/gi, "'") // Replace apostrophes
                                .replace(/&amp;/gi, '&') // Replace ampersands
                                .replace(/&#(\d+);/gi, (match, dec) => String.fromCharCode(dec))
                                .replace(/&#x([a-fA-F0-9]+);/gi, (match, hex) => String.fromCharCode(parseInt(hex, 16)))
                                .replace(/\s+/g, ' ') // Normalize whitespace
                                .trim();

                            const articleLink = item.link || item.guid;

                            return {
                                title: item.title || 'Bez naslova',
                                content: content || 'Sadržaj nije dostupan.',
                                source: source,
                                date: item.pubDate ? new Date(item.pubDate).toLocaleDateString('sr-Latn-RS') : new Date().toLocaleDateString('sr-Latn-RS'),
                                category: item.categories && item.categories.length > 0 ? item.categories[0] : "Vesti",
                                link: articleLink,
                                needsFullContent: content.length < 400 // Flag articles that need full content
                            };
                        });

                        articles = articles.concat(feedArticles);

                        // If we have enough articles, stop fetching
                        if (articles.length >= 10) break;

                    } catch (feedError) {
                        console.error(`Error fetching feed ${feedUrl}:`, feedError.message);
                        // Continue to next feed
                    }
                }

                // If we got some articles from RSS
                if (articles.length > 0) {
                    // Limit to 10 articles
                    articles = articles.slice(0, 10);

                    // Try to fetch full content for articles that need it
                    const articlesWithFullContent = await Promise.all(
                        articles.map(async (article) => {
                            if (article.needsFullContent && article.link) {
                                try {
                                    const fullContent = await fetchFullArticle(article.link);
                                    if (fullContent && fullContent.length > article.content.length) {
                                        return {
                                            ...article,
                                            content: fullContent,
                                            fullContentFetched: true,
                                            needsFullContent: false
                                        };
                                    }
                                } catch (fetchError) {
                                    console.error(`Error fetching full content for ${article.link}:`, fetchError.message);
                                }
                            }
                            return article;
                        })
                    );

                    res.json({ articles: articlesWithFullContent });
                    return;
                }
            } catch (rssError) {
                console.error('RSS feed error, falling back to sample articles:', rssError);
            }
        } else {
            console.log('RSS parser or axios not available, using sample articles');
        }

        // Fallback to sample articles if RSS fails
        const articles = [
            {
                title: "Novi most preko Dunava uskoro završen",
                content: `Radovi na izgradnji novog mosta preko Dunava ulaze u završnu fazu. Gradonačelnik je izjavio da će most biti otvoren za saobraćaj do kraja godine. Ovaj projekat predstavlja jednu od najvećih investicija u infrastrukturu u poslednjih deset godina. Most će značajno poboljšati saobraćajnu povezanost između dva dela grada i smanjiti gužve na postojećim mostovima. Ukupna vrednost investicije iznosi preko 100 miliona evra. Novi most će imati šest traka za vozila, kao i posebne staze za bicikliste i pešake. Očekuje se da će preko mosta dnevno prelaziti više od 50.000 vozila.`,
                source: "Dnevne novosti",
                date: new Date().toLocaleDateString('sr-Latn-RS'),
                category: "Infrastruktura"
            },
            {
                title: "Otvorena nova biblioteka u centru grada",
                content: `Danas je svečano otvorena nova gradska biblioteka koja se nalazi u samom centru grada. Biblioteka raspolaže sa preko 100.000 knjiga i modernom čitaonicom. Posebna pažnja posvećena je dečjem odeljenju koje ima interaktivne sadržaje za najmlađe čitaoce. U biblioteci se nalazi i multimedijalna sala za predavanja i kulturne događaje. Radno vreme biblioteke je od 8 do 20 časova svakog dana osim nedelje. Članarina je besplatna za učenike i studente. Direktorka biblioteke istakla je da će ustanova organizovati brojne književne večeri i radionice za decu.`,
                source: "Kulturni pregled",
                date: new Date().toLocaleDateString('sr-Latn-RS'),
                category: "Kultura"
            },
            {
                title: "Uspešna žetva pšenice ove godine",
                content: `Poljoprivrednici širom zemlje izveštavaju o uspešnoj žetvi pšenice. Prinosi su iznad proseka zahvaljujući povoljnim vremenskim uslovima tokom proleća. Ministarstvo poljoprivrede saopštilo je da će otkupna cena pšenice biti stabilna. Očekuje se da će ukupan prinos premašiti prošlogodišnji za oko 15 procenata. Kvalitet pšenice je izuzetan, što će omogućiti značajan izvoz. Mnogi poljoprivrednici su zadovoljni ovogodišnjom žetvom i planiraju da prošire zasejane površine sledeće godine. Država je obećala subvencije za nabavku nove mehanizacije.`,
                source: "Poljoprivredni glasnik",
                date: new Date().toLocaleDateString('sr-Latn-RS'),
                category: "Poljoprivreda"
            }
        ];

        res.json({ articles });
    } catch (error) {
        console.error('Error fetching news:', error);
        res.status(500).json({ error: 'Failed to fetch news articles' });
    }
});

app.listen(port, () => {
    console.log(`Serbian Vocabulary API running on port ${port}`);
});
