# API Rate Limiting

**Status:** ✅ Implemented | **Priority:** P0 | **User Story:** #5

## Обзор

Система rate limiting защищает API от злоупотреблений (abuse) и DDoS атак путем ограничения количества запросов от одного пользователя или IP адреса.

## Основные возможности

### ✅ Реализованные функции

- **Per-user rate limiting** - Отдельные лимиты для каждого аутентифицированного пользователя
- **Per-IP rate limiting** - Лимиты для anonymous users по IP адресу
- **Разные лимиты** - 100 req/min для auth users, 20 req/min для anon users
- **Redis счетчики** - Distributed rate limiting с Redis
- **X-RateLimit-* headers** - Стандартные headers в ответах
- **HTTP 429** - Too Many Requests при превышении лимита
- **IP Whitelist** - Bypass rate limiting для admin/internal IPs
- **Path exclusions** - Исключить определенные пути (health checks, metrics)
- **Structured logging** - JSON логи с событиями rate limit
- **Prometheus metrics** - Метрики для мониторинга

### 📊 Архитектура

```
┌─────────────┐     ┌──────────────────┐     ┌─────────┐
│   Request   │────▶│ Rate Limit       │────▶│  Redis  │
│             │     │ Middleware       │     │ Counter │
└─────────────┘     └──────────────────┘     └─────────┘
                            │
                            ├─── Auth User: rate_limit:user:{user_id}
                            └─── Anon User: rate_limit:ip:{ip_address}
```

**Алгоритм:** Sliding Window с Redis

## Конфигурация

### Переменные окружения

```env
# Enable/disable rate limiting
RATE_LIMIT_ENABLED=true

# Requests per minute for authenticated users (global default)
RATE_LIMIT_AUTH_PER_MINUTE=100

# Requests per minute for anonymous users (global default)
RATE_LIMIT_ANON_PER_MINUTE=20

# Comma-separated list of whitelisted IPs (bypass rate limiting)
RATE_LIMIT_WHITELIST_IPS=127.0.0.1,::1

# Comma-separated list of paths to exclude from rate limiting
RATE_LIMIT_EXCLUDE_PATHS=/health,/metrics

# Per-endpoint rate limits (JSON format with regex patterns)
# Keys are regex patterns, values are limits for auth/anon users
RATE_LIMIT_ENDPOINT_LIMITS={"^/graphql$": {"auth": 50, "anon": 10}, "^/api/search": {"auth": 30, "anon": 5}}
```

### Per-Endpoint Rate Limits

Вы можете настроить разные лимиты для разных endpoints:

```env
# JSON format: regex pattern -> {auth: limit, anon: limit}
RATE_LIMIT_ENDPOINT_LIMITS={
  "^/graphql$": {"auth": 50, "anon": 10},
  "^/api/search": {"auth": 30, "anon": 5},
  "^/api/users": {"auth": 100, "anon": 20}
}
```

**Как это работает:**
1. Middleware проверяет path запроса против каждого regex pattern
2. Если найдено совпадение, используется endpoint-specific лимит
3. Если совпадений нет, используется глобальный лимит (`RATE_LIMIT_AUTH_PER_MINUTE` / `RATE_LIMIT_ANON_PER_MINUTE`)

**Примеры regex patterns:**
```json
{
  "^/graphql$": {"auth": 50, "anon": 10},        // Только /graphql (exact match)
  "^/api/users": {"auth": 100, "anon": 20},      // /api/users, /api/users/123, etc
  "^/api/search": {"auth": 30, "anon": 5},       // Поиск (expensive operation)
  "^/api/(users|posts)": {"auth": 80, "anon": 15} // Multiple endpoints
}
```

### Рекомендованные значения

#### Development
```env
RATE_LIMIT_ENABLED=false  # Отключить для разработки
```

#### Production
```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_AUTH_PER_MINUTE=100
RATE_LIMIT_ANON_PER_MINUTE=20
RATE_LIMIT_WHITELIST_IPS=10.0.0.0/24,172.16.0.0/12  # Internal networks
# Stricter limits for GraphQL (expensive queries)
RATE_LIMIT_ENDPOINT_LIMITS={"^/graphql$": {"auth": 50, "anon": 10}}
```

#### High-traffic API with per-endpoint limits
```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_AUTH_PER_MINUTE=500
RATE_LIMIT_ANON_PER_MINUTE=50
# Different limits for expensive vs cheap operations
RATE_LIMIT_ENDPOINT_LIMITS={
  "^/graphql$": {"auth": 100, "anon": 20},
  "^/api/search": {"auth": 50, "anon": 10},
  "^/api/export": {"auth": 10, "anon": 2}
}
```

## Использование

### HTTP Headers

Все ответы содержат следующие headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705320060
```

**Описание:**
- `X-RateLimit-Limit` - Максимальное количество запросов в окне
- `X-RateLimit-Remaining` - Оставшееся количество запросов
- `X-RateLimit-Reset` - Unix timestamp, когда лимит сбросится

### Пример успешного запроса

**Request:**
```bash
curl -H "Authorization: Bearer <token>" https://api.example.com/graphql
```

**Response:**
```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1705320060
Content-Type: application/json

