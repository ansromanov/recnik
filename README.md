# Serbian Vocabulary Learning App

A modern microservices-based application for learning Serbian vocabulary, built with clean architecture principles and comprehensive observability.

## 🏗️ Architecture Overview

The application has been redesigned as a microservices architecture following 12-factor app principles:

- **5 Core Microservices**: Auth, Vocabulary, Practice, News, API Gateway
- **3 Background Services**: Image Sync, Cache Updater, Queue Populator  
- **Full Observability**: Structured JSON logging, Prometheus metrics, Health checks
- **Monitoring Stack**: Prometheus + Grafana dashboards
- **Infrastructure**: PostgreSQL, Redis, Docker containers

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (for text processing)
- Unsplash API key (for images)

### Environment Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd serbian-vocabulary-app
```

2. Copy and configure environment variables:

```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Start all services:

```bash
docker-compose up -d
```

4. Access the application:

- Frontend: <http://localhost:3000>
- API Gateway: <http://localhost:3001>
- Prometheus: <http://localhost:9090>
- Grafana: <http://localhost:3100>

## 📊 Service Architecture

### Core Services

| Service | Port | Purpose | Technology |
|---------|------|---------|------------|
| **Frontend** | 3000 | React web application | React, Nginx |
| **API Gateway** | 3001 | Request routing & auth | Flask, JWT |
| **Auth Service** | 3002 | User management | Flask, SQLAlchemy, PostgreSQL |
| **Vocabulary Service** | 3003 | Words & text processing | Flask, OpenAI API, PostgreSQL |
| **Practice Service** | 3004 | Learning sessions | Flask, SQLAlchemy, PostgreSQL |
| **News Service** | 3005 | Serbian news aggregation | Flask, RSS parsing, Redis |

### Background Services

- **Image Sync Service**: Fetches vocabulary images from Unsplash API
- **Cache Updater**: Keeps news articles fresh via RSS feeds
- **Queue Populator**: Manages image processing queues

### Infrastructure

- **PostgreSQL**: Primary database for user data, vocabulary, practice sessions
- **Redis**: Caching layer for news articles and background job queues
- **Prometheus**: Metrics collection from all services
- **Grafana**: Monitoring dashboards and alerting

## 🔧 Development

### Project Structure

```
serbian-vocabulary-app/
├── services/                    # Microservices
│   ├── auth-service/           # User authentication & settings
│   ├── vocabulary-service/     # Words, categories, text processing
│   ├── practice-service/       # Learning sessions & statistics
│   ├── news-service/          # News aggregation & caching
│   └── api-gateway/           # Request routing & composition
├── frontend/                   # React web application
├── image-sync-service/        # Background image processing
├── database/                  # Database initialization scripts  
├── monitoring/               # Prometheus & Grafana config
├── docs/                     # Architecture documentation
└── docker-compose.yml       # Service orchestration
```

### Service Template (MVC Pattern)

Each microservice follows a consistent structure:

```
service-name/
├── main.py                    # Flask app & routes (Views)
├── controllers/               # Business logic
├── models/                    # Database models
├── utils/                     # Shared utilities (logger, etc.)
├── health.py                  # Health check endpoint
├── metrics.py                 # Prometheus metrics
├── requirements.txt           # Python dependencies
└── Dockerfile                # Container configuration
```

### Adding a New Service

1. Create service directory under `services/`
2. Implement MVC structure with health checks and metrics
3. Add structured JSON logging
4. Create Dockerfile and requirements.txt
5. Update docker-compose.yml with service configuration
6. Add Prometheus scraping configuration
7. Update API Gateway routing

### Running Individual Services

```bash
# Start just the infrastructure
docker-compose up -d postgres redis

# Start a specific service for development
cd services/auth-service
pip install -r requirements.txt
python main.py

# View service logs
docker-compose logs -f vocabulary-service

# Scale services
docker-compose up -d --scale vocabulary-service=3
```

## 📈 Monitoring & Observability

### Structured Logging

All services output structured JSON logs with consistent fields:

```json
{
  "timestamp": "2025-01-08T07:22:15Z",
  "level": "INFO",
  "service": "auth-service",
  "message": "User registered successfully",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 123,
  "endpoint": "/api/auth/register",
  "method": "POST",
  "ip": "192.168.1.100"
}
```

### Health Checks

Every service exposes a `/health` endpoint:

