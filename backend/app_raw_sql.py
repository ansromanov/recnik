import os
import json
import random
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
import openai
from dotenv import load_dotenv
import requests
from html.parser import HTMLParser
import re

# Try to import feedparser, but don't crash if not available
try:
    import feedparser

    RSS_PARSER_AVAILABLE = True
except ImportError:
    print("feedparser not installed. News feature will use fallback articles.")
    RSS_PARSER_AVAILABLE = False

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database connection pool
DATABASE_URL = os.getenv("DATABASE_URL")
db_pool = SimpleConnectionPool(1, 20, DATABASE_URL)

# OpenAI configuration
openai.api_key = os.getenv("OPENAI_API_KEY")

# Test database connection
try:
    conn = db_pool.getconn()
    cur = conn.cursor()
    cur.execute("SELECT 1")
    cur.close()
    db_pool.putconn(conn)
    print("Connected to PostgreSQL database")
except Exception as e:
    print(f"Error connecting to database: {e}")


# Helper function to get database connection
def get_db():
    return db_pool.getconn()


def put_db(conn):
    db_pool.putconn(conn)


# Routes
@app.route("/api/health")
def health_check():
    return jsonify({"status": "ok", "message": "Serbian Vocabulary API is running"})


@app.route("/api/categories")
def get_categories():
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM categories ORDER BY name")
        categories = cur.fetchall()
        cur.close()
        return jsonify(categories)
    except Exception as e:
        print(f"Error fetching categories: {e}")
        return jsonify({"error": "Failed to fetch categories"}), 500
    finally:
        put_db(conn)


@app.route("/api/words")
def get_words():
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        category_id = request.args.get("category_id")

        query = """
            SELECT w.*, c.name as category_name, uv.mastery_level, uv.times_practiced
            FROM words w
            LEFT JOIN categories c ON w.category_id = c.id
            LEFT JOIN user_vocabulary uv ON w.id = uv.word_id
        """

        if category_id:
            query += " WHERE w.category_id = %s"
            cur.execute(query + " ORDER BY w.serbian_word", (category_id,))
        else:
            cur.execute(query + " ORDER BY w.serbian_word")

        words = cur.fetchall()
        cur.close()
        return jsonify(words)
    except Exception as e:
        print(f"Error fetching words: {e}")
        return jsonify({"error": "Failed to fetch words"}), 500
    finally:
        put_db(conn)


@app.route("/api/process-text", methods=["POST"])
def process_text():
    conn = get_db()
    try:
        data = request.get_json()
        text = data.get("text", "")

        if not text:
            return jsonify({"error": "Text is required"}), 400

        # Split text into words (basic tokenization for Serbian)
        words = [
            word
            for word in re.split(
                r"\s+", re.sub(r'[.,!?;:\'"«»()[\]{}]', " ", text.lower())
            )
            if len(word) > 1
        ]

        # Get unique words
        unique_words = list(set(words))

        # Get available categories
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, name FROM categories")
        categories = cur.fetchall()
        category_names = ", ".join([c["name"] for c in categories])
        cur.close()

        # Process words to get their infinitive forms
        processed_words = []
        seen_infinitives = set()

        # Limit to 50 words per request
        for word in unique_words[:50]:
            try:
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": f"""You are a Serbian-English translator and linguist. For the given Serbian word:
1. If it's a verb, convert it to infinitive form (e.g., "радим" → "радити", "идем" → "ићи")
2. Convert to lowercase UNLESS it's a proper noun (names of people, places, etc.)
3. Translate it to English
4. Categorize it into one of these categories: {category_names}

