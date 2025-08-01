#!/bin/bash

echo "Fixing Grafana dashboard configuration issues..."

# Stop containers if running
echo "Stopping Grafana and Prometheus containers..."
docker-compose stop grafana prometheus

# Remove Grafana data to force re-provisioning
echo "Clearing Grafana data volume..."
docker volume rm serbian-vocabulary-app_grafana_data 2>/dev/null || true

# Restart the monitoring stack
echo "Starting monitoring stack..."
docker-compose up -d prometheus grafana

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check if services are running
echo "Checking service status..."
if docker-compose ps grafana | grep -q "Up"; then
    echo "✓ Grafana is running"
else
    echo "✗ Grafana failed to start"
fi

if docker-compose ps prometheus | grep -q "Up"; then
    echo "✓ Prometheus is running"
else
    echo "✗ Prometheus failed to start"
fi

echo ""
echo "Dashboard fix complete!"
echo "Access Grafana at: http://localhost:3100"
echo "Default credentials: admin/admin"
echo ""
echo "To test the setup, run: ./test-grafana-setup.sh"
