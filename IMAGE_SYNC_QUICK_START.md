# Image Sync Service - Quick Start Guide

## Overview

This guide will help you quickly deploy and test the new separated image sync service.

## Prerequisites

- Docker and Docker Compose installed
- Unsplash API key (set in `.env` file)
- Redis and PostgreSQL (included in docker-compose)

## Quick Start

### 1. Environment Setup

Ensure your `.env` file contains the Unsplash API key:

```bash
# Check if UNSPLASH_ACCESS_KEY is set
grep UNSPLASH_ACCESS_KEY serbian-vocabulary-app/.env
```

If not set, add it:

```bash
echo "UNSPLASH_ACCESS_KEY=your_unsplash_api_key_here" >> serbian-vocabulary-app/.env
```

### 2. Start All Services

```bash
cd serbian-vocabulary-app
docker-compose up -d

# Check all services are running
docker-compose ps
```

### 3. Test the Image Sync Service

Run the comprehensive test script:

```bash
cd serbian-vocabulary-app
python test_image_sync_service.py
```

Or for a quick test:

```bash
python test_image_sync_service.py --quick
```

### 4. Monitor the Service

Watch the image sync service logs in real-time:

```bash
docker-compose logs -f image-sync-service
```

## Expected Service Behavior

### Initial Startup

```
🚀 Starting Image Sync Service
Rate limit: 25 requests/hour
Processing interval: 120 seconds
📭 Queue empty, waiting for new items...
```

### Processing Items

```
📤 Processing queued item: 'мачка' (queued 2.3m ago)
🔍 Searching Unsplash for: 'cat' (request #15)
Found 3 results for 'cat'
📥 Downloading image for 'мачка' from John Smith
✅ Processed image: 400x300 → 400x300, 45KB → 32KB (28.9% compression)
✅ Cached successful result for 'мачка' (TTL: 30 days)
⏱️  Processed 'мачка' in 5.21s
⏳ Waiting 120 seconds before next request...
```

### Rate Limiting

```
⏸️ Rate limit reached (25/25), waiting 5 minutes...
```

## Service Management

### Start Only Image Sync Service

```bash
docker-compose up -d image-sync-service
```

### Restart Image Sync Service

```bash
docker-compose restart image-sync-service
```

### Stop Image Sync Service

```bash
docker-compose stop image-sync-service
```

### View Service Status

```bash
docker-compose ps image-sync-service
```

### View Service Logs

```bash
# Live logs
docker-compose logs -f image-sync-service

# Last 100 lines
docker-compose logs --tail=100 image-sync-service

# All logs
docker-compose logs image-sync-service
```

## Monitoring and Statistics

### Backend API Endpoints

Access these through your application's backend API (requires authentication):

- **Queue Status**: `GET /api/images/background/status`
- **Cache Statistics**: `GET /api/images/cache/stats`
- **Populate Images**: `POST /api/images/background/populate`

### Redis Direct Monitoring

```bash
# Connect to Redis
docker exec -it serbian-vocab-redis redis-cli

# Check queue length
LLEN image_queue

# Check cached images count
EVAL "return #redis.call('keys', 'word_image:*')" 0

# Check rate limit
GET unsplash_rate_limit:$(date +%s | awk '{print int($1/3600)}')

# Check processing lock
GET image_processing_lock
```

## Troubleshooting

### Common Issues

#### 1. Service Not Starting

```bash
# Check container status
docker-compose ps image-sync-service

# Check logs for errors
docker-compose logs image-sync-service

# Common fixes:
docker-compose build image-sync-service
docker-compose up -d image-sync-service
```

#### 2. No Images Being Processed

```bash
# Check if service is running
docker-compose ps image-sync-service

# Check if there are items in queue
python test_image_sync_service.py --quick

# Check Redis connectivity
docker exec -it serbian-vocab-redis redis-cli ping
```

#### 3. Rate Limit Issues

