# Security Headers Middleware

Automatic security headers added to all HTTP responses to protect against common web vulnerabilities.

## Features

- X-Content-Type-Options: nosniff (prevents MIME type sniffing)
- X-Frame-Options: DENY (prevents clickjacking)
- X-XSS-Protection: 1; mode=block (enables XSS filter)
- Strict-Transport-Security (HSTS): Enforces HTTPS in production
- Content-Security-Policy: Restricts resource loading
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: Restricts dangerous browser features
- Configurable via environment variables
- Can be disabled for development

## Configuration

### Environment Variables

```bash
# .env
SECURITY_HEADERS_ENABLED=true  # Enable/disable (default: true)
CSP_POLICY=default-src 'self'; script-src 'self' 'unsafe-inline'
HSTS_MAX_AGE=31536000  # 1 year in seconds
FRAME_OPTIONS=DENY  # or SAMEORIGIN
ENVIRONMENT=production  # HSTS only enabled in production
```

### Python Configuration

```python
# app.py
from core.middleware.security_headers import SecurityHeadersMiddleware

app.add_middleware(
    SecurityHeadersMiddleware,
    csp_policy="default-src 'self'; script-src 'self' 'unsafe-inline'",
    hsts_max_age=31536000,
    frame_options="DENY"
)
```

## Security Headers Explained

### X-Content-Type-Options: nosniff

Prevents browsers from MIME-sniffing a response away from the declared content-type.

**Attack prevented:** MIME confusion attacks
**Example:** Prevents .txt file being executed as JavaScript

### X-Frame-Options: DENY

Prevents page from being displayed in a frame, iframe, or object.

**Attack prevented:** Clickjacking
**Values:**
- `DENY` - Cannot be framed anywhere
- `SAMEORIGIN` - Can only be framed by same origin

### X-XSS-Protection: 1; mode=block

Enables browser's XSS filtering and blocks the page if attack detected.

**Attack prevented:** Cross-site scripting (XSS)
**Note:** Modern browsers rely more on CSP

### Strict-Transport-Security (HSTS)

Forces browsers to use HTTPS for all requests.

**Attack prevented:** SSL stripping, protocol downgrade attacks
**Example:** `Strict-Transport-Security: max-age=31536000; includeSubDomains`
**Note:** Only sent in production (ENVIRONMENT=production)

### Content-Security-Policy (CSP)

Restricts resources the browser can load.

**Attack prevented:** XSS, data injection, clickjacking
**Default policy:**
```
default-src 'self';
script-src 'self' 'unsafe-inline';
style-src 'self' 'unsafe-inline';
img-src 'self' data:;
font-src 'self';
connect-src 'self';
frame-ancestors 'none';
```

### Referrer-Policy: strict-origin-when-cross-origin

Controls how much referrer information is included with requests.

**Privacy benefit:** Limits information leakage
**Behavior:**
- Same origin: Full URL
- Cross origin: Origin only (no path)

### Permissions-Policy

Restricts browser features and APIs.

**Features disabled:**
- geolocation
- microphone
- camera
- payment
- usb
- magnetometer

## Implementation

- `core/middleware/security_headers.py` - SecurityHeadersMiddleware
- `app.py` - Automatically added to all requests
- `tests/test_security_headers.py` - Comprehensive test suite

## Testing

### Manual Testing

```bash
# Check headers in response
curl -I http://localhost:8000/health

# Expected headers:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
# Content-Security-Policy: default-src 'self'...
# Referrer-Policy: strict-origin-when-cross-origin
# Permissions-Policy: geolocation=(), microphone=()...
```

### Automated Testing

```python
# tests/test_security_headers.py
def test_security_headers(client):
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in response.headers
```

### Browser DevTools

1. Open browser DevTools (F12)
2. Go to Network tab
3. Load any page
4. Click on request
5. Check Response Headers section

## Customization

### Custom CSP Policy

For applications with specific needs:

```python
# More permissive for development
CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "connect-src 'self' ws: wss:"
)

# Strict for production
CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self'; "
    "connect-src 'self'"
)
```

### Frame Options for Embeds

If you need to allow embedding:

```python
FRAME_OPTIONS = "SAMEORIGIN"  # Allow same-origin framing

# Or use CSP instead
CSP_POLICY = "frame-ancestors 'self' https://trusted-domain.com"
```

