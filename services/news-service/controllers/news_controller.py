from datetime import datetime
import json
import re

import feedparser
from flask import jsonify
import requests

from models.news import ContentItem


class NewsController:
    """Enhanced news controller with proper formatting and content management"""

    def __init__(self, redis_client, db, logger):
        self.redis_client = redis_client
        self.db = db
        self.logger = logger
        self.cache_expiry = 3600  # 1 hour

        # RSS feeds configuration
        self.rss_feeds = {
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

    def get_sources(self):
        """Get available news sources and categories"""
        sources = {
            "all": {"name": "All Sources", "value": ""},
        }

        # Add RSS sources
        for key, source in self.rss_feeds.items():
            sources[key] = {
                "name": source["name"],
                "value": key,
                "categories": list(source["categories"].keys()),
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

    def format_article_content(self, raw_content):
        """Enhanced content formatting with proper line breaks and structure"""
        if not raw_content:
            return raw_content

        # Remove HTML tags but preserve paragraph structure
        content = self.clean_html_with_structure(raw_content)

        # Fix common formatting issues
        content = self.fix_content_formatting(content)

        # Ensure proper paragraph separation
        content = self.ensure_paragraph_separation(content)

        return content.strip()

    def clean_html_with_structure(self, html_content):
        """Remove HTML tags while preserving paragraph structure"""
        if not html_content:
            return ""

        # Convert paragraph tags to double newlines
        html_content = re.sub(r"<p[^>]*>", "\n\n", html_content, flags=re.IGNORECASE)
        html_content = re.sub(r"</p>", "", html_content, flags=re.IGNORECASE)

        # Convert line breaks to newlines
        html_content = re.sub(r"<br[^>]*/?>", "\n", html_content, flags=re.IGNORECASE)

        # Convert div tags to line breaks
        html_content = re.sub(r"<div[^>]*>", "\n", html_content, flags=re.IGNORECASE)
        html_content = re.sub(r"</div>", "", html_content, flags=re.IGNORECASE)

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

        # Remove all remaining HTML tags
        html_content = re.sub(r"<[^>]+>", "", html_content)

        # Decode HTML entities
        html_entities = {
            "&nbsp;": " ",
            "&quot;": '"',
            "&#39;": "'",
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&ndash;": "–",
            "&mdash;": "—",
            "&hellip;": "…",
        }

        for entity, replacement in html_entities.items():
            html_content = html_content.replace(entity, replacement)

        return html_content

    def fix_content_formatting(self, content):
        """Fix common formatting issues in news content"""
        if not content:
            return content

        # Fix multiple spaces
        content = re.sub(r" +", " ", content)

        # Fix spacing around punctuation
        content = re.sub(r" +([,.;:!?])", r"\1", content)
        content = re.sub(r"([,.;:!?]) +", r"\1 ", content)

        # Fix quotes spacing
        content = re.sub(r' +"', '"', content)
        content = re.sub(r'" +', '"', content)

        # Fix Serbian specific formatting
        content = re.sub(r"(\w)- (\w)", r"\1-\2", content)  # Fix hyphenated words

        return content

    def ensure_paragraph_separation(self, content):
        """Ensure proper paragraph separation with line breaks"""
        if not content:
            return content

        # Split into lines and clean up
        lines = content.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:  # Only add non-empty lines
                cleaned_lines.append(line)

        # Join with double newlines to create clear paragraph separation
        formatted_content = "\n\n".join(cleaned_lines)

        # Ensure we don't have more than 2 consecutive newlines
        formatted_content = re.sub(r"\n{3,}", "\n\n", formatted_content)

        return formatted_content

    def calculate_reading_time(self, content):
        """Calculate estimated reading time in minutes"""
        if not content:
            return 0

        # Average reading speed: 200 words per minute for Serbian text
        words = len(content.split())
        return max(1, round(words / 200))

    def determine_difficulty_level(self, content):
        """Determine difficulty level based on content complexity"""
        if not content:
            return "intermediate"

        words = content.split()
        word_count = len(words)

        # Simple heuristic based on word count and sentence length
        sentences = content.split(".")
        avg_sentence_length = (
            sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        )

        if word_count < 200 and avg_sentence_length < 15:
            return "beginner"
        elif word_count > 500 or avg_sentence_length > 25:
            return "advanced"
        else:
            return "intermediate"

    def fetch_and_format_articles(self, source_key, category, max_articles=10):
        """Fetch articles from RSS and format them properly"""
        articles = []

        try:
            if source_key not in self.rss_feeds:
                return articles

            source_info = self.rss_feeds[source_key]
            feed_url = source_info["categories"].get(
                category, source_info["categories"]["all"]
            )

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Charset": "utf-8",
                "Accept-Encoding": "gzip, deflate",
            }

            feed = feedparser.parse(feed_url, request_headers=headers)

            # Ensure proper encoding
            if (
                hasattr(feed, "encoding")
                and feed.encoding
                and feed.encoding.lower() not in ["utf-8", "utf8"]
            ):
                try:
                    response = requests.get(feed_url, headers=headers, timeout=10)
                    response.encoding = "utf-8"
                    feed = feedparser.parse(response.text)
                except:
                    pass

            for item in feed.entries[:max_articles]:
                # Get content from various fields
                raw_content = ""
                if hasattr(item, "content") and item.content:
                    raw_content = (
                        item.content[0].value
                        if isinstance(item.content, list)
                        else item.content
                    )
                elif hasattr(item, "description"):
                    raw_content = item.description
                elif hasattr(item, "summary"):
                    raw_content = item.summary

                # Format the content properly
                formatted_content = self.format_article_content(raw_content)

                # Calculate metadata
                word_count = len(formatted_content.split()) if formatted_content else 0
                reading_time = self.calculate_reading_time(formatted_content)
                difficulty = self.determine_difficulty_level(formatted_content)

                article = {
                    "title": item.title if hasattr(item, "title") else "Bez naslova",
                    "content": formatted_content or "Sadržaj nije dostupan.",
                    "raw_content": raw_content,
                    "source": source_info["name"],
                    "source_url": item.link if hasattr(item, "link") else "",
                    "category": category,
                    "publish_date": (
                        datetime(*item.published_parsed[:6]).strftime("%d.%m.%Y %H:%M")
                        if hasattr(item, "published_parsed")
                        else datetime.now().strftime("%d.%m.%Y %H:%M")
                    ),
                    "word_count": word_count,
                    "reading_time_minutes": reading_time,
                    "difficulty_level": difficulty,
                    "is_formatted": True,
                    "has_full_content": len(formatted_content) > 300,
                    "content_type": "article",
                    "date": (
                        datetime(*item.published_parsed[:6]).strftime("%d.%m.%Y")
                        if hasattr(item, "published_parsed")
                        else datetime.now().strftime("%d.%m.%Y")
                    ),
                }

                articles.append(article)

        except Exception as e:
            self.logger.error(
                f"Error fetching articles from {source_key}/{category}: {e}"
            )

        return articles

    def get_generated_content(self, content_type="all", limit=10):
        """Get generated content from database"""
        try:
            query = ContentItem.query.order_by(ContentItem.created_at.desc())

            if content_type != "all":
                query = query.filter_by(content_type=content_type)

            content_items = query.limit(limit).all()

            # Convert to the same format as RSS articles
            articles = []
            for item in content_items:
                article = {
                    "title": item.title,
                    "content": item.content,
                    "source": "Generated",
                    "source_url": "",
                    "category": item.content_type,
                    "publish_date": item.created_at.strftime("%d.%m.%Y %H:%M"),
                    "date": item.created_at.strftime("%d.%m.%Y"),
                    "word_count": item.word_count or len(item.content.split()),
                    "reading_time_minutes": item.reading_time_minutes
                    or max(1, round(len(item.content.split()) / 200)),
                    "difficulty_level": item.difficulty_level or "intermediate",
                    "is_formatted": True,
                    "has_full_content": True,
                    "content_type": item.content_type,
                    "generated": True,
                    "topic": item.topic,
                }
                articles.append(article)

            return articles

        except Exception as e:
            self.logger.error(f"Error getting generated content: {e}")
            return []

    def get_formatted_news(self, source, category, content_type, limit):
        """Get news with enhanced formatting and content type filtering"""
        try:
            # Construct cache key
            cache_key = f"formatted_news:{source}:{category}:{content_type}"

            # Try cache first
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                try:
                    data = json.loads(cached_data)
                    return jsonify(
                        {
                            "articles": data["articles"][:limit],
                            "from_cache": True,
                            "last_update": data.get("last_update"),
                            "total": len(data["articles"]),
                        }
                    )
                except:
                    pass

            # Fetch fresh articles
            all_articles = []

            # Always include generated content
            generated_articles = self.get_generated_content(content_type, limit // 2)
            all_articles.extend(generated_articles)

            # Fetch RSS articles only if not filtering for generated content types
            if content_type in ["all", "article"]:
                if source == "all" or not source:
                    # Fetch from all sources
                    for source_key in self.rss_feeds.keys():
                        articles = self.fetch_and_format_articles(
                            source_key, category, 3
                        )
                        all_articles.extend(articles)
                else:
                    # Fetch from specific source
                    articles = self.fetch_and_format_articles(source, category, limit)
                    all_articles.extend(articles)

            # Sort by publish date (newest first)
            all_articles.sort(key=lambda x: x.get("publish_date", ""), reverse=True)

            # Filter by content type if specified
            if content_type != "all":
                all_articles = [
                    a for a in all_articles if a.get("content_type") == content_type
                ]

            # Cache the results
            cache_data = {
                "articles": all_articles,
                "last_update": datetime.now().isoformat(),
            }
            self.redis_client.setex(
                cache_key, self.cache_expiry, json.dumps(cache_data)
            )

            return jsonify(
                {
                    "articles": all_articles[:limit],
                    "from_cache": False,
                    "last_update": cache_data["last_update"],
                    "total": len(all_articles),
                }
            )

        except Exception as e:
            self.logger.error(f"Error getting formatted news: {e}")
            return jsonify({"error": "Failed to fetch news"}), 500

    def get_article_detail(self, article_id):
        """Get detailed article with full formatting"""
        try:
            # For now, return error since we don't have persistent storage yet
            # In future versions, this would fetch from database
            return jsonify({"error": "Article detail not implemented yet"}), 501

        except Exception as e:
            self.logger.error(f"Error getting article detail: {e}")
            return jsonify({"error": "Failed to get article detail"}), 500

    def refresh_news_cache(self):
        """Manually refresh news cache"""
        try:
            # Clear all formatted news cache
            for key in self.redis_client.scan_iter("formatted_news:*"):
                self.redis_client.delete(key)

            self.logger.info("News cache cleared successfully")
            return jsonify({"message": "News cache refreshed successfully"})

        except Exception as e:
            self.logger.error(f"Error refreshing news cache: {e}")
            return jsonify({"error": "Failed to refresh news cache"}), 500
