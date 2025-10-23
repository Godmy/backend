# Health Checks

The application provides two health check endpoints for monitoring system status.

## Endpoints

### Simple Health Check (Backward Compatible)

Basic health check endpoint for simple monitoring.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

### Detailed Health Check (Comprehensive Monitoring)

Comprehensive health check with detailed component status.

```bash
curl http://localhost:8000/health/detailed
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1737000000.123,
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12.34,
      "message": "Database connection successful"
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 5.67,
      "message": "Redis connection successful"
    },
    "disk": {
      "status": "healthy",
      "percent_used": 45.2,
      "total_gb": 100.0,
      "used_gb": 45.2,
      "free_gb": 54.8,
      "message": "Disk usage at 45.2%"
    },
    "memory": {
      "status": "healthy",
      "percent_used": 65.5,
      "total_gb": 16.0,
      "used_gb": 10.5,
      "available_gb": 5.5,
      "message": "Memory usage at 65.5%"
    }
  }
}
```

---

## Status Levels

- **`healthy`** - All components operating normally (HTTP 200)
- **`degraded`** - Some components have warnings but system is operational (HTTP 200)
- **`unhealthy`** - One or more critical components failed (HTTP 503)

---

## Monitoring Thresholds

- **Disk usage warning:** 90%
- **Memory usage warning:** 90%

---

## Implementation

- **Service:** `core/services/health_service.py` - HealthCheckService with component checks
- **Metrics:** Uses `psutil` for system metrics (disk, memory)
- **Response times:** Measures response times for database and Redis connections

---

## Usage in Production

**Docker Compose:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

**Kubernetes:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/detailed
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## Monitoring Integration

- **Prometheus:** Scrape `/metrics` endpoint for detailed metrics
- **Grafana:** Create dashboards with health check data
- **Alerting:** Set up alerts for unhealthy status
