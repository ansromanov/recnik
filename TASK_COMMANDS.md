# Serbian Vocabulary App - Task Commands & Features

## 🚀 Quick Start Commands

Use these commands for common development tasks:

```bash
# Show all available commands
make help

# Start the application
make up

# Stop the application
make down

# Restart all services
make restart

# View logs
make logs

# Follow logs in real-time
make logs-follow
```

## 🛠️ Build Commands

```bash
# Build all services
make build

# Rebuild only frontend (recommended after UI changes)
make rebuild-frontend

# Rebuild only Grafana (for monitoring updates)
make rebuild-grafana

# Rebuild all services from scratch
make rebuild-all
```

## 💾 Database Commands

```bash
# Run database migrations
make migrate

# Open PostgreSQL shell
make db-shell

# Open Redis shell
make redis-shell

# Create database backup
make backup-db

# Restore database from backup
make restore-db
```

## 🧹 Maintenance Commands

```bash
# Clean unused Docker resources
make clean

# Clean all Docker resources (⚠️ destructive)
make clean-all

# Run backend tests
make test

# Show container status
make status
```

## 🌐 Quick Access Commands

```bash
# Open application in browser (http://localhost:3000)
make open-app

# Open Grafana dashboard (http://localhost:3001)
make open-grafana
```

## ⚡ Development Helpers

```bash
# Quick restart (backend + frontend only)
make quick-restart

# View development logs (backend + frontend)
make dev-logs

# Access backend shell
make backend-shell

# Access frontend shell
make frontend-shell

# Install/update dependencies
make install-deps
```

## 🎯 Setup & Deployment

```bash
# Complete setup from scratch
make setup

# Production deployment
make prod-deploy
```

---

## 🚫 Excluded Words Feature

### Overview

The excluded words feature allows users to manage words they don't want to learn, preventing them from appearing in practice sessions and lessons.

### Key Features

#### 1. **Manual Word Exclusion**

- Remove words from vocabulary using the "❌ Remove" button on each word card
- Words are moved to the excluded words list with reason "manual_removal"
- Excluded words won't appear in practice sessions

#### 2. **Automatic News Parser Exclusion**

- When processing news articles, unselected words are automatically excluded
- Prevents the same unwanted words from appearing in future lessons
- Marked with reason "news_parser_skip"

#### 3. **Excluded Words Management**

- View all excluded words in a collapsible table on the vocabulary page
- See exclusion reason, date, and word details
- **Restore** words back to vocabulary
- **Delete** words permanently from excluded list

#### 4. **Statistics Integration**

- Excluded words count is shown in vocabulary statistics
- Tracks manual vs automatic exclusions

### API Endpoints

```bash
# Get user's excluded words
GET /api/excluded-words

# Remove word from vocabulary and exclude it
POST /api/words/{id}/exclude

# Remove word from excluded list
DELETE /api/excluded-words/{id}

# Bulk exclude multiple words (used by news parser)
POST /api/excluded-words/bulk
```

### Database Schema

The `excluded_words` table includes:

- `user_id` - Links to the user who excluded the word
- `word_id` - Links to the excluded word
- `reason` - Why the word was excluded ("manual_removal", "news_parser_skip")
- `created_at` - When the word was excluded

### Usage Examples

#### Exclude a word manually

1. Go to vocabulary page
2. Click "❌ Remove" on any word
3. Confirm the action
4. Word moves to excluded list

#### Process news articles

1. Go to news page
2. Extract vocabulary from an article
3. Select only words you want to learn
4. Click "Save X Words"
5. Unselected words are automatically excluded

#### Manage excluded words

1. Go to vocabulary page
2. Click "Show" next to "Excluded Words"
3. Use "↩️ Restore" to add words back to vocabulary
4. Use "🗑️ Delete" to remove from excluded list permanently

### Benefits

- **Improved Learning Experience**: Focus only on words you want to learn
- **Reduced Clutter**: Unwanted words don't reappear in lessons
- **Flexible Management**: Easy to restore or permanently remove words
- **Automatic Filtering**: News parser respects your word preferences
- **User Isolation**: Each user has their own excluded words list

---

## 📊 Monitoring

- **Application**: <http://localhost:3000>
- **Grafana Dashboard**: <http://localhost:3001> (admin/admin)
- **Prometheus Metrics**: <http://localhost:9090>

---

## 🔧 Development Workflow

1. **Make changes** to code
2. **Rebuild services** using `make rebuild-frontend` or `make rebuild-grafana`
3. **Check logs** with `make logs` or `make dev-logs`
4. **Test changes** in browser
5. **Run migrations** with `make migrate` if database changes
6. **Monitor** with `make status`

---

## 📝 Notes

- All commands work from the `serbian-vocabulary-app` directory
- Docker and Docker Compose are required
- Frontend rebuilds take longer due to React build process
- Database migrations are automatically run during setup
- Use `make clean` regularly to free up disk space
