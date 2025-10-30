# Email Verification & Password Reset

Complete email verification and password reset system using **Redis** for token storage.

## Features

- Email verification for new user registrations
- Password reset flow with secure tokens
- Token expiration and cleanup
- Rate limiting to prevent abuse
- Email notifications

---

## Redis Token Storage

**Redis** is used for storing temporary tokens with automatic expiration.

### Check Tokens

```bash
# Access Redis CLI
docker exec -it templates_redis redis-cli

# Check verification tokens
KEYS verify:*

# Check reset tokens
KEYS reset:*

# Check rate limits
KEYS rate:email:*

# View specific token
GET verify:abc123token

# Check TTL (time to live)
TTL verify:abc123token
```

---

## GraphQL API

**See detailed documentation:** [docs/graphql/mutation/auth.md](../../graphql/mutation/auth.md)

**Available mutations:**
- `register` - Register user (automatically sends verification email)
- `verifyEmail` - Verify email with token
- `requestPasswordReset` - Request password reset email
- `resetPassword` - Reset password with token

---

## Token Configuration

### Token TTLs (Time To Live)

- **Verification tokens:** 24 hours
- **Reset tokens:** 1 hour
- **Email change tokens:** 24 hours

### Rate Limiting

- **3 requests per hour** per email address
- Prevents spam and abuse
- Applies to:
  - Password reset requests
  - Email verification requests
  - Email change requests

---

## Flow Diagrams

### Email Verification Flow

```
1. User registers → register mutation
2. System creates user (is_verified: false)
3. System generates verification token
4. Token stored in Redis (TTL: 24h)
5. Verification email sent to user
6. User clicks link in email
7. Frontend calls verifyEmail mutation
8. Token validated, user marked as verified
9. Token deleted from Redis
```

### Password Reset Flow

```
1. User requests password reset
2. System generates reset token
3. Token stored in Redis (TTL: 1h)
4. Reset email sent to user
5. User clicks link in email
6. Frontend shows password reset form
7. User enters new password
8. Frontend calls resetPassword mutation
9. Password updated, token deleted
```

---

## Implementation

### Files

- **Service:** `auth/services/verification_service.py`
- **Email Service:** `core/email_service.py`
- **GraphQL Schema:** `auth/schemas/user.py`
- **Email Templates:** `templates/emails/`

### Redis Keys

```python
# Verification tokens
verify:{token} → user_id

# Reset tokens
reset:{token} → user_id

# Rate limiting
rate:email:{email} → request_count
```

---

## Configuration

```env
# Redis connection
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# Token expiration (seconds)
VERIFICATION_TOKEN_TTL=86400  # 24 hours
RESET_TOKEN_TTL=3600  # 1 hour

# Rate limiting
EMAIL_RATE_LIMIT=3  # requests per hour
```

---

## Security Features

- **Secure token generation** using `secrets` module
- **Tokens are single-use** (deleted after verification)
- **Automatic expiration** via Redis TTL
- **Rate limiting** prevents abuse
- **HTTPS-only** links in production
- **No token in logs** for security

---

## Error Handling

### Common Errors

**Token expired:**
```json
{
  "message": "Verification token has expired",
  "code": "TOKEN_EXPIRED"
}
```

**Invalid token:**
```json
{
  "message": "Invalid verification token",
  "code": "INVALID_TOKEN"
}
```

**Rate limit exceeded:**
```json
{
  "message": "Too many requests. Please try again later.",
  "code": "RATE_LIMIT_EXCEEDED"
}
```

---

## Testing

```python
# Test verification flow
def test_email_verification():
    # Register user
    response = register_user(email="test@example.com")

    # Get token from email (in tests, token is returned)
    token = get_verification_token_from_email()

    # Verify email
    result = verify_email(token)
    assert result.success is True

    # Check user is verified
    user = get_user_by_email("test@example.com")
    assert user.is_verified is True
```

---

## Monitoring

**Metrics to track:**
- Verification email success rate
- Reset email success rate
- Token expiration rate
- Rate limit hits
- Average time to verification

**Alerts:**
- High token expiration rate (> 50%)
- Email delivery failures
- Frequent rate limit violations

---

## See Full Documentation

**Detailed flow documentation:** [docs/EMAIL_VERIFICATION_FLOW.md](../EMAIL_VERIFICATION_FLOW.md)
