# Recnik

[![codecov](https://codecov.io/gh/ansromanov/recnik/branch/main/graph/badge.svg)](https://codecov.io/gh/ansromanov/recnik)
[![Python Code Quality](https://github.com/ansromanov/recnik/actions/workflows/python-quality.yml/badge.svg)](https://github.com/ansromanov/recnik/actions/workflows/python-quality.yml)
[![Build and Push Docker Images](https://github.com/ansromanov/recnik/actions/workflows/docker-build.yml/badge.svg)](https://github.com/ansromanov/recnik/actions/workflows/docker-build.yml)

A modern microservices-based Serbian vocabulary learning application with comprehensive observability and monitoring.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (for text processing)
- Unsplash API key (for images)

### Setup

1. Clone and configure:

```bash
git clone <repository-url>
cd recnik
cp .env.example .env
# Edit .env with your API keys
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

## 🏗️ Architecture

**Microservices Architecture** with 5 core services:

- **Auth Service** (3002): User management & authentication
- **Vocabulary Service** (3003): Words & text processing with OpenAI
- **Practice Service** (3004): Learning sessions & progress tracking
- **News Service** (3005): Serbian news aggregation
- **API Gateway** (3001): Request routing & composition

**Background Services:**

- Image Sync Service (Unsplash API integration)
- Cache Updater (RSS feeds)
- Queue Populator (image processing)

**Infrastructure:**

- PostgreSQL (primary database)
- Redis (caching & job queues)
- Prometheus + Grafana (monitoring)

## 🔧 Development

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

## 📊 Monitoring

**Health Checks**: Each service exposes `/health` endpoint

```bash
curl http://localhost:3002/health  # Auth Service
curl http://localhost:3003/health  # Vocabulary Service
```

**Metrics**: Prometheus metrics at `/metrics` for all services

**Structured Logging**: JSON logs with consistent format across services

**Grafana Dashboards**: Pre-configured dashboards for service monitoring, performance metrics, and business insights

## 🔐 Security

- JWT authentication across all services
- Input validation and sanitization
- Rate limiting on public endpoints
- Environment-based secrets management
- Network isolation via Docker

## 📚 API Endpoints

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

## 🚀 Deployment

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

## 📈 Features

- **AI-Powered Learning**: OpenAI integration for text processing and translations
- **Image Integration**: Automatic vocabulary images from Unsplash
- **Progress Tracking**: Comprehensive learning statistics and achievements
- **News Integration**: Real-time Serbian news for contextual learning
- **Responsive Design**: Modern React frontend with mobile support
- **Observability**: Complete monitoring stack with alerts

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Follow established patterns and add tests
4. Ensure all quality checks pass: `make check-all`
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

---

For detailed architecture documentation, see [docs/architecture.md](docs/architecture.md).
