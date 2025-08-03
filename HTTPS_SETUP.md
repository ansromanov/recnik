# HTTPS Setup for Serbian Vocabulary App

This guide explains how to run the Serbian Vocabulary App with HTTPS using self-signed certificates for local development.

## Quick Start

To start the application with HTTPS, simply run:

```bash
./start-https.sh
```

This script will:

- Create SSL certificates if they don't exist
- Set up environment variables
- Start all services with HTTPS configuration
- Provide health checks and access information

## Manual Setup

If you prefer to set up HTTPS manually, follow these steps:

### 1. Create SSL Certificates

```bash
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -keyout ssl/localhost.key -out ssl/localhost.crt -days 365 -nodes \
    -subj "/C=RS/ST=Belgrade/L=Belgrade/O=SerbianVocabApp/OU=Development/CN=localhost"
```

### 2. Start Services

```bash
docker-compose -f docker-compose-https.yml up --build -d
```

## Access Points

Once the services are running, you can access:

- **Frontend (HTTPS)**: <https://localhost:443>
- **Frontend (HTTP)**: <http://localhost:3000> (redirects to HTTPS)
- **Backend API**: <https://localhost:443/api>
- **Grafana**: <http://localhost:3100>
- **Prometheus**: <http://localhost:9090>

## SSL Certificate Details

- **Type**: Self-signed certificate
- **Validity**: 365 days
- **Subject**: CN=localhost, O=SerbianVocabApp, OU=Development
- **Key Size**: RSA 4096-bit

## Browser Security Warning

Since we're using self-signed certificates, your browser will show a security warning. To proceed:

1. Click "Advanced" or "Show Details"
2. Click "Proceed to localhost (unsafe)" or similar option
3. The certificate will be temporarily accepted for this session

## Configuration Files

### HTTPS Docker Compose

- File: `docker-compose-https.yml`
- Includes SSL certificate mounting
- Updated CORS origins for HTTPS
- HTTP to HTTPS redirect configuration

### Nginx HTTPS Configuration

- File: `frontend/nginx-https.conf`
- SSL/TLS settings
- Security headers
- HTTP to HTTPS redirect
- API proxy configuration

### Backend Configuration

- Updated CORS origins to include HTTPS URLs
- Maintains compatibility with both HTTP and HTTPS

## Security Features

The HTTPS setup includes several security enhancements:

### SSL/TLS Configuration

- TLS 1.2 and 1.3 support
- Strong cipher suites
- Perfect Forward Secrecy
- Session caching

### Security Headers

- `Strict-Transport-Security` (HSTS)
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection`
- `Referrer-Policy`

## Troubleshooting

### Certificate Issues

If you encounter certificate issues:

```bash
# Remove existing certificates
rm -rf ssl/

# Regenerate certificates
./start-https.sh
```

### Port Conflicts

If port 443 is already in use:

```bash
# Check what's using port 443
sudo lsof -i :443

# Stop conflicting services
sudo service nginx stop  # Example for nginx
```

### Browser Cache Issues

If you see old certificate warnings:

1. Clear browser cache and cookies
2. Try incognito/private browsing mode
3. Restart the browser

### Service Health Checks

Check service status:

```bash
# View all service logs
docker-compose -f docker-compose-https.yml logs -f

# Check specific service
docker-compose -f docker-compose-https.yml logs frontend

# Check service health
curl -k https://localhost:443/api/health
```

## Development Notes

### CORS Configuration

The backend is configured to accept requests from:

- `https://localhost:443`
- `https://localhost:3000`
- `http://localhost:3000` (for fallback)

### API Calls

All frontend API calls use relative URLs (`/api/...`) which automatically work with both HTTP and HTTPS through the nginx proxy.

### Hot Reloading

Development features like hot reloading continue to work with HTTPS enabled.

## Production Considerations

**Important**: This setup is for development only. For production:

1. Use certificates from a trusted Certificate Authority (CA)
2. Implement proper certificate management
3. Use environment-specific configurations
4. Enable additional security measures
5. Consider using a reverse proxy like Cloudflare

## File Structure

```
serbian-vocabulary-app/
├── ssl/                          # SSL certificates
│   ├── localhost.crt            # SSL certificate
│   └── localhost.key            # SSL private key
├── docker-compose-https.yml     # HTTPS Docker Compose config
├── frontend/nginx-https.conf    # Nginx HTTPS configuration
├── start-https.sh              # HTTPS startup script
└── HTTPS_SETUP.md              # This documentation
```

## Stopping Services

To stop all HTTPS services:

```bash
docker-compose -f docker-compose-https.yml down
```

To stop and remove volumes:

```bash
docker-compose -f docker-compose-https.yml down -v
```

## Support

If you encounter issues with the HTTPS setup:

1. Check the troubleshooting section above
2. Verify all certificates are properly generated
3. Ensure no port conflicts exist
4. Check Docker container logs for errors

For additional help, refer to the main project documentation or create an issue in the project repository.
