# News Service

Enhanced news service with proper formatting and LLM content generation capabilities.

## Features

### Enhanced News Processing

- **Improved Formatting**: Proper paragraph separation and line breaks between articles
- **Content Cleaning**: Advanced HTML cleaning while preserving article structure
- **Metadata Extraction**: Reading time, difficulty level, and word count calculation
- **Multi-source Support**: N1 Info, Blic, B92 with category filtering

### LLM-Generated Content

- **Dialogues**: Conversational content on news topics
- **Summaries**: Article summaries with vocabulary focus
- **Stories**: Educational stories incorporating target vocabulary
- **Vocabulary Context**: Content designed to teach specific words

### Content Types

- `dialogue`: Conversational format between speakers
- `summary`: Concise article summaries
- `story`: Educational narratives
- `interview`: Question-answer format
- `vocabulary_exercise`: Vocabulary-focused content

## API Endpoints

### News Endpoints

- `GET /api/news` - Get formatted news articles
- `GET /api/news/sources` - Get available sources and categories
- `GET /api/news/article/{id}` - Get detailed article
- `POST /api/news/refresh` - Refresh news cache

### Content Generation Endpoints

- `POST /api/content/dialogue` - Generate dialogue from topic
- `POST /api/content/summary` - Generate summary from article
- `POST /api/content/vocabulary-context` - Generate vocabulary-focused content
- `GET /api/content/types` - Get available content types
- `GET /api/content/recent` - Get recent generated content

### Service Endpoints

- `GET /health` - Health check
- `GET /metrics` - Service metrics

## Configuration

Required environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `OPENAI_API_KEY` - OpenAI API key for content generation
- `OPENAI_MODEL` - OpenAI model (default: gpt-3.5-turbo)
- `PORT` - Service port (default: 5002)
- `DEBUG` - Debug mode (default: false)

## Usage

### Generate Dialogue

```bash
curl -X POST http://localhost:5002/api/content/dialogue \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Serbian cuisine",
    "difficulty": "intermediate",
    "word_count": 200
  }'
```

### Generate Summary

```bash
curl -X POST http://localhost:5002/api/content/summary \
  -H "Content-Type: application/json" \
  -d '{
    "article_text": "Article content here...",
    "type": "vocabulary_focused"
  }'
```

### Get Formatted News

```bash
curl "http://localhost:5002/api/news?source=n1info&category=vesti&type=article&limit=10"
```

## Content Templates

The service includes predefined templates for generating different content types:

1. **News Dialogue - Intermediate**: Conversational format for news topics
2. **News Summary - Brief**: Concise article summaries
3. **Vocabulary Story**: Stories incorporating target vocabulary

Templates can be customized through the database `content_templates` table.

## Caching

- **Redis Caching**: Formatted news cached for 1 hour
- **Cache Keys**: `formatted_news:{source}:{category}:{type}`
- **Metrics Tracking**: Cache hit rates and performance metrics

## Database Schema

### news_articles

- Enhanced article storage with formatting metadata
- Word count, reading time, difficulty level
- Processing flags for content state

### content_items

- LLM-generated content storage
- Topic, difficulty, target words tracking
- Generation metadata and prompts

### content_templates

- Reusable templates for content generation
- Customizable prompts and parameters

## Monitoring

- Health checks with dependency validation
- Prometheus metrics for performance monitoring
- Structured logging with request tracking
- Error rate and response time monitoring

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost/db"
export REDIS_URL="redis://localhost:6379"
export OPENAI_API_KEY="your-key-here"

# Run service
python main.py
```

## Docker

```bash
# Build image
docker build -t news-service .

# Run container
docker run -p 5002:5002 \
  -e DATABASE_URL="postgresql://user:pass@db/vocabulary" \
  -e REDIS_URL="redis://redis:6379" \
  -e OPENAI_API_KEY="your-key" \
  news-service
