# Image Sync Service Architecture

## Overview

The image synchronization functionality has been split from the main backend into a separate, containerized service for better scalability, isolation, and detailed logging. This document explains the new architecture.

## Architecture Components

### 1. Image Sync Service (`image-sync-service/`)

**Location**: `serbian-vocabulary-app/image-sync-service/`

**Purpose**: Dedicated service for fetching and caching images from Unsplash API with detailed logging.

**Key Features**:

- ✅ Standalone Python service with comprehensive logging
- ✅ Rate-limited API requests (25 requests/hour to stay under Unsplash limits)
- ✅ Redis-based task queue and caching
- ✅ Intelligent image processing and optimization
- ✅ Distributed processing locks to prevent conflicts
- ✅ Detailed statistics and monitoring
- ✅ Containerized with health checks

**Files**:

- `image_sync_worker.py` - Main service worker
- `Dockerfile` - Container definition
- `requirements.txt` - Python dependencies

### 2. Backend Image Service Client (`backend/image_service_client.py`)

**Purpose**: Lightweight client that communicates with the image sync service through Redis.

**Key Features**:

- ✅ Simple interface that queues image requests
- ✅ Returns cached images immediately if available
- ✅ No heavy processing or API calls in main backend
- ✅ Compatible with existing API endpoints

### 3. Communication Layer (Redis)

**Purpose**: Message queue and cache for communication between services.

**Key Components**:

- `image_queue` - Task queue for image processing requests
- `word_image:*` - Cached image data
- `image_processing_lock` - Distributed lock for processing coordination
- `unsplash_rate_limit:*` - Rate limiting counters

## Service Flow

```
1. User requests image through API
   ↓
2. Backend checks Redis cache
   ↓ (if not cached)
3. Backend adds request to Redis queue
   ↓
4. Image Sync Service picks up request
   ↓
5. Service fetches from Unsplash API
   ↓
6. Service processes and caches image
   ↓
7. Image available for future requests
```

## Logging and Monitoring

### Image Sync Service Logs

The service provides detailed logging at multiple levels:

**INFO Level**:

- Service startup/shutdown
- Queue processing status
- API request tracking
- Cache operations
- Statistics summaries

**DEBUG Level**:

- Rate limit checks
- Image processing details
- Redis operations

**ERROR Level**:

- API failures
- Image processing errors
- Cache operation failures

### Log Output Example

```
2025-01-31 23:50:00 | INFO     | ImageSyncService | 🚀 Starting Image Sync Service
2025-01-31 23:50:01 | INFO     | ImageSyncService | 📤 Processing queued item: 'мачка' (queued 2.3m ago)
2025-01-31 23:50:02 | INFO     | ImageSyncService | 🔍 Searching Unsplash for: 'cat' (request #15)
2025-01-31 23:50:03 | INFO     | ImageSyncService | Found 3 results for 'cat'
2025-01-31 23:50:04 | INFO     | ImageSyncService | 📥 Downloading image for 'мачка' from John Smith
2025-01-31 23:50:05 | INFO     | ImageSyncService | ✅ Processed image: 400x300 → 400x300, 45KB → 32KB (28.9% compression)
2025-01-31 23:50:06 | INFO     | ImageSyncService | ✅ Cached successful result for 'мачка' (TTL: 30 days)
2025-01-31 23:50:07 | INFO     | ImageSyncService | ⏱️  Processed 'мачка' in 5.21s
```

## Configuration

### Environment Variables

**Image Sync Service**:

- `REDIS_URL` - Redis connection string
- `UNSPLASH_ACCESS_KEY` - Unsplash API key
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `LOG_FILE` - Optional log file path

**Backend**:

- `REDIS_URL` - Redis connection string (same as image service)

### Docker Compose Configuration

```yaml
image-sync-service:
  build: ./image-sync-service
  container_name: serbian-vocab-image-sync
  environment:
    REDIS_URL: redis://redis:6379
    UNSPLASH_ACCESS_KEY: ${UNSPLASH_ACCESS_KEY}
    LOG_LEVEL: INFO
    LOG_FILE: /app/logs/image-sync.log
  depends_on:
    - redis
  networks:
    - vocab-network
  volumes:
    - ./image-sync-service:/app
    - image_sync_logs:/app/logs
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "python", "-c", "import redis; redis.from_url('redis://redis:6379').ping()"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 30s
```

## Rate Limiting

The service implements conservative rate limiting:

