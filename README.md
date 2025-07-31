# Serbian Vocabulary Learning App

A web application for learning Serbian vocabulary with automatic translation, categorization, and practice exercises. The app uses PostgreSQL for data storage, OpenAI API for translations, and runs entirely in Docker containers.

## Features

- **User Authentication**: Secure login system with individual user accounts
- **Personal Vocabulary**: Each user maintains their own vocabulary list and progress
- **Text Processing**: Paste Serbian text to automatically extract and translate new vocabulary
- **Serbian News Reader**: Read real-time Serbian news from N1 Info RSS feed and extract vocabulary
- **Word Categories**: Organize words into categories (Verbs, Nouns, Food & Drink, etc.)
- **Vocabulary Management**: View and search your saved words with mastery tracking
- **Practice Mode**: Interactive multiple-choice exercises to test your knowledge
- **Progress Tracking**: Monitor your learning progress with statistics and session history
- **Example Sentences**: See words used in context with AI-generated examples
- **Fully Containerized**: Everything runs in Docker for easy setup

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key (get one from [OpenAI Platform](https://platform.openai.com/api-keys))

## Important: Database Migrations

After setting up the application for the first time, you need to run database migrations:

1. **Authentication tables** (if not already done):

   ```bash
   docker-compose exec backend python add_auth_tables.py
   ```

2. **User-specific vocabulary** (NEW - Required for user-specific features):

   ```bash
   docker-compose exec backend python add_user_relationships.py
   ```

See [RUN_USER_MIGRATION.md](RUN_USER_MIGRATION.md) for detailed migration instructions.

## Quick Start

1. **Clone or download this project**

2. **Set up your OpenAI API key**

   ```bash
   cd serbian-vocabulary-app
   cp backend/.env.example backend/.env
   ```

   Edit `backend/.env` and replace `your-openai-api-key-here` with your actual OpenAI API key.

3. **Start the application**

   ```bash
   docker-compose up -d
   ```

4. **Access the app**
   - Open your browser and go to <http://localhost:3000>
   - The backend API runs on <http://localhost:3001>
   - PostgreSQL database runs on localhost:5432

## Usage Guide

### Adding New Words

1. Go to "Process Text" page
2. Paste any Serbian text
3. Click "Process Text" to extract and translate words
4. Select words you want to save and assign categories
5. Click "Save Selected Words"

### Practicing Vocabulary

1. Go to "Practice" page
2. You'll see Serbian words with multiple choice options
3. Select the correct English translation
4. View example sentences for correct answers
5. Track your progress throughout the session

### Reading Serbian News

1. Go to "News" page
2. Browse latest Serbian news from N1 Info (automatically fetched from RSS)
3. Click on an article to read it
4. Click "Extract Vocabulary" to find new words
5. Select words to add to your vocabulary
6. All articles are in Latin script for easier reading

### Viewing Your Vocabulary

1. Go to "My Vocabulary" page
2. Filter by category or search for specific words
3. View mastery level and practice statistics for each word

## Project Structure

```
serbian-vocabulary-app/
├── backend/               # Node.js Express API
│   ├── server.js         # Main server file
│   ├── package.json      # Backend dependencies
│   └── Dockerfile        # Backend container config
├── frontend/             # React application
│   ├── src/
│   │   ├── pages/       # React page components
│   │   ├── services/    # API service layer
│   │   └── App.js       # Main React component
│   ├── package.json     # Frontend dependencies
│   └── Dockerfile       # Frontend container config
├── database/
│   └── init.sql         # Database schema and initial data
└── docker-compose.yml   # Docker orchestration config
```

## Database Schema

- **users**: User accounts with authentication
- **settings**: User-specific settings (OpenAI API keys)
- **categories**: Word categories (Verbs, Nouns, etc.)
- **words**: Serbian words with translations
- **user_vocabulary**: Tracks each user's vocabulary and learning progress
- **practice_sessions**: User-specific practice session records
- **practice_results**: Individual practice results per session

## API Endpoints

### Authentication (No auth required)

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user (requires auth)

### Settings (Requires authentication)

- `GET /api/settings` - Get user settings
- `PUT /api/settings` - Update user settings (OpenAI API key)

### Vocabulary (Most require authentication)

- `GET /api/health` - Health check
- `GET /api/categories` - Get all categories
- `GET /api/words` - Get words with user-specific progress (requires auth)
- `POST /api/process-text` - Process Serbian text and get translations (requires auth)
- `POST /api/words` - Add new words to user's vocabulary (requires auth)

### Practice (All require authentication)

- `GET /api/practice/words` - Get words for practice from user's vocabulary
- `POST /api/practice/start` - Start a practice session
- `POST /api/practice/submit` - Submit practice result
- `POST /api/practice/complete` - Complete practice session
- `POST /api/practice/example-sentence` - Generate example sentence for a word

### Statistics & News

- `GET /api/stats` - Get user-specific statistics (requires auth)
- `GET /api/news` - Get Serbian news articles (no auth required)
- `GET /api/news/sources` - Get available news sources (no auth required)

## Development

To run in development mode with hot reloading:

```bash
# Start only the database
docker-compose up -d postgres

# In one terminal, start the backend
cd backend
npm install
npm run dev

# In another terminal, start the frontend
cd frontend
npm install
npm start
```

## Stopping the Application

```bash
docker-compose down
```

To also remove the database volume (this will delete all your saved words):

```bash
docker-compose down -v
```

## Troubleshooting

1. **Port conflicts**: If ports 3000, 3001, or 5432 are already in use, modify the port mappings in `docker-compose.yml`

2. **OpenAI API errors**: Make sure your API key is valid and has credits

3. **Database connection issues**: Ensure the database container is running with `docker-compose ps`

4. **Container build issues**: Try rebuilding with `docker-compose build --no-cache`

## License

This project is open source and available for educational purposes.
