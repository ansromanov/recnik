# How to Apply the Latest Updates

If you're running the application and want to apply the latest changes (automatic categorization, select/deselect all buttons, and 50-word limit), follow these steps:

## 1. Stop the Running Containers

```bash
cd serbian-vocabulary-app
docker-compose down
```

## 2. Rebuild the Containers

Since we've made changes to the source code, you need to rebuild the Docker images:

```bash
docker-compose build --no-cache
```

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

### Backend (server.js)

- Modified `/api/process-text` endpoint to use AI for categorization
- Increased word limit from 20 to 50
- AI now returns both translation and category in JSON format
- Added verb infinitive transformation (e.g., "радим" → "радити")
- Converts words to lowercase except proper nouns

### Frontend (TextProcessorPage.js)

- Added Select All / Deselect All buttons
- Updated to use AI-assigned categories
- Updated tips to reflect 50-word limit
- Shows original form when different from infinitive
- Added tips about infinitive transformation

## Troubleshooting

If the changes don't appear:

1. **Clear browser cache**: Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
2. **Check logs**: `docker-compose logs backend` or `docker-compose logs frontend`
3. **Ensure containers rebuilt**: The build step is crucial for changes to take effect
4. **Verify .env file**: Make sure your OpenAI API key is properly set

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