```bash
# Check current rate limit status
python -c "
import redis, time
r = redis.from_url('redis://localhost:6379', decode_responses=True)
hour = int(time.time() // 3600)
count = r.get(f'unsplash_rate_limit:{hour}') or 0
print(f'Current requests this hour: {count}/25')
"
```

#### 4. Permission Issues

```bash
# Fix log directory permissions
sudo chown -R $(id -u):$(id -g) serbian-vocabulary-app/image-sync-service
```

### Log Analysis

**Successful Processing Pattern**:

1. `📤 Processing queued item` - Item picked up from queue
2. `🔍 Searching Unsplash` - API request made
3. `📥 Downloading image` - Image download started
4. `✅ Processed image` - Image processed and optimized
5. `✅ Cached successful result` - Result stored in Redis

**Error Patterns to Watch For**:

- `❌ Error searching Unsplash` - API issues
- `❌ Error downloading/processing image` - Image processing issues
- `Error connecting to Redis` - Redis connectivity issues
- `UNSPLASH_ACCESS_KEY not found` - Configuration issue

## Performance Expectations

### Typical Performance Metrics

- **Processing Rate**: 1 word every 2 minutes (rate-limited)
- **Queue Processing**: Continuous when items available
- **Image Optimization**: 20-40% size reduction
- **Cache Hit Rate**: 85-95% for established vocabularies
- **Memory Usage**: 50-100MB per service instance

### Rate Limiting

- **Limit**: 25 requests per hour (conservative)
- **Unsplash Limit**: 50 requests per hour (demo account)
- **Behavior**: Service waits when limit reached
- **Recovery**: Automatic resumption when window resets

## Advanced Configuration

### Environment Variables

Customize service behavior through environment variables in `docker-compose.yml`:

```yaml
environment:
  REDIS_URL: redis://redis:6379
  UNSPLASH_ACCESS_KEY: ${UNSPLASH_ACCESS_KEY}
  LOG_LEVEL: INFO  # DEBUG, INFO, WARNING, ERROR
  LOG_FILE: /app/logs/image-sync.log  # Optional log file
```

### Scaling

To run multiple image sync service instances:

```yaml
# In docker-compose.yml
image-sync-service:
  # ... existing configuration
  deploy:
    replicas: 2  # Run 2 instances
```

Or manually:

```bash
# Start additional instance
docker-compose up -d --scale image-sync-service=2
```

## Integration Testing

### Test Complete Flow

1. **Add words to user vocabulary** (through web app)
2. **Trigger image population** (`POST /api/images/background/populate`)
3. **Monitor processing** (`docker-compose logs -f image-sync-service`)
4. **Verify images cached** (`GET /api/images/cache/stats`)
5. **Check word images** (through web app vocabulary page)

### API Testing

```bash
# Using curl (requires authentication token)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:3001/api/images/background/status

curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:3001/api/images/cache/stats
```

## Next Steps

1. **Monitor Initial Run**: Watch logs for first few processed images
2. **Populate Vocabulary**: Add words and trigger image population
3. **Performance Tuning**: Adjust rate limits if you have Unsplash Pro
4. **Monitoring Setup**: Set up alerts for service health
5. **Backup Strategy**: Plan for Redis cache backup if needed

## Support

For issues or questions:

1. Check service logs: `docker-compose logs image-sync-service`
2. Run test script: `python test_image_sync_service.py`
3. Review architecture documentation: `IMAGE_SYNC_SERVICE_ARCHITECTURE.md`
4. Check Redis connectivity: `docker exec -it serbian-vocab-redis redis-cli ping`

## Summary

The separated image sync service provides:

- ✅ **Reliable Background Processing**: Images processed independently
- ✅ **Detailed Logging**: Comprehensive monitoring and debugging
- ✅ **Rate Limit Management**: Conservative API usage within limits
- ✅ **Scalable Architecture**: Can run multiple instances
- ✅ **Easy Monitoring**: Multiple ways to check service health
- ✅ **Graceful Degradation**: Main app works even if service is down

The service runs continuously, processing queued image requests and caching results for immediate future access.
