# Recnik

[![codecov](https://codecov.io/gh/ansromanov/recnik/branch/main/graph/badge.svg)](https://codecov.io/gh/ansromanov/recnik)
[![Python Code Quality](https://github.com/ansromanov/recnik/actions/workflows/python-quality.yml/badge.svg)](https://github.com/ansromanov/recnik/actions/workflows/python-quality.yml)
[![Build and Push Docker Images](https://github.com/ansromanov/recnik/actions/workflows/docker-build.yml/badge.svg)](https://github.com/ansromanov/recnik/actions/workflows/docker-build.yml)

A modern microservices-based Serbian vocabulary learning application with comprehensive observability and monitoring.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Required API keys (see API Keys section below)

### Required API Keys

| API Service | Purpose | Get API Key | Environment Variable |
|-------------|---------|-------------|---------------------|
| OpenAI | Text processing and translations | [OpenAI Platform](https://platform.openai.com) | `OPENAI_API_KEY` |
| Unsplash | Vocabulary word images | [Unsplash Developers](https://unsplash.com/developers) | `UNSPLASH_ACCESS_KEY` |
| ResponsiveVoice | Text-to-speech functionality | [ResponsiveVoice.org API](https://responsivevoice.org/api/) | `RESPONSIVEVOICE_API_KEY` |

### Setup

1. Clone and configure:

```bash
git clone <repository-url>
cd recnik
cp .env.example .env
# Edit .env with your API keys (see API Keys section above)
```

2. Start all services:

```bash
make setup
# OR
docker-compose up -d
```

3. Access:

- **Application**: <http://localhost:3000>
- **API Gateway**: <http://localhost:3001>
- **Monitoring**: <http://localhost:3100> (Grafana)

## Architecture

The application follows a microservices architecture with 5 core services, background workers, and monitoring infrastructure:

```mermaid
architecture-beta
    group frontend(cloud)[Frontend Layer]
    group api(cloud)[API Layer]
    group services(cloud)[Microservices]
    group background(cloud)[Background Services]
    group data(database)[Data Layer]
    group monitoring(cloud)[Monitoring]
    group external(internet)[External APIs]

    service user(internet)[User] in frontend
    service react(server)[React App :3000] in frontend

    service gateway(server)[API Gateway :3001] in api

    service auth(server)[Auth Service :3002] in services
    service vocab(server)[Vocabulary Service :3003] in services
    service practice(server)[Practice Service :3004] in services
    service news(server)[News Service :3005] in services

    service imagesync(server)[Image Sync Service] in background
    service cacheupdater(server)[Cache Updater] in background
    service queuepop(server)[Queue Populator] in background

    service postgres(database)[PostgreSQL :5432] in data
    service redis(database)[Redis :6379] in data

    service prometheus(server)[Prometheus :9090] in monitoring
    service grafana(server)[Grafana :3100] in monitoring

    service openai(internet)[OpenAI API] in external
    service unsplash(internet)[Unsplash API] in external
    service responsivevoice(internet)[ResponsiveVoice API] in external
    service rss(internet)[RSS Feeds] in external

    user:R --> L:react
    react:R --> L:gateway
    gateway:R --> L:auth
    gateway:R --> L:vocab
    gateway:R --> L:practice
    gateway:R --> L:news

    auth:B --> T:postgres
    vocab:B --> T:postgres
    practice:B --> T:postgres
    news:B --> T:redis

    imagesync:B --> T:redis
    cacheupdater:B --> T:redis
    queuepop:B --> T:redis
    queuepop:B --> T:postgres

    prometheus:L --> R:gateway
    prometheus:L --> R:auth
    prometheus:L --> R:vocab
    prometheus:L --> R:practice
    prometheus:L --> R:news
    grafana:L --> R:prometheus

    vocab:T --> B:openai
    imagesync:T --> B:unsplash
    react:T --> B:responsivevoice
    news:T --> B:rss
```

### Core Services

- **Auth Service** (3002): User management & authentication
- **Vocabulary Service** (3003): Words & text processing with OpenAI
- **Practice Service** (3004): Learning sessions & progress tracking
- **News Service** (3005): Serbian news aggregation
- **API Gateway** (3001): Request routing & composition

### Background Services

- **Image Sync Service**: Unsplash API integration for vocabulary images
- **Cache Updater**: RSS feed processing for news articles
- **Queue Populator**: Image processing queue management

### Infrastructure

- **PostgreSQL**: Primary database for user data, vocabulary, and sessions
- **Redis**: Caching and job queues for background processing
- **Prometheus + Grafana**: Comprehensive monitoring and observability

## Development

### Common Commands

```bash
# Development
make up              # Start all services
make down            # Stop all services
make logs            # View logs
make rebuild-all     # Rebuild all services

# Code Quality
make format          # Format with Black
make lint            # Lint with Ruff
make test-cov        # Run tests with coverage
make check-all       # Run all quality checks

# Database
make migrate         # Run migrations
make db-shell        # PostgreSQL shell
```

### Testing

```bash
make test            # Run tests
make test-cov        # Tests with coverage report
make ci-test-cov     # CI-compatible tests with XML output
```

## Monitoring

**Health Checks**: Each service exposes `/health` endpoint

```bash
curl http://localhost:3002/health  # Auth Service
curl http://localhost:3003/health  # Vocabulary Service
```

**Metrics**: Prometheus metrics at `/metrics` for all services

**Structured Logging**: JSON logs with consistent format across services

**Grafana Dashboards**: Pre-configured dashboards for service monitoring, performance metrics, and business insights

## Security

- JWT authentication across all services
- Input validation and sanitization
- Rate limiting on public endpoints
- Environment-based secrets management
- Network isolation via Docker

## API Endpoints

### Authentication

```
POST /api/auth/register    # Register user
POST /api/auth/login       # User login
GET  /api/auth/me          # Current user
```

### Vocabulary & Learning

```
GET  /api/words            # User's vocabulary
POST /api/words            # Add words
POST /api/process-text     # AI text processing
GET  /api/practice/words   # Practice session
POST /api/practice/submit  # Submit answers
```

### News & Content

```
GET  /api/news            # Serbian news articles
GET  /api/news/sources    # Available sources
```

## Deployment

### Development

```bash
make setup           # Complete setup
docker-compose up -d # Start services
```

### Production

- Use environment-specific configurations
- Implement proper secrets management
- Configure SSL/TLS termination
- Set up log aggregation
- Configure monitoring alerts

## Features

- **AI-Powered Learning**: OpenAI integration for text processing and translations
- **Image Integration**: Automatic vocabulary images from Unsplash
- **Progress Tracking**: Comprehensive learning statistics and achievements
- **News Integration**: Real-time Serbian news for contextual learning
- **Responsive Design**: Modern React frontend with mobile support
- **Observability**: Complete monitoring stack with alerts

## Environment Configuration

Create a `.env` file with your API keys:

```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here
RESPONSIVEVOICE_API_KEY=your_responsivevoice_api_key_here

# Database (defaults work for Docker setup)
DATABASE_URL=postgresql://recnik:recnik@postgres:5432/recnik
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=your_jwt_secret_key_here
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Follow established patterns and add tests
4. Ensure all quality checks pass: `make check-all`
5. Submit pull request

## License

MIT License - see LICENSE file for details.

---

For detailed architecture documentation, see [docs/architecture.md](docs/architecture.md).