{"data": {...}}
```

### Пример заблокированного запроса

**Request:**
```bash
curl https://api.example.com/graphql
```

**Response:**
```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705320000
Content-Type: application/json

{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Limit: 20 requests per minute.",
  "retry_after": 45
}
```

## Как работает Rate Limiting

### Для аутентифицированных пользователей

1. Middleware извлекает `user_id` из JWT токена
2. Создается Redis key: `rate_limit:user:{user_id}`
3. Счетчик инкрементируется
4. Если счетчик > лимита → HTTP 429
5. Счетчик сбрасывается через 60 секунд (TTL)

### Для анонимных пользователей

1. Middleware извлекает IP адрес из:
   - `X-Forwarded-For` header (если за прокси)
   - `X-Real-IP` header
   - Прямой IP соединения
2. Создается Redis key: `rate_limit:ip:{ip_address}`
3. Дальше аналогично аутентифицированным пользователям

### IP Extraction за прокси

```python
# Примеры X-Forwarded-For header
X-Forwarded-For: 203.0.113.195                    # Один IP
X-Forwarded-For: 203.0.113.195, 70.41.3.18       # Два IP (берется первый)
X-Forwarded-For: 2001:db8::1                      # IPv6
```

**Используется первый IP в цепочке** - это клиентский IP

## Whitelist (bypass rate limiting)

### Добавление IP в whitelist

```env
# Один IP
RATE_LIMIT_WHITELIST_IPS=192.168.1.100

# Несколько IP
RATE_LIMIT_WHITELIST_IPS=192.168.1.100,10.0.0.50,172.16.0.10

# Localhost (по умолчанию)
RATE_LIMIT_WHITELIST_IPS=127.0.0.1,::1
```

### Use cases для whitelist

1. **Admin панель** - Internal admin dashboard
2. **Мониторинг** - Health check services (Prometheus, Grafana)
3. **CI/CD** - Automated tests and deployments
4. **Internal services** - Microservices communication

## Excluded Paths

Некоторые endpoints не должны иметь rate limiting:

```env
RATE_LIMIT_EXCLUDE_PATHS=/health,/metrics,/health/detailed
```

**По умолчанию исключены:**
- `/health` - Health checks
- `/metrics` - Prometheus metrics

**Рекомендуется исключить:**
- Health check endpoints
- Metrics endpoints
- Static files (если обслуживаются через backend)

## Мониторинг

### Prometheus Metrics

```promql
# Total rate limit exceeded responses
http_rate_limit_exceeded_total

# By user type
http_rate_limit_exceeded_total{user_type="authenticated"}
http_rate_limit_exceeded_total{user_type="anonymous"}

# By endpoint
http_rate_limit_exceeded_total{endpoint="/graphql"}

# Total blocked requests
http_rate_limit_blocked_total{user_type="authenticated"}
http_rate_limit_blocked_total{user_type="anonymous"}
```

### Structured Logs

Логи rate limit events в JSON формате:

```json
{
  "timestamp": "2025-01-15T10:30:45.123456+00:00",
  "level": "WARNING",
  "logger": "core.middleware.rate_limit",
  "message": "Rate limit exceeded",
  "user_id": 42,
  "ip": "203.0.113.195",
  "user_type": "authenticated",
  "path": "/graphql",
  "limit": 100,
  "event": "rate_limit_exceeded"
}
```

### Поиск в логах

```bash
# Docker logs
docker logs humans_ontology_backend 2>&1 | jq 'select(.event == "rate_limit_exceeded")'

# Grafana Loki
{container="humans_ontology_backend"} | json | event="rate_limit_exceeded"

# Elasticsearch
event: "rate_limit_exceeded" AND level: "WARNING"
```

### Алерты

Настройте алерты в Prometheus/Grafana:

**Много заблокированных запросов:**
```promql
rate(http_rate_limit_blocked_total[5m]) > 10
```

**Частые превышения лимитов:**
```promql
increase(http_rate_limit_exceeded_total[1h]) > 100
```

## Troubleshooting

### Проблема: Пользователи жалуются на 429 ошибки

**Решение 1:** Увеличьте лимит
```env
RATE_LIMIT_AUTH_PER_MINUTE=200  # Было 100
```

**Решение 2:** Добавьте IP в whitelist
```env
RATE_LIMIT_WHITELIST_IPS=127.0.0.1,::1,<проблемный_ip>
```

**Решение 3:** Проверьте логи
```bash
docker logs humans_ontology_backend 2>&1 | jq 'select(.event == "rate_limit_exceeded")' | tail -20
```

### Проблема: Rate limiting не работает

**Проверка 1:** Убедитесь, что enabled
```bash
docker exec humans_ontology_backend env | grep RATE_LIMIT_ENABLED
```

**Проверка 2:** Проверьте Redis
```bash
docker exec humans_ontology_backend redis-cli -h redis ping
# Должно вернуть: PONG
```

**Проверка 3:** Проверьте Redis keys
```bash
docker exec humans_ontology_backend redis-cli -h redis keys "rate_limit:*"
```

### Проблема: Разные пользователи имеют общий лимит

**Причина:** JWT токен не передается или невалиден

**Решение:** Проверьте заголовок Authorization
```bash
curl -H "Authorization: Bearer <valid_token>" https://api.example.com/graphql
```

### Проблема: IP-based rate limiting не работает за прокси

**Причина:** Прокси не передает X-Forwarded-For header

**Решение:** Настройте прокси (nginx):
```nginx
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Real-IP $remote_addr;
```

## Testing

### Manual Testing

```bash
# Test anonymous rate limit (20 req/min)
for i in {1..25}; do
  curl -w "\nStatus: %{http_code}\n" http://localhost:8000/graphql
  sleep 0.1
