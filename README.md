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

### Environment Configuration

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

### Setup

1. Clone and configure:

```bash
git clone <repository-url>
cd recnik
cp .env.example .env
# Edit .env with your API keys (see Environment Configuration above)
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
    %% User and Frontend
    User[User] --> Frontend[React App<br/>:3000]

    %% API Gateway
    Frontend --> Gateway[API Gateway<br/>:3001]

    %% Core Services
    Gateway --> Auth[Auth Service]
    Gateway --> Vocab[Vocabulary Service]
    Gateway --> Practice[Practice Service]
    Gateway --> News[News Service]

    %% Background Services
    ImageSync[Image Sync Service] --> Redis
    CacheUpdater[Cache Updater] --> Redis
    QueuePopulator[Queue Populator] --> Redis
    QueuePopulator --> Postgres

    %% Infrastructure
    Auth --> Postgres[(PostgreSQL<br/>:5432)]
    Vocab --> Postgres
    Practice --> Postgres
    News --> Redis[(Redis<br/>:6379)]

    %% Monitoring
    Prometheus[Prometheus<br/>:9090] --> Gateway
    Prometheus --> Auth
    Prometheus --> Vocab
    Prometheus --> Practice
    Prometheus --> News
    Grafana[Grafana<br/>:3100] --> Prometheus

    %% External APIs
    Vocab -.-> OpenAI[OpenAI API]
    ImageSync -.-> Unsplash[Unsplash API]
    Frontend -.-> ResponsiveVoice[ResponsiveVoice API]
    News -.-> RSS[RSS Feeds]

    %% Styling
    classDef service fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef infrastructure fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef external fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef monitoring fill:#e8f5e8,stroke:#2e7d2e,stroke-width:2px
    classDef background fill:#fce4ec,stroke:#880e4f,stroke-width:2px

    class Auth,Vocab,Practice,News,Gateway service
    class Postgres,Redis infrastructure
    class OpenAI,Unsplash,ResponsiveVoice,RSS external
    class Prometheus,Grafana monitoring
    class ImageSync,CacheUpdater,QueuePopulator background
```

### Core Services

- **Auth Service**: User management & authentication
- **Vocabulary Service**: Words & text processing with OpenAI
- **Practice Service**: Learning sessions & progress tracking
- **News Service**: Serbian news aggregation
- **API Gateway**: Request routing & composition

### Background Services

- **Image Sync Service**: Unsplash API integration for vocabulary images
- **Cache Updater**: RSS feed processing for news articles
- **Queue Populator**: Image processing queue management

### Infrastructure

- **PostgreSQL**: Primary database for user data, vocabulary, and sessions
- **Redis**: Caching and job queues for background processing
- **Prometheus + Grafana**: Comprehensive monitoring and observability

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| **Authentication** |
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | User login |
| GET | `/api/auth/me` | Get current user |
| **Vocabulary & Learning** |
| GET | `/api/words` | Get user's vocabulary |
| POST | `/api/words` | Add new words |
| POST | `/api/process-text` | AI text processing |
| GET | `/api/practice/words` | Get practice session |
| POST | `/api/practice/submit` | Submit practice answers |
| **News & Content** |
| GET | `/api/news` | Get Serbian news articles |
| GET | `/api/news/sources` | Get available news sources |

## Features

### AI-Powered Learning

OpenAI integration provides intelligent text processing and contextual translations. Analyzes learning patterns to suggest optimal study sessions.

### Visual Learning

Vocabulary words automatically paired with high-quality Unsplash images to enhance memory retention through visual association.

### Progress Tracking & Gamification

Track vocabulary growth, practice streaks, and mastery levels. Earn XP points and unlock achievements to stay motivated.

### Contextual Learning

Real-time Serbian news articles provide authentic language exposure while keeping you informed about current events.

### Audio Learning

Text-to-speech powered by ResponsiveVoice helps master Serbian pronunciation with natural-sounding voices.

### Mobile-Friendly Design

Responsive design works seamlessly across desktop, tablet, and mobile devices for learning anywhere.

### Adaptive Practice Sessions

Spaced repetition algorithm focuses on challenging vocabulary while reinforcing mastered words for maximum efficiency.

## Monitoring & Health Checks

**Health Checks**: Each service exposes `/health` endpoint

```bash
curl http://localhost:3002/health  # Auth Service
curl http://localhost:3003/health  # Vocabulary Service
```

**Metrics**: Prometheus metrics at `/metrics` for all services

**Structured Logging**: JSON logs with consistent format across services

**Grafana Dashboards**: Pre-configured dashboards for service monitoring, performance metrics, and business insights

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