Respond in JSON format: {{"serbian_infinitive": "word in infinitive/base form", "translation": "english word", "category": "category name", "is_proper_noun": true/false}}""",
                        },
                        {"role": "user", "content": f'Serbian word: "{word}"'},
                    ],
                    temperature=0.3,
                    max_tokens=150,
                )

                response = completion.choices[0].message["content"].strip()
                try:
                    parsed = json.loads(response)
                    category = next(
                        (
                            c
                            for c in categories
                            if c["name"].lower() == parsed["category"].lower()
                        ),
                        None,
                    )

                    serbian_word = parsed.get("serbian_infinitive", word)

                    if serbian_word not in seen_infinitives:
                        seen_infinitives.add(serbian_word)
                        processed_words.append(
                            {
                                "serbian_word": serbian_word,
                                "english_translation": parsed["translation"],
                                "category_id": category["id"] if category else 1,
                                "category_name": category["name"]
                                if category
                                else "Common Words",
                                "original_form": word,
                            }
                        )
                except json.JSONDecodeError:
                    if word not in seen_infinitives:
                        seen_infinitives.add(word)
                        processed_words.append(
                            {
                                "serbian_word": word,
                                "english_translation": response,
                                "category_id": 1,
                                "category_name": "Common Words",
                            }
                        )
            except Exception as e:
                print(f'Error translating word "{word}": {e}')
                if word not in seen_infinitives:
                    seen_infinitives.add(word)
                    processed_words.append(
                        {
                            "serbian_word": word,
                            "english_translation": "Translation failed",
                            "category_id": 1,
                            "category_name": "Common Words",
                        }
                    )

        # Check which words already exist
        infinitive_forms = [w["serbian_word"] for w in processed_words]
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT serbian_word FROM words WHERE serbian_word = ANY(%s)",
            (infinitive_forms,),
        )
        existing_words = set(row["serbian_word"] for row in cur.fetchall())
        cur.close()

        new_words = [
            word
            for word in processed_words
            if word["serbian_word"] not in existing_words
        ]

        return jsonify(
            {
                "total_words": len(unique_words),
                "existing_words": len(existing_words),
                "new_words": len(new_words),
                "translations": new_words,
            }
        )
    except Exception as e:
        print(f"Error processing text: {e}")
        return jsonify({"error": "Failed to process text"}), 500
    finally:
        put_db(conn)


@app.route("/api/words", methods=["POST"])
def add_words():
    conn = get_db()
    try:
        data = request.get_json()
        words = data.get("words", [])

        if not words or not isinstance(words, list):
            return jsonify({"error": "Words array is required"}), 400

        inserted_words = []
        cur = conn.cursor(cursor_factory=RealDictCursor)

        for word in words:
            try:
                cur.execute(
                    """
                    INSERT INTO words (serbian_word, english_translation, category_id, context, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (serbian_word, english_translation) DO NOTHING
                    RETURNING *
                """,
                    (
                        word["serbian_word"],
                        word["english_translation"],
                        word.get("category_id", 1),
                        word.get("context"),
                        word.get("notes"),
                    ),
                )

                result = cur.fetchone()
                if result:
                    inserted_words.append(result)

                    # Add to user vocabulary
                    cur.execute(
                        """
                        INSERT INTO user_vocabulary (word_id)
                        VALUES (%s)
                        ON CONFLICT (word_id) DO NOTHING
                    """,
                        (result["id"],),
                    )
            except Exception as e:
                print(f'Error inserting word "{word["serbian_word"]}": {e}')

        conn.commit()
        cur.close()

        return jsonify({"inserted": len(inserted_words), "words": inserted_words})
    except Exception as e:
        conn.rollback()
        print(f"Error adding words: {e}")
        return jsonify({"error": "Failed to add words"}), 500
    finally:
        put_db(conn)


@app.route("/api/practice/words")
def get_practice_words():
    conn = get_db()
    try:
        limit = int(request.args.get("limit", 10))
        difficulty = request.args.get("difficulty")

        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT w.*, c.name as category_name, uv.mastery_level, uv.times_practiced
            FROM words w
            LEFT JOIN categories c ON w.category_id = c.id
            LEFT JOIN user_vocabulary uv ON w.id = uv.word_id
            WHERE uv.mastery_level < 80
        """

        params = []
        if difficulty:
            query += " AND w.difficulty_level = %s"
            params.append(difficulty)

        query += """ ORDER BY 
            COALESCE(uv.last_practiced, '1900-01-01'::timestamp) ASC,
            uv.mastery_level ASC
            LIMIT %s"""
        params.append(limit)

        cur.execute(query, params)
        words = cur.fetchall()

        # For each word, get 3 random incorrect options
        practice_words = []
        for word in words:
            cur.execute(
                """
                SELECT english_translation FROM words 
                WHERE id != %s 
                ORDER BY RANDOM() 
                LIMIT 3
            """,
                (word["id"],),
            )

            incorrect_options = [row["english_translation"] for row in cur.fetchall()]
            all_options = [word["english_translation"]] + incorrect_options

            # Shuffle options
            random.shuffle(all_options)

            practice_words.append(
                {
                    **word,
                    "options": all_options,
                    "correct_answer": word["english_translation"],
                }
            )

        cur.close()
        return jsonify(practice_words)
    except Exception as e:
        print(f"Error fetching practice words: {e}")
        return jsonify({"error": "Failed to fetch practice words"}), 500
    finally:
        put_db(conn)


@app.route("/api/practice/example-sentence", methods=["POST"])
def generate_example_sentence():
    try:
        data = request.get_json()
        serbian_word = data.get("serbian_word")
        english_translation = data.get("english_translation")

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a Serbian language teacher. Create a simple Serbian sentence using the given word. The sentence should be easy to understand and help reinforce the word's meaning.",
                },
                {
                    "role": "user",
                    "content": f'Create a Serbian sentence using the word "{serbian_word}" ({english_translation}). Keep it simple and educational.',
                },
            ],
            temperature=0.7,
            max_tokens=100,
        )

        sentence = completion.choices[0].message["content"].strip()
        return jsonify({"sentence": sentence})
    except Exception as e:
        print(f"Error generating example sentence: {e}")
        return jsonify({"error": "Failed to generate example sentence"}), 500


