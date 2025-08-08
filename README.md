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

The application follows a microservices architecture with 5 core services, frontend, and monitoring infrastructure:

```mermaid
graph TB
    %% User and Frontend
    User[User] --> Frontend[React App<br/>:3000]

    %% Core Services
    Frontend --> Auth[Auth Service]
    Frontend --> Backend[Backend Service]
    Frontend --> Vocab[Vocabulary Service]
    Frontend --> News[News Service]

    %% Background Services
    ImageSync[Image Sync Service] --> Redis
    Backend --> ImageSync

    %% Infrastructure
    Auth --> Postgres[(PostgreSQL<br/>:5432)]
    Backend --> Postgres
    Vocab --> Postgres
    News --> Redis[(Redis<br/>:6379)]
    ImageSync --> Redis

    %% Monitoring
    Prometheus[Prometheus<br/>:9090] --> Auth
    Prometheus --> Backend
    Prometheus --> Vocab
    Prometheus --> News
    Prometheus --> ImageSync
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

    class Auth,Backend,Vocab,News service
    class Postgres,Redis infrastructure
    class OpenAI,Unsplash,ResponsiveVoice,RSS external
    class Prometheus,Grafana monitoring
    class ImageSync background
```

### Core Services

- **Auth Service**: User management & authentication
- **Backend Service**: Main application logic & API orchestration
- **Vocabulary Service**: Words & text processing with OpenAI
- **News Service**: Serbian news aggregation
- **Image Sync Service**: Unsplash API integration for vocabulary images

### Frontend & Monitoring

- **Frontend**: React application serving the user interface
- **Prometheus + Grafana**: Comprehensive monitoring and observability

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

### AI-Powered Learning & Content Processing

OpenAI integration provides intelligent text processing, contextual translations, and personalized vocabulary recommendations. Real-time Serbian news articles provide authentic language exposure while keeping you informed about current events.

### Multimedia Learning Experience

Vocabulary words automatically paired with high-quality Unsplash images and text-to-speech audio powered by ResponsiveVoice to enhance memory retention through visual and auditory association.

### Progress Tracking & Adaptive Learning

Track vocabulary growth, practice streaks, and mastery levels. Earn XP points and unlock achievements to stay motivated. Spaced repetition algorithm focuses on challenging vocabulary while reinforcing mastered words for maximum efficiency.

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
