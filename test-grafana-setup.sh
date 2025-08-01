#!/bin/bash

# Test Grafana Setup Script
echo "Testing Grafana Dashboard Setup..."
echo "================================="

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✓ Loaded environment variables from .env"
else
    echo "✗ .env file not found"
    exit 1
fi

# Test Grafana health
echo ""
echo "Testing Grafana health..."
if curl -s -f http://localhost:3100/api/health > /dev/null; then
    echo "✓ Grafana is healthy and responding"
else
    echo "✗ Grafana is not responding"
    exit 1
fi

# Test Prometheus connection
echo ""
echo "Testing Prometheus connection..."
if curl -s -f http://localhost:9090/api/v1/status/config > /dev/null; then
    echo "✓ Prometheus is healthy and responding"
else
    echo "✗ Prometheus is not responding"
    exit 1
fi

# Test Grafana login with credentials from .env
echo ""
echo "Testing Grafana authentication..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:3100/login \
    -H "Content-Type: application/json" \
    -d "{\"user\":\"${GRAFANA_ADMIN_USER}\",\"password\":\"${GRAFANA_ADMIN_PASSWORD}\"}")

if echo "$LOGIN_RESPONSE" | grep -q "message"; then
    echo "✓ Grafana login successful with credentials from .env"
else
    echo "✗ Grafana login failed"
fi

# Test dashboard API
echo ""
echo "Testing dashboard provisioning..."
DASHBOARDS=$(curl -s -u "${GRAFANA_ADMIN_USER}:${GRAFANA_ADMIN_PASSWORD}" \
    http://localhost:3100/api/search?type=dash-db)

if echo "$DASHBOARDS" | grep -q "title"; then
    DASHBOARD_COUNT=$(echo "$DASHBOARDS" | grep -o '"title"' | wc -l)
    echo "✓ Found $DASHBOARD_COUNT provisioned dashboard(s)"
    echo "$DASHBOARDS" | jq -r '.[] | "  - " + .title' 2>/dev/null || echo "  (Install jq for better formatting)"
else
    echo "✗ No dashboards found or API error"
fi

# Test datasource
echo ""
echo "Testing Prometheus datasource..."
DATASOURCES=$(curl -s -u "${GRAFANA_ADMIN_USER}:${GRAFANA_ADMIN_PASSWORD}" \
    http://localhost:3100/api/datasources)

if echo "$DATASOURCES" | grep -q "Prometheus"; then
    echo "✓ Prometheus datasource is configured"
else
    echo "✗ Prometheus datasource not found"
fi

echo ""
echo "================================="
echo "Setup Summary:"
echo "- Grafana URL: http://localhost:3100"
echo "- Username: ${GRAFANA_ADMIN_USER}"
echo "- Password: ${GRAFANA_ADMIN_PASSWORD}"
echo "- Prometheus URL: http://localhost:9090"
echo "================================="