done
# First 20 should return 200, then 429

# Test authenticated rate limit (100 req/min)
TOKEN="<your_jwt_token>"
for i in {1..105}; do
  curl -H "Authorization: Bearer $TOKEN" \
       -w "\nStatus: %{http_code}\n" \
       http://localhost:8000/graphql
  sleep 0.1
done
# First 100 should return 200, then 429
```

### Automated Testing

```bash
# Run rate limiting tests
pytest tests/test_rate_limiting.py -v

# Run with coverage
pytest tests/test_rate_limiting.py --cov=core.middleware.rate_limit
```

## Best Practices

### 1. Используйте разные лимиты для разных endpoint типов

**Application level (Python):**
```env
# Настройте per-endpoint лимиты в .env
RATE_LIMIT_ENDPOINT_LIMITS={
  "^/graphql$": {"auth": 50, "anon": 10},
  "^/api/search": {"auth": 30, "anon": 5},
  "^/api/export": {"auth": 10, "anon": 2},
  "^/api/upload": {"auth": 20, "anon": 5}
}
```

**Nginx level (Infrastructure):**
```nginx
# GraphQL - strict limit
location /graphql {
    limit_req zone=graphql burst=20 nodelay;
}

# Authentication - moderate limit
location ~ ^/(login|register) {
    limit_req zone=auth burst=10 nodelay;
}

# General API - high limit
location /api/ {
    limit_req zone=general burst=50 nodelay;
}
```

**Рекомендация:** Используйте оба уровня для лучшей защиты

### 2. Логируйте все rate limit events

Помогает обнаружить атаки и проблемы:
```bash
docker logs humans_ontology_backend 2>&1 | \
  jq 'select(.event == "rate_limit_exceeded")' | \
  jq -s 'group_by(.ip) | map({ip: .[0].ip, count: length}) | sort_by(.count) | reverse'
```

### 3. Мониторьте метрики

Создайте дашборд в Grafana:
- Rate limit exceeded по endpoint
- Top IPs by rate limit hits
- Auth vs Anon rate limit violations

### 4. Настройте алерты

```yaml
# Prometheus alert rule
- alert: HighRateLimitViolations
  expr: rate(http_rate_limit_exceeded_total[5m]) > 10
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High rate of rate limit violations"
    description: "{{ $value }} rate limit violations per second in the last 5 minutes"
```

### 5. Документируйте лимиты в API docs

Пример GraphQL документации:
```graphql
"""
Query current user profile.

Rate limit: 100 requests per minute (authenticated users)

Returns User object with profile data.
"""
type Query {
  me: User
}
```

## Интеграция с Nginx

Для production используйте **двухуровневый rate limiting**:

### Level 1: Nginx (Infrastructure level)
- Быстрый, эффективный
- Защита от DDoS
- Per-IP limiting

### Level 2: Python Middleware (Application level)
- Per-user limiting
- Более гибкая логика
- Интеграция с auth system

Пример `nginx.conf`:
```nginx
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=graphql:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=general:10m rate=100r/s;

server {
    # GraphQL endpoint
    location /graphql {
        limit_req zone=graphql burst=20 nodelay;
        limit_req_status 429;
        proxy_pass http://backend;
    }
}
```

## Ограничения и будущие улучшения

### Текущие ограничения

1. **Только per-minute windows** - Нет per-hour или per-day лимитов
2. **Нет GraphQL field-level limiting** - Все GraphQL запросы считаются одинаковыми
3. **Нет tiered limits** - Нельзя настроить разные лимиты для Premium users

### Планируемые улучшения (Future)

- [ ] **GraphQL field-level rate limiting** - Разные лимиты для разных queries/mutations
- [ ] **Multiple time windows** - Per-minute, per-hour, per-day одновременно
- [ ] **Tiered limits** - Premium/Free user tiers с разными лимитами
- [ ] **Adaptive rate limiting** - Автоматическая подстройка лимитов под нагрузку
- [ ] **Rate limit quotas** - Monthly/daily quotas для API keys

## См. также

- [Structured Logging](structured_logging.md) - Логирование rate limit events
- [Prometheus Metrics](prometheus.md) - Метрики rate limiting
- [Security Headers](security_headers.md) - Дополнительная защита

---

**Implemented in:** `core/middleware/rate_limit.py`
**Tests:** `tests/test_rate_limiting.py`
**Configuration:** `.env` файл
