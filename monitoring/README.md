# Monitoring Setup

This directory contains the monitoring configuration for the Serbian Vocabulary App using Prometheus and Grafana.

## Architecture

- **Prometheus**: Metrics collection and storage
- **Grafana**: Dashboard visualization and alerting
- **Flask Metrics**: Application metrics from Python services using `prometheus_flask_exporter`

## Services Monitored

1. **Infrastructure Services**:
   - Backend Service (Flask app on port 3001)
   - Auth Service (Flask app on port 3002)
   - Vocabulary Service (Flask app on port 3003)
   - Prometheus itself (port 9090)

2. **Metrics Collected**:
   - HTTP request rates and response times
   - Error rates and status codes
   - Service health/availability
   - Database connections
   - Cache operations
   - Business metrics (registrations, API usage)

## Dashboards

### 1. Infrastructure Dashboard (`infrastructure-dashboard.json`)

- **System Overview**: Services status, request rates
- **Response Times & Performance**: HTTP response times, error rates
- **Service Health**: Availability monitoring table

### 2. Application Dashboard (`application-dashboard.json`)

- **Authentication Metrics**: Login/register request rates, success/failure ratios
- **Backend Service Metrics**: API endpoint usage
- **Database & Cache Performance**: Connection metrics, cache operations
- **Business Metrics**: User registrations, vocabulary API usage

## Access URLs

- **Prometheus**: <http://localhost:9090>
- **Grafana**: <http://localhost:3100>
  - Default credentials: admin / admin (or set via `GRAFANA_PASSWORD` env var)

## Configuration Files

```
monitoring/
├── prometheus.yml              # Prometheus scrape configuration
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── prometheus.yml  # Grafana datasource config
│   │   └── dashboards/
│   │       └── dashboard.yml   # Dashboard provisioning config
│   └── dashboards/
│       ├── infrastructure-dashboard.json
│       └── application-dashboard.json
└── README.md
```

## Available Metrics

### Flask Application Metrics (via prometheus_flask_exporter)

- `flask_http_request_total`: Total HTTP requests
- `flask_http_request_duration_seconds`: HTTP request duration
- `flask_exporter_info`: General application info
- `up`: Service availability (1 = up, 0 = down)

### Custom Metrics Examples

You can add custom metrics in your Flask applications:

```python
from prometheus_client import Counter, Histogram, Gauge

# Custom business metrics
user_registrations = Counter('user_registrations_total', 'Total user registrations')
vocabulary_words_added = Counter('vocabulary_words_added_total', 'Total vocabulary words added')
active_users = Gauge('active_users', 'Number of active users')
```

## Alerts (Future Enhancement)

You can add alerting rules to Prometheus and configure Grafana alerts for:

- High error rates (>5%)
- Slow response times (>2s)
- Service downtime
- Database connection issues
- High memory/CPU usage

## Starting the Monitoring Stack

```bash
# Start all services including monitoring
docker compose up -d

# Start only monitoring services
docker compose up -d prometheus grafana

# View logs
docker compose logs -f prometheus grafana
```

## Troubleshooting

1. **Prometheus can't scrape services**:
   - Check if services are running and accessible
   - Verify network connectivity between containers
   - Check Prometheus targets: <http://localhost:9090/targets>

2. **Grafana dashboards not loading**:
   - Check if datasource is configured: <http://localhost:3100/datasources>
   - Verify dashboard files are mounted correctly
   - Check Grafana logs: `docker compose logs grafana`

3. **No metrics data**:
   - Ensure `prometheus_flask_exporter` is installed in your Python services
   - Check if metrics endpoints are accessible: <http://localhost:3001/api/metrics>
   - Verify Prometheus scrape configuration

## Extending Monitoring

To add more metrics or dashboards:

1. **Add new scrape targets** in `prometheus.yml`
2. **Create new dashboard JSON files** in `grafana/dashboards/`
3. **Add custom metrics** in your application code
4. **Configure alerts** in Prometheus or Grafana
