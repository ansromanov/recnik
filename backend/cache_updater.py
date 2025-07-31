import os
import time
import json
import logging
from datetime import datetime
import redis
import feedparser
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Cache configuration
CACHE_EXPIRY = 3600  # 1 hour expiry for individual items
UPDATE_INTERVAL = 900  # 15 minutes

# RSS feeds configuration
RSS_FEEDS = {
    "n1info": {
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


def clean_html_content(html_content):
    """Remove HTML tags and clean up content"""
    import re

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


def fetch_full_article(url):
    """Fetch and extract article content from URL"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "sr,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = "utf-8"

        import re

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
        logger.error(f"Error fetching full article from {url}: {e}")
        return None


def fetch_feed_articles(source_key, category, feed_url, max_articles=10):
    """Fetch articles from a single RSS feed"""
    articles = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Charset": "utf-8",
            "Accept-Encoding": "gzip, deflate",
        }

        feed = feedparser.parse(feed_url, request_headers=headers)

        # Ensure proper encoding
        if hasattr(feed, "encoding"):
            if feed.encoding and feed.encoding.lower() not in ["utf-8", "utf8"]:
                try:
                    response = requests.get(feed_url, headers=headers, timeout=10)
                    response.encoding = "utf-8"
                    feed = feedparser.parse(response.text)
                except:
                    pass

        # Transform RSS items to article format
        for item in feed.entries[:max_articles]:
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

            article_link = item.link if hasattr(item, "link") else item.get("guid", "")

            article = {
                "title": item.title if hasattr(item, "title") else "Bez naslova",
                "content": content or "Sadržaj nije dostupan.",
                "source": RSS_FEEDS[source_key]["name"],
                "date": datetime(*item.published_parsed[:6]).strftime("%d.%m.%Y")
                if hasattr(item, "published_parsed")
                else datetime.now().strftime("%d.%m.%Y"),
                "category": category,
                "link": article_link,
                "source_key": source_key,
                "needsFullContent": len(content) < 400,
            }

            # Try to fetch full content if needed
            if article["needsFullContent"] and article["link"]:
                full_content = fetch_full_article(article["link"])
                if full_content and len(full_content) > len(article["content"]):
                    article["content"] = full_content
                    article["fullContentFetched"] = True
                    article["needsFullContent"] = False

            articles.append(article)

    except Exception as e:
        logger.error(f"Error fetching feed {feed_url}: {e}")

    return articles


def update_news_cache():
    """Update the news cache in Redis"""
    logger.info("Starting news cache update...")

    try:
        # Clear existing cache
        for key in redis_client.scan_iter("news:*"):
            redis_client.delete(key)

        # Fetch articles from all sources and categories
        all_articles = []

        for source_key, source_info in RSS_FEEDS.items():
            for category, feed_url in source_info["categories"].items():
                logger.info(f"Fetching {source_key} - {category}")

                articles = fetch_feed_articles(source_key, category, feed_url)

                # Store articles by source and category
                cache_key = f"news:{source_key}:{category}"
                if articles:
                    redis_client.setex(cache_key, CACHE_EXPIRY, json.dumps(articles))
                    all_articles.extend(articles)

                # Also store in combined keys
                # Store all articles for a source
                source_cache_key = f"news:{source_key}:all"
                existing = redis_client.get(source_cache_key)
                if existing:
                    existing_articles = json.loads(existing)
                    existing_articles.extend(articles)
                    redis_client.setex(
                        source_cache_key,
                        CACHE_EXPIRY,
                        json.dumps(existing_articles[:50]),  # Keep top 50
                    )
                else:
                    redis_client.setex(
                        source_cache_key, CACHE_EXPIRY, json.dumps(articles)
                    )

        # Store all articles combined
        redis_client.setex(
            "news:all:all",
            CACHE_EXPIRY,
            json.dumps(all_articles[:100]),  # Keep top 100
        )

        # Store last update timestamp
        redis_client.set("news:last_update", datetime.now().isoformat())

        logger.info(
            f"News cache updated successfully. Total articles: {len(all_articles)}"
        )

    except Exception as e:
        logger.error(f"Error updating news cache: {e}")


def main():
    """Main loop for the cache updater"""
    logger.info("Cache updater service started")

    # Initial update
    update_news_cache()

    # Run updates every 15 minutes
    while True:
        try:
            time.sleep(UPDATE_INTERVAL)
            update_news_cache()
        except KeyboardInterrupt:
            logger.info("Cache updater service stopped")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            time.sleep(60)  # Wait a minute before retrying


if __name__ == "__main__":
    main()