@app.route("/api/practice/start", methods=["POST"])
def start_practice_session():
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("INSERT INTO practice_sessions DEFAULT VALUES RETURNING *")
        session = cur.fetchone()
        conn.commit()
        cur.close()
        return jsonify(session)
    except Exception as e:
        conn.rollback()
        print(f"Error starting practice session: {e}")
        return jsonify({"error": "Failed to start practice session"}), 500
    finally:
        put_db(conn)


@app.route("/api/practice/submit", methods=["POST"])
def submit_practice_result():
    conn = get_db()
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        word_id = data.get("word_id")
        was_correct = data.get("was_correct")
        response_time_seconds = data.get("response_time_seconds")

        cur = conn.cursor()

        # Record the result
        cur.execute(
            """
            INSERT INTO practice_results (session_id, word_id, was_correct, response_time_seconds)
            VALUES (%s, %s, %s, %s)
        """,
            (session_id, word_id, was_correct, response_time_seconds),
        )

        # Update user vocabulary stats
        if was_correct:
            cur.execute(
                """
                UPDATE user_vocabulary 
                SET times_practiced = times_practiced + 1,
                    times_correct = times_correct + 1,
                    last_practiced = CURRENT_TIMESTAMP,
                    mastery_level = LEAST(mastery_level + 10, 100)
                WHERE word_id = %s
            """,
                (word_id,),
            )
        else:
            cur.execute(
                """
                UPDATE user_vocabulary 
                SET times_practiced = times_practiced + 1,
                    last_practiced = CURRENT_TIMESTAMP,
                    mastery_level = GREATEST(mastery_level - 5, 0)
                WHERE word_id = %s
            """,
                (word_id,),
            )

        conn.commit()
        cur.close()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        print(f"Error submitting practice result: {e}")
        return jsonify({"error": "Failed to submit practice result"}), 500
    finally:
        put_db(conn)


@app.route("/api/practice/complete", methods=["POST"])
def complete_practice_session():
    conn = get_db()
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        duration_seconds = data.get("duration_seconds")

        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get session statistics
        cur.execute(
            """
            SELECT 
                COUNT(*) as total_questions,
                SUM(CASE WHEN was_correct THEN 1 ELSE 0 END) as correct_answers
            FROM practice_results
            WHERE session_id = %s
        """,
            (session_id,),
        )

        stats = cur.fetchone()

        # Update session
        cur.execute(
            """
            UPDATE practice_sessions 
            SET total_questions = %s,
                correct_answers = %s,
                duration_seconds = %s
            WHERE id = %s
        """,
            (
                stats["total_questions"],
                stats["correct_answers"],
                duration_seconds,
                session_id,
            ),
        )

        conn.commit()
        cur.close()

        return jsonify(
            {
                "total_questions": int(stats["total_questions"]),
                "correct_answers": int(stats["correct_answers"]),
                "accuracy": round(
                    (stats["correct_answers"] / stats["total_questions"]) * 100
                )
                if stats["total_questions"] > 0
                else 0,
            }
        )
    except Exception as e:
        conn.rollback()
        print(f"Error completing practice session: {e}")
        return jsonify({"error": "Failed to complete practice session"}), 500
    finally:
        put_db(conn)


