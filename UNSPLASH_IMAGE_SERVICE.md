# Rate-Limited Unsplash Image Service

This document explains how to set up and use the new rate-limited Unsplash-based image service for the Serbian Vocabulary App.

## Overview

The image service has been completely redesigned with aggressive rate limiting and background processing to stay well under API limits. This provides:

- **Aggressive rate limiting**: Maximum 25 requests per hour (well under the 30/hour limit)
- **Background processing**: Images are processed slowly in the background (2 minutes between requests)
- **Aggressive caching**: Images cached for 30 days instead of 7 days
- **Queue-based system**: All image requests are queued and processed asynchronously
- **Distributed locking**: Safe for multiple server instances
- **High-quality images**: Professional photography from Unsplash
- **Legal compliance**: All images are free to use under Unsplash license
- **Attribution support**: Photographer credits are included

## Setup Instructions

### 1. Get Unsplash API Access

1. Go to [Unsplash Developers](https://unsplash.com/developers)
2. Create a free account if you don't have one
3. Create a new application
4. Copy your **Access Key** (starts with something like `abc123...`)

### 2. Configure Environment Variables

Add your Unsplash access key to your environment file:

```bash
# In serbian-vocabulary-app/backend/.env
UNSPLASH_ACCESS_KEY=your-unsplash-access-key-here
```

Or copy from the example:

```bash
cp serbian-vocabulary-app/backend/.env.example serbian-vocabulary-app/backend/.env
```

Then edit the `.env` file and add your Unsplash access key.

### 3. Test the Service

You can test the image service without running the full app:

```bash
cd serbian-vocabulary-app
python test_unsplash_images.py
```

This will:

- Check if your Unsplash API key is configured
- Test Redis connection
- Search for images for common Serbian words
- Display cache statistics

### 4. Restart the Application

After adding the Unsplash API key, restart your Flask application:

```bash
# If using Docker
docker-compose down
docker-compose up

# If running directly
cd serbian-vocabulary-app/backend
python app.py
```

## API Endpoints

The following endpoints are available for image management:

### Get Image for a Word

```http
GET /api/words/{word_id}/image
Authorization: Bearer <jwt_token>
```

### Search for Image

```http
POST /api/images/search
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "serbian_word": "pas",
  "english_translation": "dog"
}
```

### Clear Image Cache

```http
POST /api/images/cache/clear
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "serbian_word": "pas"
}
```

### Get Cache Statistics

```http
GET /api/images/cache/stats
Authorization: Bearer <jwt_token>
```

### Background Processing Endpoints

#### Get Background Status

```http
GET /api/images/background/status
Authorization: Bearer <jwt_token>
```

Returns queue length, rate limit status, and processing status.

#### Populate Images for User's Vocabulary

```http
POST /api/images/background/populate
Authorization: Bearer <jwt_token>
```

Adds all user's vocabulary words to the background processing queue.

#### Get Image Immediately (Testing)

```http
POST /api/images/immediate
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "serbian_word": "pas",
  "english_translation": "dog"
}
```

Processes image immediately if rate limit allows (for testing/admin use).

## Response Format

Successful image responses include:

```json
{
  "success": true,
  "image": {
    "image_data": "base64-encoded-image-data",
    "content_type": "image/jpeg",
    "width": 400,
    "height": 300,
    "size": 15420,
    "search_query": "dog",
    "photographer": "John Doe",
    "unsplash_id": "abc123",
    "alt_description": "A cute dog sitting in grass",
    "cached_at": 1643723400,
    "source": "unsplash"
  }
}
```

## Search Strategy

The service uses a smart search strategy:

1. **Primary search**: Uses English translation (e.g., "dog")
2. **Category-enhanced search**: For common categories, adds "object" (e.g., "dog object")
3. **Fallback search**: Uses Serbian word directly

Images are filtered for:

- **Quality**: High content filter enabled
- **Orientation**: Prefers square-ish images for better display
- **Size**: Resized to max 400x400 pixels for performance
- **Format**: Converted to JPEG for consistency

## Caching

- **Redis caching**: Images are cached for 7 days
- **Automatic cleanup**: Failed searches are cached to avoid repeated attempts
- **Cache management**: Clear individual words or get statistics
- **Size optimization**: Images are resized and optimized before caching

## Rate Limits

Unsplash has the following rate limits for free accounts:

- **50 requests per hour** for development
- **5,000 requests per hour** for production (after approval)

The caching system helps minimize API calls by storing results for 7 days.

## Troubleshooting

### Common Issues

1. **"UNSPLASH_ACCESS_KEY not found"**
   - Make sure you've added the key to your `.env` file
   - Restart the application after adding the key

2. **"No suitable image found"**
   - Some words might not have good matches on Unsplash
   - Try using more common English translations
   - The service caches failed searches to avoid repeated attempts

3. **Redis connection errors**
   - Make sure Redis is running
   - Check your `REDIS_URL` environment variable

4. **Rate limit exceeded**
   - Wait for the rate limit to reset (hourly)
   - Consider upgrading to a production Unsplash account

### Debug Mode

To enable more detailed logging, set debug mode in your application:

```python
# In app.py
app.run(host="0.0.0.0", port=port, debug=True)
```

This will show detailed error messages and API responses.

## Migration from Google Images

The old Google Images scraping service has been completely replaced. Key changes:

- **No more web scraping**: Uses official Unsplash API
- **Better attribution**: Photographer credits are preserved
- **Consistent quality**: All images are high-quality professional photos
- **Legal compliance**: All images are free to use
- **No blocking**: No more IP blocking or captcha issues

## License and Attribution

Images from Unsplash are provided under the [Unsplash License](https://unsplash.com/license):

- Free to use for any purpose
- No permission needed
- Attribution appreciated but not required

The service includes photographer attribution in the response data for proper crediting.

## Support

If you encounter issues:

1. Run the test script: `python test_unsplash_images.py`
2. Check the application logs for detailed error messages
3. Verify your Unsplash API key is valid and has remaining quota
4. Ensure Redis is running and accessible

For more help, check the Unsplash API documentation at: <https://unsplash.com/documentation>