### HSTS Configuration

```python
# Basic HSTS
HSTS_MAX_AGE = 31536000  # 1 year

# Include subdomains
HSTS_HEADER = f"max-age={HSTS_MAX_AGE}; includeSubDomains"

# Preload (be careful!)
HSTS_HEADER = f"max-age={HSTS_MAX_AGE}; includeSubDomains; preload"
```

## Security Best Practices

### Development vs Production

**Development:**
```bash
SECURITY_HEADERS_ENABLED=true
CSP_POLICY=default-src 'self' 'unsafe-inline' 'unsafe-eval'
FRAME_OPTIONS=SAMEORIGIN
ENVIRONMENT=development  # No HSTS
```

**Production:**
```bash
SECURITY_HEADERS_ENABLED=true
CSP_POLICY=default-src 'self'; script-src 'self'
FRAME_OPTIONS=DENY
ENVIRONMENT=production  # HSTS enabled
HSTS_MAX_AGE=31536000
```

### CSP Violation Reporting

Report CSP violations to track attacks:

```python
CSP_POLICY = (
    "default-src 'self'; "
    "report-uri /api/csp-report; "
    "report-to csp-endpoint"
)
```

### Testing Before Deployment

1. Test with CSP report-only mode:
```python
Content-Security-Policy-Report-Only: default-src 'self'
```

2. Monitor violations for 1-2 weeks
3. Fix legitimate issues
4. Switch to enforcement mode

## Common Issues

### CSP Blocking Resources

**Symptom:** Scripts, styles, or images not loading

**Solution:** Add source to CSP policy
```python
# Allow specific CDN
CSP_POLICY = "script-src 'self' https://cdn.example.com"

# Allow inline styles (not recommended)
CSP_POLICY = "style-src 'self' 'unsafe-inline'"
```

### HSTS Causing Issues

**Symptom:** Cannot access site over HTTP

**Solution:**
- Clear HSTS cache in browser
- Use production HSTS only
- Test with shorter max-age first

### Frame-Ancestors Blocking Embeds

**Symptom:** Cannot embed in iframe

**Solution:**
```python
# Allow specific domain
CSP_POLICY = "frame-ancestors 'self' https://trusted.com"

# Or use X-Frame-Options
FRAME_OPTIONS = "SAMEORIGIN"
```

## Browser Compatibility

| Header | Chrome | Firefox | Safari | Edge |
|--------|--------|---------|--------|------|
| X-Content-Type-Options | ✅ | ✅ | ✅ | ✅ |
| X-Frame-Options | ✅ | ✅ | ✅ | ✅ |
| X-XSS-Protection | ✅ | ⚠️ | ✅ | ✅ |
| HSTS | ✅ | ✅ | ✅ | ✅ |
| CSP | ✅ | ✅ | ✅ | ✅ |
| Referrer-Policy | ✅ | ✅ | ✅ | ✅ |
| Permissions-Policy | ✅ | ✅ | ⚠️ | ✅ |

⚠️ = Partial support or older syntax

## Security Auditing

### Online Tools

- [Security Headers](https://securityheaders.com) - Grade your headers
- [Mozilla Observatory](https://observatory.mozilla.org) - Comprehensive security scan
- [CSP Evaluator](https://csp-evaluator.withgoogle.com) - Check CSP policy

### Command Line

```bash
# Check headers with curl
curl -I https://yourdomain.com | grep -E "^X-|^Content-Security-Policy|^Strict-Transport-Security"

# Test with nmap
nmap --script http-security-headers yourdomain.com
```

### Automated Testing

```python
# tests/test_security_audit.py
import requests

def test_security_headers_production():
    response = requests.get("https://yourdomain.com")

    # Check required headers
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "Content-Security-Policy" in response.headers
    assert "Strict-Transport-Security" in response.headers

    # Check header values
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] in ["DENY", "SAMEORIGIN"]
    assert "max-age" in response.headers["Strict-Transport-Security"]
```

## Related Documentation

- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [MDN Web Security](https://developer.mozilla.org/en-US/docs/Web/Security)
- [Content Security Policy Reference](https://content-security-policy.com/)