```bash
# Check all services
curl http://localhost:3002/health  # Auth Service
curl http://localhost:3003/health  # Vocabulary Service
curl http://localhost:3004/health  # Practice Service
curl http://localhost:3005/health  # News Service
```

### Prometheus Metrics

All services expose metrics at `/metrics`:

- HTTP request counts and durations
- Database connection status
- Custom business metrics (registrations, vocabulary size, etc.)
- Service-specific performance indicators

### Grafana Dashboards

Pre-configured dashboards for:

- Service overview and health
- Request rates and response times
- Database performance
- Business metrics (user activity, learning progress)

## 🔐 Security

- **JWT Authentication**: Stateless token-based auth across services
- **Input Validation**: All API endpoints validate and sanitize input
- **Network Isolation**: Services communicate via internal Docker network
- **Secrets Management**: API keys via environment variables
- **Rate Limiting**: Protection against abuse on public endpoints

## 🧪 Testing

```bash
# Run unit tests for a service
cd services/auth-service
pytest tests/

# Integration testing
python test_api.py

# Load testing
docker-compose up -d
# Use your preferred load testing tool against localhost:3001
```

## 🚀 Deployment

### Docker Compose (Development)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Considerations

- Use environment-specific configuration files
- Implement proper secret management (HashiCorp Vault, AWS Secrets Manager)
- Set up log aggregation (ELK stack, Fluentd)
- Configure automated backups for PostgreSQL
- Implement proper SSL/TLS termination
- Set up monitoring alerts in Grafana

## 📚 API Documentation

### Authentication Endpoints

```
POST /api/auth/register    # Register new user
POST /api/auth/login       # User login
GET  /api/auth/me          # Get current user info
GET  /api/settings         # Get user settings
PUT  /api/settings         # Update user settings
```

### Vocabulary Endpoints

```
GET  /api/categories                      # List word categories
GET  /api/words                          # Get user's vocabulary
POST /api/words                          # Add words to vocabulary
POST /api/process-text                   # Process Serbian text with AI
GET  /api/top100/categories/<id>         # Get top 100 words by category
POST /api/top100/add                     # Add top 100 words to vocabulary
```

### Practice Endpoints

```
GET  /api/practice/words                 # Get words for practice session
POST /api/practice/start                 # Start new practice session
POST /api/practice/submit                # Submit practice answers
POST /api/practice/complete              # Complete practice session
POST /api/practice/example-sentence     # Generate example sentence
GET  /api/stats                          # Get learning statistics
```

### News Endpoints

```
GET  /api/news                           # Get Serbian news articles
GET  /api/news/sources                   # Get available news sources
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Follow the established MVC patterns and logging standards
4. Add tests for new functionality
5. Ensure all services have proper health checks and metrics
6. Update documentation as needed
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆚 Architecture Improvements

This redesign implements the following improvements over the original monolithic structure:

### ✅ Microservices Design

- **Domain Separation**: Each service handles a specific business domain
- **Independent Scaling**: Scale services based on individual needs
- **Technology Diversity**: Choose best tools for each service
- **Fault Isolation**: Service failures don't bring down the entire system

### ✅ Observability & Monitoring

- **Structured JSON Logging**: Consistent, searchable logs across all services
- **Prometheus Metrics**: Comprehensive monitoring of all services and infrastructure
- **Health Checks**: Automated health monitoring for all components
- **Grafana Dashboards**: Visual monitoring and alerting

### ✅ 12-Factor App Compliance

- **Configuration**: All config via environment variables
- **Stateless Processes**: Services can be scaled horizontally
- **Port Binding**: Each service binds to its own port
- **Logs**: JSON to stdout for proper log aggregation
- **Dev/Prod Parity**: Same containers run in all environments

### ✅ Clean Architecture

- **MVC Pattern**: Consistent structure across all services
- **Dependency Injection**: Testable, loosely coupled components
- **Single Responsibility**: Each service has a clear, focused purpose
- **API-First Design**: Well-defined interfaces between services

### ✅ Production Ready

- **Docker Containers**: All services containerized with health checks
- **Service Discovery**: Services communicate via internal network
- **Circuit Breakers**: Resilience patterns for external API calls
- **Monitoring Stack**: Complete observability with Prometheus + Grafana

For detailed architecture documentation, see [docs/architecture.md](docs/architecture.md).
