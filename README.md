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

#### OpenAI API Key
- **Purpose**: Text processing and translations
- **Get it**: [OpenAI Platform](https://platform.openai.com) → API Keys
- **Add to .env**: `OPENAI_API_KEY=your_key_here`

#### Unsplash API Key
- **Purpose**: Vocabulary word images
- **Get it**: [Unsplash Developers](https://unsplash.com/developers) → Create App
- **Add to .env**: `UNSPLASH_ACCESS_KEY=your_key_here`

#### ResponsiveVoice API Key
- **Purpose**: Text-to-speech functionality
- **Get it**: [ResponsiveVoice.org API](https://responsivevoice.org/api/)
- **Add to .env**: `RESPONSIVEVOICE_API_KEY=your_key_here`

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
graph TB
    %% User Interface
    User[User] --> Frontend[Frontend<br/>React App<br/>:3000]

    %% API Gateway
    Frontend --> Gateway[API Gateway<br/>Request Router<br/>:3001]

    %% Core Microservices
    Gateway --> Auth[Auth Service<br/>User Management<br/>:3002]
    Gateway --> Vocab[Vocabulary Service<br/>Words & Categories<br/>:3003]
    Gateway --> Practice[Practice Service<br/>Learning Sessions<br/>:3004]
    Gateway --> News[News Service<br/>Content Aggregation<br/>:3005]

    %% Background Services
    ImageSync[Image Sync Service<br/>Background Worker] --> Redis
    CacheUpdater[Cache Updater<br/>News Background Worker] --> Redis
    QueuePopulator[Queue Populator<br/>Image Queue Management] --> Redis
    QueuePopulator --> Postgres

    %% Infrastructure
    Auth --> Postgres[(PostgreSQL<br/>:5432)]
    Vocab --> Postgres
    Practice --> Postgres
    News --> Redis[(Redis<br/>:6379)]
    ImageSync --> Redis

    %% Monitoring
    Prometheus[Prometheus<br/>Metrics Collection<br/>:9090] --> Gateway
    Prometheus --> Auth
    Prometheus --> Vocab
    Prometheus --> Practice
    Prometheus --> News

    Grafana[Grafana<br/>Dashboards<br/>:3100] --> Prometheus

    %% External Services
    Vocab -.-> OpenAI[OpenAI API<br/>Text Processing]
    ImageSync -.-> Unsplash[Unsplash API<br/>Image Search]
    News -.-> RSS[RSS Feeds<br/>News Sources]

    %% Styling
    classDef service fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef infrastructure fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef external fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef monitoring fill:#e8f5e8,stroke:#2e7d2e,stroke-width:2px

    class Auth,Vocab,Practice,News,Gateway service
    class Postgres,Redis infrastructure
    class OpenAI,Unsplash,RSS external
    class Prometheus,Grafana monitoring
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
