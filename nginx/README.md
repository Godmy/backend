# Nginx Configuration

This directory contains nginx configuration files for production deployment.

## Files

- **`nginx.conf`** - Production configuration with SSL/HTTPS
- **`nginx.dev.conf`** - Development/Staging configuration (HTTP only)
- **`ssl/`** - Directory for SSL certificates (not tracked in git)

## Setup for Production

### 1. Prepare SSL Certificates

#### Option A: Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificates will be at:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

Then update `docker-compose.prod.yml`:

```yaml
nginx:
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro
```

And update `nginx.conf`:

```nginx
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
```

#### Option B: Self-signed (Development/Testing)

```bash
# Create ssl directory
mkdir -p ssl

# Generate self-signed certificate (valid for 365 days)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem \
  -out ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=yourdomain.com"
```

### 2. Update nginx.conf

Replace `yourdomain.com` with your actual domain:

```nginx
server_name yourdomain.com www.yourdomain.com;
```

### 3. Configure CORS

Update allowed origins in `nginx.conf`:

```nginx
add_header 'Access-Control-Allow-Origin' 'https://yourdomain.com' always;
```

### 4. Test Configuration

```bash
# Test nginx config syntax
docker run --rm -v $(pwd)/nginx/nginx.conf:/etc/nginx/nginx.conf:ro nginx nginx -t

# Or if nginx is running
docker exec templates_nginx nginx -t
```

### 5. Deploy

```bash
# Start with production config
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f nginx

# Reload nginx after config changes
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

## Rate Limiting

Default rate limits in production:

- **GraphQL**: 10 requests/second (burst 20)
- **Auth endpoints**: 5 requests/second (burst 10)
- **General API**: 100 requests/second (burst 50)

Adjust in `nginx.conf`:

```nginx
limit_req_zone $binary_remote_addr zone=graphql:10m rate=10r/s;
```

## Security Headers

Production config includes:

- `X-Frame-Options: SAMEORIGIN` - Prevents clickjacking
- `X-Content-Type-Options: nosniff` - Prevents MIME sniffing
- `X-XSS-Protection: 1; mode=block` - XSS protection
- `Strict-Transport-Security` - Force HTTPS
- `Referrer-Policy` - Control referrer information

## Monitoring

### Access Logs

```bash
# View access logs
docker-compose -f docker-compose.prod.yml logs nginx

# Real-time monitoring
docker exec templates_nginx tail -f /var/log/nginx/access.log
```

### Error Logs

```bash
docker exec templates_nginx tail -f /var/log/nginx/error.log
```

### Metrics

Add nginx prometheus exporter for monitoring:

```yaml
# docker-compose.prod.yml
nginx-exporter:
  image: nginx/nginx-prometheus-exporter:latest
  ports:
    - "9113:9113"
  command:
    - -nginx.scrape-uri=http://nginx:80/stub_status
```

## Troubleshooting

### Issue: 502 Bad Gateway

**Cause**: Backend (app) is not running or not reachable

**Solution**:
```bash
# Check backend status
docker-compose -f docker-compose.prod.yml ps app

# Check backend logs
docker-compose -f docker-compose.prod.yml logs app

# Restart backend
docker-compose -f docker-compose.prod.yml restart app
```

### Issue: 429 Too Many Requests

**Cause**: Rate limit exceeded

**Solution**:
- Increase rate limits in `nginx.conf`
- Implement request caching on client side
- Check for retry loops in client code

### Issue: SSL certificate errors

**Cause**: Certificate expired or invalid

**Solution**:
```bash
# Check certificate expiration
openssl x509 -in ssl/cert.pem -noout -enddate

# Renew Let's Encrypt certificate
sudo certbot renew

# Reload nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### Issue: CORS errors

**Cause**: Origin not allowed

**Solution**:
Update CORS headers in `nginx.conf`:
```nginx
add_header 'Access-Control-Allow-Origin' 'https://your-frontend-domain.com' always;
```

## Performance Tuning

### Worker Processes

```nginx
# Adjust based on CPU cores
worker_processes auto;
```

### Worker Connections

```nginx
events {
    worker_connections 4096;  # Increase for high traffic
}
```

### Client Body Size

```nginx
client_max_body_size 50M;  # For file uploads
```

### Timeouts

```nginx
proxy_connect_timeout 120s;
proxy_send_timeout 120s;
proxy_read_timeout 120s;
```

## Alternative: Using Caddy

If you prefer automatic HTTPS, consider Caddy:

```yaml
# docker-compose.prod.yml
caddy:
  image: caddy:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./Caddyfile:/etc/caddy/Caddyfile
    - caddy_data:/data
```

**`Caddyfile`**:
```
yourdomain.com {
    reverse_proxy app:8000

    rate_limit {
        zone graphql {
            match path /graphql
            rate 10r/s
        }
    }
}
```

Caddy automatically obtains and renews Let's Encrypt certificates!

## Resources

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [Nginx Rate Limiting](https://www.nginx.com/blog/rate-limiting-nginx/)
