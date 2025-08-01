# Serbian Vocabulary App - Automated Setup Guide

This guide provides automated setup instructions for the Serbian Vocabulary App with auto-advance functionality.

## 🚀 Quick Start (Fully Automated)

### Prerequisites

- Docker and Docker Compose installed
- Make utility (available on most Unix systems)

### One-Command Setup

```bash
make setup-full
```

This single command will:

1. Create environment configuration files
2. Build all Docker containers with test dependencies
3. Start all services (database, backend, frontend, monitoring)
4. Run database migrations automatically
5. Execute comprehensive tests to verify everything works
6. Display access URLs

## 📋 What Gets Automated

### ✅ Database Setup

- PostgreSQL database with proper schema
- Auto-advance settings migration applied automatically
- All required tables and indexes created

### ✅ Backend Services

- Flask/Gunicorn application server
- All Python dependencies including test frameworks
- Automatic database connection waiting
- Migration execution on startup

### ✅ Frontend Application

- React application with auto-advance UI
- Settings page with timeout configuration
- Practice page with timer functionality

### ✅ Testing Environment

- pytest and all testing dependencies pre-installed
- Comprehensive test suite execution
- Verification of auto-advance functionality

## 🔧 Available Commands

### Setup Commands

```bash
make setup          # Basic setup (no testing)
make setup-full      # Complete setup with testing
make dev-setup       # Quick development environment
```

### Development Commands

```bash
make up              # Start services
make down            # Stop services
make restart         # Restart all services
make test            # Run tests
make logs            # View logs
```

### Build Commands

```bash
make build           # Build all containers
make rebuild-all     # Rebuild everything from scratch
```

## 🎯 Auto-Advance Feature

The auto-advance functionality is fully configured and tested:

### Backend Features

- ✅ Database schema with auto-advance settings
- ✅ API endpoints for configuration
- ✅ User-specific timeout settings (1-10 seconds)
- ✅ Default values and validation

### Frontend Features

- ✅ Settings page with enable/disable toggle
- ✅ Configurable timeout slider (1-10 seconds)
- ✅ Practice page with automatic timer
- ✅ Manual override capability

### Testing Coverage

- ✅ All backend API endpoints tested
- ✅ Database model validation
- ✅ Settings persistence verification
- ✅ Comprehensive test suite (110+ tests)

## 🌐 Access URLs

After running `make setup-full`, access the application at:

- **Frontend Application**: <http://localhost:80>
- **Backend API**: <http://localhost:3000>
- **Grafana Monitoring**: <http://localhost:3001> (admin/admin)
- **API Health Check**: <http://localhost:3000/api/health>

## 🔍 Verification Steps

The automated setup includes verification:

1. **Database Connection**: Waits for PostgreSQL to be ready
2. **Migration Execution**: Applies auto-advance schema changes
3. **Service Health**: Checks all containers are running
4. **API Functionality**: Tests all endpoints
5. **Auto-advance Logic**: Validates timer functionality

## 🛠️ Manual Override (if needed)

If you need to run steps manually:

```bash
# 1. Environment setup
cp .env.example .env
cp backend/.env.example backend/.env

# 2. Build and start
docker-compose build
docker-compose up -d

# 3. Wait for database and run migrations
sleep 15
docker exec serbian-vocab-backend python migrations/add_auto_advance_settings.py

# 4. Install test dependencies (if needed)
docker exec serbian-vocab-backend pip install -r requirements-test.txt

# 5. Run tests
docker exec serbian-vocab-backend python -m pytest tests/ -v
```

## 🏃‍♂️ Usage

1. **Run Setup**: `make setup-full`
2. **Open App**: Navigate to <http://localhost:80>
3. **Register/Login**: Create a user account
4. **Configure Auto-advance**: Go to Settings page
   - Enable "Auto-advance to next word after answer"
   - Set desired timeout (1-10 seconds)
5. **Practice**: Use the Practice page with automatic advancement

## 🧪 Testing

The automated setup runs comprehensive tests including:

- Database model tests
- API endpoint tests
- Settings functionality tests
- Auto-advance logic validation
- Cache and Redis tests
- Image service tests

## 🔧 Troubleshooting

If setup fails:

```bash
# Check container status
make status

# View logs
make logs

# Clean and retry
make clean
make setup-full
```

## 📈 Monitoring

Grafana dashboards are automatically configured at <http://localhost:3001> with:

- Application metrics
- Database performance
- API response times
- Error tracking

The automated setup ensures zero manual intervention for a fully functional Serbian vocabulary learning application with auto-advance capabilities.
