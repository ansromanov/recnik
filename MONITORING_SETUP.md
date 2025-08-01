# Serbian Vocabulary App - Monitoring Setup Complete

## 🎯 Overview

Comprehensive monitoring has been set up for the Serbian Vocabulary App with Prometheus and Grafana, including:

- **Infrastructure monitoring** (services, performance, health)
- **Application-specific metrics** (authentication, business metrics)
- **Alert rules** for proactive monitoring
- **Pre-configured dashboards** for visualization

## 📊 Dashboards Created

### 1. Infrastructure Dashboard

- **System Overview**: Service count, HTTP request rates
- **Performance Metrics**: Response times (95th/50th percentile), error rates
- **Service Health**: Real-time availability status table

### 2. Application Dashboard

- **Authentication Metrics**: Login/register rates, success vs failure
- **Backend API Usage**: All endpoint request rates
- **Database & Cache**: Connection metrics, cache operations
- **Business Metrics**: User registrations, vocabulary API usage

## 🚨 Alert Rules Configured

1. **ServiceDown**: Alerts when any service is unreachable (Critical)
2. **HighErrorRate**: Alerts when error rate > 5% (Warning)
3. **HighResponseTime**: Alerts when 95th percentile > 2s (Warning)
4. **HighAuthFailureRate**: Alerts when login failures > 10% (Warning)
5. **LowUserRegistrations**: Info alert for low activity (Info)

## 🔧 Access Points

- **Prometheus**: <http://localhost:9090>
  - Targets: <http://localhost:9090/targets>
  - Rules: <http://localhost:9090/rules>
  - Alerts: <http://localhost:9090/alerts>

- **Grafana**: <http://localhost:3100>
  - Username: `admin`
  - Password: `admin` (or set `GRAFANA_PASSWORD` env var)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask Apps    │    │   Prometheus    │    │     Grafana     │
│                 │───▶│                 │───▶│                 │
│ - Backend       │    │ Metrics Storage │    │  Visualization  │
│ - Auth Service  │    │ Alert Engine    │    │   Dashboards    │
│ - Vocab Service │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 File Structure

```
monitoring/
├── prometheus.yml                    # Prometheus config
├── alert-rules.yml                   # Alert definitions
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── prometheus.yml        # Grafana datasource
│   │   └── dashboards/
│   │       └── dashboard.yml         # Dashboard provisioning
│   └── dashboards/
│       ├── infrastructure-dashboard.json
│       └── application-dashboard.json
├── README.md                         # Detailed setup guide
└── MONITORING_SETUP.md              # This summary
```

## 🚀 Quick Start

1. **Start monitoring services**:

   ```bash
   docker compose up -d prometheus grafana
   ```

2. **Start application services** (to see metrics):

   ```bash
   docker compose up -d backend auth-service
   ```

3. **Access dashboards**:
   - Open <http://localhost:3100>
   - Login with admin/admin
   - Dashboards are auto-provisioned

## 📈 Key Metrics Monitored

### Infrastructure Metrics

- `up`: Service availability
- `flask_http_request_total`: HTTP request counts
- `flask_http_request_duration_seconds`: Response times

### Application Metrics

- Authentication success/failure rates
- API endpoint usage patterns
- Database connection health
- Cache operation rates
- User registration trends

## 🎛️ Next Steps

1. **Add custom business metrics** in your Flask apps:

   ```python
   from prometheus_client import Counter, Histogram
   
   user_actions = Counter('user_actions_total', 'User actions', ['action_type'])
   vocabulary_size = Histogram('user_vocabulary_size', 'User vocabulary size')
   ```

2. **Configure alerting** (optional):
   - Set up Alertmanager for notifications
   - Configure Slack/email integrations
   - Add more specific business alert rules

3. **Extend monitoring**:
   - Add database metrics (PostgreSQL exporter)
   - Add Redis metrics (Redis exporter)
   - Add system metrics (Node exporter)

## ✅ Status

- [x] Docker Compose build issue fixed (`libpq-dev` package)
- [x] Prometheus configuration complete
- [x] Grafana dashboards provisioned
- [x] Alert rules configured
- [x] Services successfully running
- [x] Documentation complete

**The monitoring setup is fully operational and ready for use!**

## 🔍 Troubleshooting

If you encounter issues:

1. **Check service status**: `docker compose ps`
2. **View logs**: `docker compose logs prometheus grafana`
3. **Verify targets**: Visit <http://localhost:9090/targets>
4. **Test dashboards**: Visit <http://localhost:3100>

Refer to `monitoring/README.md` for detailed troubleshooting steps.
