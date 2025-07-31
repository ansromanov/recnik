# How to Apply the Latest Updates

If you're running the application and want to apply the latest changes (automatic categorization, select/deselect all buttons, and 50-word limit), follow these steps:

## 1. Stop the Running Containers

```bash
cd serbian-vocabulary-app
docker-compose down
```

## 2. Rebuild the Containers

Since we've made changes to the source code and added new dependencies, you need to rebuild the Docker images:

```bash
docker-compose build --no-cache
```

**IMPORTANT**: This step is crucial for the News feature to work, as it installs the new RSS parser dependencies.

## 3. Start the Updated Application

```bash
docker-compose up -d
```

## 4. Verify the Changes

Once the containers are running, you can verify the updates:

1. Go to <http://localhost:3000>
2. Navigate to "Process Text"
3. You should see:
   - Select All / Deselect All buttons when processing text
   - Words automatically categorized by the AI
   - The tips mentioning "up to 50 new words"
4. Navigate to "News" to see the new feature:
   - Real-time Serbian news from N1 Info (Latin script)
   - Ability to extract vocabulary from actual news articles
   - Automatic word categorization
   - Updates with fresh content from RSS feed

## Alternative: Development Mode

If you're developing and want to see changes immediately without rebuilding:

```bash
# Terminal 1: Start only the database
docker-compose up -d postgres

# Terminal 2: Run backend in development mode
cd backend
npm install
npm run dev

# Terminal 3: Run frontend in development mode
cd frontend
npm install
npm start
```

## What Changed

### Backend (server.js & package.json)

- Modified `/api/process-text` endpoint to use AI for categorization
- Increased word limit from 20 to 50
- AI now returns both translation and category in JSON format
- Added verb infinitive transformation (e.g., "радим" → "радити")
- Converts words to lowercase except proper nouns
- **NEW**: Removes duplicate words during processing (same infinitive forms)
- **NEW**: Practice mode now provides multiple choice options (4 choices)
- **NEW**: Added endpoint to generate example sentences with OpenAI
- **NEW**: Added `/api/news` endpoint that fetches real Serbian news from N1 Info RSS feed
- **NEW**: Added dependencies: `rss-parser` and `axios` for RSS feed parsing

### Frontend (TextProcessorPage.js)

- Added Select All / Deselect All buttons
- Updated to use AI-assigned categories
- Updated tips to reflect 50-word limit
- Shows original form when different from infinitive
- Added tips about infinitive transformation

### Frontend (PracticePage.js)

- **NEW**: Changed from text input to multiple choice questions
- **NEW**: Shows 4 answer options for each word
- **NEW**: Displays example sentences for correct answers
- **NEW**: Highlights the Serbian word in green within example sentences
- **NEW**: Visual feedback with colored buttons (green for correct, red for wrong)

### Frontend (NewsPage.js) - **NEW FEATURE**

- **NEW**: Serbian News Reader page
- **NEW**: Fetches real-time news from N1 Info RSS feed (Latin script)
- **NEW**: Displays up to 10 latest Serbian news articles
- **NEW**: Click on an article to read the full content
- **NEW**: "Extract Vocabulary" button to find new words in articles
- **NEW**: Highlights extracted words in the article text
- **NEW**: Select/deselect words to add to your vocabulary
- **NEW**: Automatically processes and categorizes words from news
- **NEW**: Falls back to sample articles if RSS feed is unavailable

### Frontend (App.js)

- **NEW**: Added News navigation link and route

## Troubleshooting

If the changes don't appear:

1. **Clear browser cache**: Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
2. **Check logs**: `docker-compose logs backend` or `docker-compose logs frontend`
3. **Ensure containers rebuilt**: The build step is crucial for changes to take effect
4. **Verify .env file**: Make sure your OpenAI API key is properly set

**News Feature 502 Error**: If you get a 502 error on the News page, it means the backend needs to be rebuilt to install the RSS parser dependencies. Run:

```bash
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d
```

## Quick Command Summary

```bash
# Complete rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check if everything is running
docker-compose ps

# View logs if needed
docker-compose logs -f
