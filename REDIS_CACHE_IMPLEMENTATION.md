# Redis Cache Implementation for Serbian News

## Overview

A Redis-based caching system has been implemented to improve performance and reduce external API calls for the news feature. The system pre-fetches news articles from multiple Serbian news sources and stores them in Redis with automatic updates every 15 minutes.

## Architecture

### Components

1. **Redis Service**
   - Redis 7 Alpine container
   - Persistent storage with volume mounting
   - Configured for append-only file persistence

2. **Cache Updater Service**
   - Python-based background service
   - Runs continuously and updates cache every 15 minutes
   - Fetches articles from multiple RSS feeds
   - Attempts to fetch full article content when RSS summaries are short

3. **Backend Integration**
   - Flask app checks Redis cache first before fetching from RSS
   - Falls back to RSS feeds if cache miss or Redis error
   - Returns cache metadata (timestamp, source) to frontend

4. **Frontend Integration**
   - Displays cache indicator when articles are served from cache
   - Shows last update time for transparency

## News Sources and Categories

### Supported Sources

- **N1 Info**: vesti, biznis, sport, kultura, sci-tech, region
- **Blic**: vesti, sport, zabava, kultura
- **B92**: vesti, sport, biz, tehnopolis

### Cache Keys Structure

- `news:all:all` - All articles from all sources
- `news:{source}:all` - All articles from a specific source
- `news:{source}:{category}` - Articles from specific source and category
- `news:last_update` - Timestamp of last successful update

## Implementation Details

### Cache Updater (`cache_updater.py`)

- Fetches RSS feeds from all configured sources
- Cleans HTML content and extracts text
- Attempts to fetch full article content for short summaries
- Stores articles in Redis with 1-hour expiry
- Updates every 15 minutes (configurable)

### Backend Changes (`app.py`)

- Added Redis client initialization
- Modified `/api/news` endpoint to check cache first
- Returns cache metadata in response
- Graceful fallback to RSS on cache miss

### Frontend Changes

- Added cache status display in NewsPage
- Shows "📦 Cached" badge with last update time
- Styled with light blue background for visibility

## Benefits

1. **Performance**
   - Near-instant article loading from cache
   - Reduced latency for users
   - Better user experience

2. **Reliability**
   - Articles available even if RSS feeds are slow/down
   - Consistent article availability
   - Reduced dependency on external services

3. **Efficiency**
   - Reduced load on RSS feed servers
   - Lower bandwidth usage
   - Centralized article fetching

## Configuration

### Environment Variables

- `REDIS_URL`: Redis connection string (default: `redis://localhost:6379`)

### Cache Settings

- `CACHE_EXPIRY`: 3600 seconds (1 hour)
- `UPDATE_INTERVAL`: 900 seconds (15 minutes)

## Monitoring

### Check Cache Status

```bash
docker-compose logs cache-updater
```

### View Redis Contents

```bash
docker exec -it serbian-vocab-redis redis-cli
> KEYS news:*
> GET news:last_update
```

## Future Enhancements

1. **Cache Warming**
   - Pre-fetch popular categories on startup
   - Prioritize frequently accessed content

2. **Smart Caching**
   - Track user preferences
   - Cache personalized content

3. **Cache Analytics**
   - Track hit/miss rates
   - Optimize cache strategy based on usage

4. **Error Recovery**
   - Retry failed fetches
   - Alert on persistent failures

## Troubleshooting

### Cache Not Updating

1. Check cache-updater logs: `docker-compose logs cache-updater`
2. Verify Redis is running: `docker-compose ps`
3. Check Redis connectivity: `docker exec -it serbian-vocab-backend redis-cli ping`

### Articles Not Cached

1. Check RSS feed availability
2. Verify network connectivity
3. Check for parsing errors in logs

### Performance Issues

1. Monitor Redis memory usage
2. Adjust cache expiry if needed
3. Consider increasing Redis memory limits