@app.route("/api/stats")
def get_user_stats():
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT COUNT(*) as count FROM words")
        total_words = cur.fetchone()["count"]

        cur.execute(
            "SELECT COUNT(*) as count FROM user_vocabulary WHERE times_practiced > 0"
        )
        learned_words = cur.fetchone()["count"]

        cur.execute(
            "SELECT COUNT(*) as count FROM user_vocabulary WHERE mastery_level >= 80"
        )
        mastered_words = cur.fetchone()["count"]

        cur.execute("""
            SELECT * FROM practice_sessions 
            WHERE total_questions > 0
            ORDER BY session_date DESC 
            LIMIT 10
        """)
        recent_sessions = cur.fetchall()

        cur.close()

        return jsonify(
            {
                "total_words": int(total_words),
                "learned_words": int(learned_words),
                "mastered_words": int(mastered_words),
                "recent_sessions": recent_sessions,
            }
        )
    except Exception as e:
        print(f"Error fetching statistics: {e}")
        return jsonify({"error": "Failed to fetch statistics"}), 500
    finally:
        put_db(conn)


# Helper function to clean HTML content
def clean_html_content(html_content):
    """Remove HTML tags and clean up content"""
    # Remove script and style elements
    html_content = re.sub(
        r"<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>",
        "",
        html_content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    html_content = re.sub(
        r"<style\b[^<]*(?:(?!</style>)<[^<]*)*</style>",
        "",
        html_content,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Remove all HTML tags
    html_content = re.sub(r"<[^>]+>", "", html_content)

    # Decode HTML entities
    html_content = html_content.replace("&nbsp;", " ")
    html_content = html_content.replace("&quot;", '"')
    html_content = html_content.replace("&#39;", "'")
    html_content = html_content.replace("&amp;", "&")
    html_content = html_content.replace("&lt;", "<")
    html_content = html_content.replace("&gt;", ">")

    # Clean up whitespace
    html_content = re.sub(r"\s+", " ", html_content)
    html_content = re.sub(r"\n\s*\n\s*\n", "\n\n", html_content)

    return html_content.strip()


# Helper function to fetch full article content
def fetch_full_article(url):
    """Fetch and extract article content from URL"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "sr,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        html = response.text
        content = ""

        # N1 Info specific patterns
        patterns = [
            r'<div[^>]*class="[^"]*rich-text[^"]*"[^>]*>([\s\S]*?)(?=</div>(?:\s*<div|$))',
            r'<div[^>]*class="[^"]*article__text[^"]*"[^>]*>([\s\S]*?)(?=</div>(?:\s*<div|$))',
            r'<div[^>]*class="[^"]*text-editor[^"]*"[^>]*>([\s\S]*?)(?=</div>(?:\s*<div|$))',
            r'<div[^>]*class="[^"]*entry-content[^"]*"[^>]*>([\s\S]*?)(?=</div>(?:\s*<div|$))',
            r"<article[^>]*>([\s\S]*?)</article>",
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>([\s\S]*?)(?=</div>(?:\s*<div|$))',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE)
            for match in matches:
                if match.group(1):
                    paragraphs = re.findall(
                        r"<p[^>]*>([\s\S]*?)</p>", match.group(1), re.IGNORECASE
                    )
                    if paragraphs:
                        extracted_content = "\n\n".join(
                            [
                                clean_html_content(p)
                                for p in paragraphs
                                if len(clean_html_content(p)) > 20
                            ]
                        )
                        if len(extracted_content) > len(content):
                            content = extracted_content

        # If no content found with specific patterns, try general approach
        if not content or len(content) < 200:
            all_paragraphs = re.findall(r"<p[^>]*>[\s\S]*?</p>", html, re.IGNORECASE)
            paragraph_texts = []
            for p in all_paragraphs:
                text = clean_html_content(p)
                if (
                    len(text) > 50
                    and "Cookie" not in text
                    and "cookie" not in text
                    and "Prihvati" not in text
                    and "Saglasnost" not in text
                    and "©" not in text
                ):
                    paragraph_texts.append(text)

            if len(paragraph_texts) > 3:
                content = "\n\n".join(paragraph_texts[:-2])

        return content if len(content) > 300 else None
    except Exception as e:
        print(f"Error fetching full article: {e}")
        return None


@app.route("/api/news/sources")
def get_news_sources():
    sources = {
        "all": {"name": "All Sources", "value": ""},
        "n1info": {
            "name": "N1 Info",
            "value": "n1info",
            "categories": [
                "all",
                "vesti",
                "biznis",
                "sport",
                "kultura",
                "sci-tech",
                "region",
            ],
        },
        "blic": {
            "name": "Blic",
            "value": "blic",
            "categories": ["all", "vesti", "sport", "zabava", "kultura"],
        },
        "b92": {
            "name": "B92",
            "value": "b92",
            "categories": ["all", "vesti", "sport", "biz", "tehnopolis"],
        },
    }

    categories = {
        "all": "All Categories",
        "vesti": "News",
        "sport": "Sports",
        "kultura": "Culture",
        "biznis": "Business",
        "sci-tech": "Science & Tech",
        "region": "Region",
        "zabava": "Entertainment",
        "biz": "Business",
        "tehnopolis": "Technology",
    }

    return jsonify({"sources": sources, "categories": categories})


@app.route("/api/news")
def get_news():
    try:
        source = request.args.get("source")
        category = request.args.get("category")

        # Try to fetch from RSS feed first if parser is available
        if RSS_PARSER_AVAILABLE:
            try:
                # Define available RSS feeds with categories
                all_rss_feeds = {
                    "n1info": {
                        "url": "https://n1info.rs/feed/",
                        "name": "N1 Info",
                        "categories": {
                            "all": "https://n1info.rs/feed/",
                            "vesti": "https://n1info.rs/vesti/feed/",
                            "biznis": "https://n1info.rs/biznis/feed/",
                            "sport": "https://n1info.rs/sport/feed/",
                            "kultura": "https://n1info.rs/kultura/feed/",
                            "sci-tech": "https://n1info.rs/sci-tech/feed/",
                            "region": "https://n1info.rs/region/feed/",
                        },
                    },
                    "blic": {
                        "url": "https://www.blic.rs/rss/danasnje-vesti",
                        "name": "Blic",
                        "categories": {
                            "all": "https://www.blic.rs/rss/danasnje-vesti",
                            "vesti": "https://www.blic.rs/rss/vesti",
                            "sport": "https://www.blic.rs/rss/sport",
                            "zabava": "https://www.blic.rs/rss/zabava",
                            "kultura": "https://www.blic.rs/rss/kultura",
                        },
                    },
                    "b92": {
                        "url": "https://www.b92.net/info/rss/danas.xml",
                        "name": "B92",
                        "categories": {
                            "all": "https://www.b92.net/info/rss/danas.xml",
                            "vesti": "https://www.b92.net/info/rss/vesti.xml",
                            "sport": "https://www.b92.net/info/rss/sport.xml",
                            "biz": "https://www.b92.net/info/rss/biz.xml",
                            "tehnopolis": "https://www.b92.net/info/rss/tehnopolis.xml",
                        },
                    },
                }

                # Determine which feeds to use
                feeds_to_use = []
                if source and source in all_rss_feeds:
                    source_feed = all_rss_feeds[source]
                    category_url = source_feed["categories"].get(
                        category, source_feed["categories"]["all"]
                    )
                    feeds_to_use = [{"url": category_url, "name": source_feed["name"]}]
                else:
                    for key, feed in all_rss_feeds.items():
                        category_url = feed["categories"].get(
                            category, feed["categories"]["all"]
                        )
                        feeds_to_use.append({"url": category_url, "name": feed["name"]})

                articles = []

                for feed_info in feeds_to_use:
                    try:
                        feed = feedparser.parse(feed_info["url"])

                        # Transform RSS items to our article format
                        for item in feed.entries[:5]:
                            # Get content from various possible fields
                            content = ""
                            if hasattr(item, "content") and item.content:
                                content = (
                                    item.content[0].value
                                    if isinstance(item.content, list)
                                    else item.content
                                )
                            elif hasattr(item, "description"):
                                content = item.description
                            elif hasattr(item, "summary"):
                                content = item.summary

                            # Clean the content
                            content = clean_html_content(content)

                            article_link = (
                                item.link
                                if hasattr(item, "link")
                                else item.get("guid", "")
                            )

                            articles.append(
                                {
                                    "title": item.title
                                    if hasattr(item, "title")
                                    else "Bez naslova",
                                    "content": content or "Sadržaj nije dostupan.",
                                    "source": feed_info["name"],
                                    "date": datetime(
                                        *item.published_parsed[:6]
                                    ).strftime("%d.%m.%Y")
                                    if hasattr(item, "published_parsed")
                                    else datetime.now().strftime("%d.%m.%Y"),
                                    "category": item.categories[0].term
                                    if hasattr(item, "categories") and item.categories
                                    else "Vesti",
                                    "link": article_link,
                                    "needsFullContent": len(content) < 400,
                                }
                            )

                        if len(articles) >= 10:
                            break

                    except Exception as feed_error:
                        print(f"Error fetching feed {feed_info['url']}: {feed_error}")
                        continue

                # If we got some articles from RSS
                if articles:
                    articles = articles[:10]

                    # Try to fetch full content for articles that need it
                    for i, article in enumerate(articles):
                        if article["needsFullContent"] and article["link"]:
                            full_content = fetch_full_article(article["link"])
                            if full_content and len(full_content) > len(
                                article["content"]
                            ):
                                articles[i]["content"] = full_content
                                articles[i]["fullContentFetched"] = True
                                articles[i]["needsFullContent"] = False

                    return jsonify({"articles": articles})
            except Exception as rss_error:
                print(f"RSS feed error, falling back to sample articles: {rss_error}")
        else:
            print("RSS parser not available, using sample articles")

        # Fallback to sample articles
        articles = [
            {
                "title": "Novi most preko Dunava uskoro završen",
                "content": "Radovi na izgradnji novog mosta preko Dunava ulaze u završnu fazu. Gradonačelnik je izjavio da će most biti otvoren za saobraćaj do kraja godine. Ovaj projekat predstavlja jednu od najvećih investicija u infrastrukturu u poslednjih deset godina. Most će značajno poboljšati saobraćajnu povezanost između dva dela grada i smanjiti gužve na postojećim mostovima. Ukupna vrednost investicije iznosi preko 100 miliona evra. Novi most će imati šest traka za vozila, kao i posebne staze za bicikliste i pešake. Očekuje se da će preko mosta dnevno prelaziti više od 50.000 vozila.",
                "source": "Dnevne novosti",
                "date": datetime.now().strftime("%d.%m.%Y"),
                "category": "Infrastruktura",
            },
            {
                "title": "Otvorena nova biblioteka u centru grada",
                "content": "Danas je svečano otvorena nova gradska biblioteka koja se nalazi u samom centru grada. Biblioteka raspolaže sa preko 100.000 knjiga i modernom čitaonicom. Posebna pažnja posvećena je dečjem odeljenju koje ima interaktivne sadržaje za najmlađe čitaoce. U biblioteci se nalazi i multimedijalna sala za predavanja i kulturne događaje. Radno vreme biblioteke je od 8 do 20 časova svakog dana osim nedelje. Članarina je besplatna za učenike i studente. Direktorka biblioteke istakla je da će ustanova organizovati brojne književne večeri i radionice za decu.",
                "source": "Kulturni pregled",
                "date": datetime.now().strftime("%d.%m.%Y"),
                "category": "Kultura",
            },
            {
                "title": "Uspešna žetva pšenice ove godine",
                "content": "Poljoprivrednici širom zemlje izveštavaju o uspešnoj žetvi pšenice. Prinosi su iznad proseka zahvaljujući povoljnim vremenskim uslovima tokom proleća. Ministarstvo poljoprivrede saopštilo je da će otkupna cena pšenice biti stabilna. Očekuje se da će ukupan prinos premašiti prošlogodišnji za oko 15 procenata. Kvalitet pšenice je izuzetan, što će omogućiti značajan izvoz. Mnogi poljoprivrednici su zadovoljni ovogodišnjom žetvom i planiraju da prošire zasejane površine sledeće godine. Država je obećala subvencije za nabavku nove mehanizacije.",
                "source": "Poljoprivredni glasnik",
                "date": datetime.now().strftime("%d.%m.%Y"),
                "category": "Poljoprivreda",
            },
        ]

        return jsonify({"articles": articles})
    except Exception as e:
        print(f"Error fetching news: {e}")
        return jsonify({"error": "Failed to fetch news articles"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3001))
    app.run(host="0.0.0.0", port=port, debug=True)