- **Limit**: 25 requests per hour (under Unsplash's 50/hour demo limit)
- **Window**: Rolling 1-hour window
- **Behavior**: Queues requests when limit reached
- **Recovery**: Automatically resumes when window resets

## Image Processing

**Optimization Features**:

- Format conversion to JPEG
- Thumbnail generation (max 400x400px)
- Quality optimization (85% JPEG quality)
- Size compression averaging 20-40% reduction

**Caching Strategy**:

- **Success**: 30 days TTL
- **Failure**: 30 days TTL (prevents repeated failed searches)
- **Retry Logic**: Failed searches retry after 24 hours

## Monitoring Endpoints

The backend provides several endpoints to monitor the image sync service:

### `/api/images/background/status`

Returns current service status:

```json
{
  "status": {
    "queue_length": 15,
    "requests_this_hour": 12,
    "max_requests_per_hour": 25,
    "is_processing": true,
    "service_type": "separate_image_sync_service"
  }
}
```

### `/api/images/cache/stats`

Returns cache statistics:

```json
{
  "stats": {
    "total_cached_words": 1250,
    "cache_size_mb": 45.7,
    "successful_caches": 1100,
    "failed_caches": 150,
    "service_type": "separate_image_sync_service"
  }
}
```

## Deployment

### Starting the Services

```bash
# Start all services including image sync
docker-compose up -d

# Start only image sync service
docker-compose up -d image-sync-service

# View logs
docker-compose logs -f image-sync-service

# Check service status
docker-compose ps image-sync-service
```

### Health Checks

The service includes built-in health checks:

- **Container Health**: Redis connectivity test
- **Service Health**: Processing queue monitoring
- **Rate Limit Health**: API quota tracking

## Benefits of Separated Architecture

### 1. **Scalability**

- Image service can be scaled independently
- No impact on main API performance
- Can run multiple image service instances

### 2. **Reliability**

- Service failures don't affect main application
- Automatic restart policies
- Graceful degradation when unavailable

### 3. **Monitoring**

- Detailed logging specific to image processing
- Isolated metrics and performance tracking
- Clear separation of concerns

### 4. **Resource Management**

- Dedicated resources for image processing
- Better memory management
- Controlled API rate limiting

### 5. **Maintenance**

- Independent updates and deployments
- Easier debugging and troubleshooting
- Service-specific configuration

## Migration from Old Architecture

### What Changed

**Before**:

- Heavy image processing in main backend
- Threading-based background processing
- Mixed logging with other services

**After**:

- Lightweight client in backend
- Separate containerized service
- Dedicated logging and monitoring

### Compatibility

The new architecture maintains full API compatibility:

- All existing endpoints work unchanged
- Same response formats
- Same caching behavior
- Same rate limiting (but more reliable)

### Benefits for Users

- **Faster API responses** (no blocking image processing)
- **Better reliability** (service isolation)
- **Improved logging** (detailed image processing logs)
- **Easier debugging** (clear service boundaries)

## Troubleshooting

### Common Issues

1. **Service Not Processing Queue**
   - Check Redis connectivity
   - Verify Unsplash API key
   - Check service logs: `docker-compose logs image-sync-service`

2. **Rate Limit Exceeded**
   - Monitor `/api/images/background/status`
   - Service automatically waits when limit reached
   - Consider upgrading Unsplash API plan

3. **Images Not Appearing**
   - Check if requests are being queued
   - Verify service is running: `docker-compose ps`
   - Check cache stats for processing status

### Log Analysis

**Key Log Patterns**:

- `🔄 Processing word` - Service actively working
- `📭 Queue empty` - No pending work
- `⏸️ Rate limit reached` - Waiting for quota reset
- `❌ Error` - Processing failures

## Performance Metrics

**Typical Performance**:

- **Queue Processing**: 1 item every 2 minutes (rate-limited)
- **Image Processing**: 2-5 seconds per image
- **Cache Hit Rate**: 85-95% for established vocabularies
- **Compression Ratio**: 20-40% size reduction
- **Memory Usage**: ~50-100MB per service instance

## Future Enhancements

Potential improvements for the image sync service:

1. **Multiple Image Sources**: Support for additional image APIs
2. **Smart Queuing**: Priority-based processing
3. **Batch Processing**: Process multiple images per API call
4. **Advanced Caching**: Intelligent cache warming
5. **Analytics**: Usage statistics and reporting
6. **A/B Testing**: Different image search strategies
