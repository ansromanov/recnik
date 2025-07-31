# Serbian Vocabulary Learning App

A web application for learning Serbian vocabulary with automatic translation, categorization, and practice exercises. The app uses PostgreSQL for data storage, OpenAI API for translations, and runs entirely in Docker containers.

## Features

- **Text Processing**: Paste Serbian text to automatically extract and translate new vocabulary
- **Word Categories**: Organize words into categories (Verbs, Nouns, Food & Drink, etc.)
- **Vocabulary Management**: View and search your saved words with mastery tracking
- **Practice Mode**: Interactive exercises to test your knowledge
- **Progress Tracking**: Monitor your learning progress with statistics and session history
- **Fully Containerized**: Everything runs in Docker for easy setup

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key (get one from [OpenAI Platform](https://platform.openai.com/api-keys))

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
2. You'll see Serbian words one by one
3. Type the English translation
4. Press Enter to submit
5. Track your progress throughout the session

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

- **categories**: Word categories (Verbs, Nouns, etc.)
- **words**: Serbian words with translations
- **user_vocabulary**: Tracks user's learning progress
- **practice_sessions**: Practice session records
- **practice_results**: Individual practice results

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/categories` - Get all categories
- `GET /api/words` - Get all words (with optional category filter)
- `POST /api/process-text` - Process Serbian text and get translations
- `POST /api/words` - Add new words to vocabulary
- `GET /api/practice/words` - Get words for practice
- `POST /api/practice/start` - Start a practice session
- `POST /api/practice/submit` - Submit practice result
- `POST /api/practice/complete` - Complete practice session
- `GET /api/stats` - Get user statistics

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
