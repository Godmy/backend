# Auth Module Improvements

Roadmap for enhancing the authentication system with security and UX improvements.

## Current Features ✅

- JWT authentication (access + refresh tokens)
- Email verification
- Password reset
- OAuth (Google + Telegram)
- Rate limiting (email endpoints)
- Roles & Permissions
- User profiles

---

## Proposed Improvements

### 🔴 Tier 1: Critical Security (High Priority)

#### 1. Two-Factor Authentication (2FA/TOTP)

**Why:** Protects against compromised passwords, industry standard for sensitive applications.

**Implementation:**

```python
# auth/models/user.py
class UserModel(BaseModel):
    # ... existing fields ...
    totp_secret = Column(String(32), nullable=True)  # Base32 encoded secret
    totp_enabled = Column(Boolean, default=False)
    backup_codes = Column(JSON, nullable=True)  # List of one-time backup codes

# auth/services/totp_service.py
import pyotp
import qrcode
from io import BytesIO
import base64

class TOTPService:
    @staticmethod
    def generate_secret() -> str:
        """Generate TOTP secret"""
        return pyotp.random_base32()

    @staticmethod
    def generate_qr_code(username: str, secret: str, issuer: str = "МультиПУЛЬТ") -> str:
        """Generate QR code for authenticator apps"""
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=username,
            issuer_name=issuer
        )

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        # Return base64 encoded image
        return base64.b64encode(buffer.getvalue()).decode()

    @staticmethod
    def verify_code(secret: str, code: str) -> bool:
        """Verify TOTP code"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)  # Allow 30s window

    @staticmethod
    def generate_backup_codes(count: int = 10) -> list:
        """Generate backup codes for 2FA"""
        import secrets
        return [secrets.token_hex(4) for _ in range(count)]
```

**GraphQL Mutations:**

```graphql
# Enable 2FA (returns QR code)
mutation {
  enable2FA {
    secret
    qrCode  # Base64 encoded PNG
    backupCodes
  }
}

# Verify and activate 2FA
mutation {
  verify2FA(input: { code: "123456" }) {
    success
    message
  }
}

# Disable 2FA
mutation {
  disable2FA(input: { password: "user_password", code: "123456" }) {
    success
    message
  }
}

# Login with 2FA
mutation {
  login(input: {
    username: "user"
    password: "pass"
    totpCode: "123456"  # Optional, required if 2FA enabled
  }) {
    accessToken
    refreshToken
    requires2FA  # True if 2FA enabled but code not provided
  }
}
```

**Dependencies:**
```txt
pyotp
qrcode[pil]
```

---

#### 2. JWT Refresh Token Rotation

**Why:** If refresh token is stolen, attacker has limited time window.

**Current Issue:** Same refresh token used indefinitely (7 days).

**Solution:**

```python
# auth/services/auth_service.py
class AuthService:
    @staticmethod
    def refresh_tokens(refresh_token: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Refresh tokens with rotation"""
        # Verify old refresh token
        payload = jwt_handler.decode_token(refresh_token)
        if not payload:
            return None, "Invalid refresh token"

        user_id = payload.get("user_id")

        # Check if token is blacklisted (revoked)
        if token_service.is_token_blacklisted(refresh_token):
            return None, "Token has been revoked"

        # Generate NEW tokens (both access AND refresh)
        token_data = {
            "sub": payload.get("sub"),
            "user_id": user_id,
            "email": payload.get("email")
        }
        new_access_token = jwt_handler.create_access_token(token_data)
        new_refresh_token = jwt_handler.create_refresh_token(token_data)

        # Blacklist old refresh token
        token_service.blacklist_token(refresh_token)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,  # NEW token!
            "token_type": "bearer"
        }, None
```

**Redis Storage:**

```python
# auth/services/token_service.py
class TokenService:
    @staticmethod
    def blacklist_token(token: str, ttl: int = 7 * 24 * 60 * 60):
        """Add token to blacklist"""
        redis_client.set(f"blacklist:{token}", "1", expire_seconds=ttl)

    @staticmethod
    def is_token_blacklisted(token: str) -> bool:
        """Check if token is blacklisted"""
        return redis_client.exists(f"blacklist:{token}")
```

**Benefits:**
- Old refresh token can't be reused
- Automatic revocation on refresh
- Limited attack window

---

#### 3. Password Policy Enforcement

**Why:** Prevent weak passwords, comply with security standards.

**Current:** Only checks length >= 8

**Improved:**

```python
# auth/utils/password_validator.py
import re
from typing import Tuple, Optional

class PasswordValidator:
    MIN_LENGTH = 12
    COMMON_PASSWORDS = set([
        "password123", "qwerty123", "admin123", "letmein123",
        # Add more from: https://github.com/danielmiessler/SecLists/tree/master/Passwords
    ])

    @staticmethod
    def validate(password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength

        Requirements:
        - At least 12 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        - Not in common passwords list
        """
        if len(password) < PasswordValidator.MIN_LENGTH:
            return False, f"Password must be at least {PasswordValidator.MIN_LENGTH} characters"

        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"

        if password.lower() in PasswordValidator.COMMON_PASSWORDS:
            return False, "This password is too common and easily guessable"

        return True, None

    @staticmethod
    def calculate_strength(password: str) -> dict:
        """Calculate password strength score (0-100)"""
        score = 0
        feedback = []

        # Length score (up to 30 points)
        length = len(password)
        score += min(30, length * 2)

        # Character variety (up to 40 points)
        if re.search(r"[a-z]", password):
            score += 10
        if re.search(r"[A-Z]", password):
            score += 10
        if re.search(r"\d", password):
            score += 10
        if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            score += 10

        # Complexity (up to 30 points)
        unique_chars = len(set(password))
        score += min(30, unique_chars * 2)

        # Determine strength level
        if score < 40:
            strength = "weak"
            feedback.append("Password is too weak")
        elif score < 70:
            strength = "medium"
            feedback.append("Password is acceptable but could be stronger")
        else:
            strength = "strong"
            feedback.append("Password is strong")

        return {
            "score": score,
            "strength": strength,
            "feedback": feedback
        }
```

**Usage:**

```python
# In registration/password reset
from auth.utils.password_validator import PasswordValidator

valid, error = PasswordValidator.validate(password)
if not valid:
    return None, error

# Return strength to frontend
strength = PasswordValidator.calculate_strength(password)
```

---

#### 4. Account Lockout (Brute Force Protection)

**Why:** Prevent brute force attacks on login.

**Implementation:**

```python
# auth/services/lockout_service.py
from datetime import timedelta

class LockoutService:
    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION = 15 * 60  # 15 minutes

    @staticmethod
    def record_failed_attempt(username: str):
        """Record failed login attempt"""
        key = f"login_attempts:{username}"
        current = redis_client.get(key)

        if current is None:
            redis_client.set(key, "1", expire_seconds=3600)  # Reset after 1 hour
        else:
            attempts = int(current) + 1
            redis_client.set(key, str(attempts), expire_seconds=3600)

            # Lock account if max attempts reached
            if attempts >= LockoutService.MAX_ATTEMPTS:
                LockoutService.lock_account(username)

    @staticmethod
    def lock_account(username: str):
        """Lock account for specified duration"""
        key = f"account_locked:{username}"
        redis_client.set(key, "1", expire_seconds=LockoutService.LOCKOUT_DURATION)

        # Send email notification
        from core.email_service import email_service
        # TODO: Send security alert email

    @staticmethod
    def is_account_locked(username: str) -> bool:
        """Check if account is locked"""
        return redis_client.exists(f"account_locked:{username}")

    @staticmethod
    def get_remaining_lockout_time(username: str) -> int:
        """Get remaining lockout time in seconds"""
        key = f"account_locked:{username}"
        return redis_client.ttl(key)

    @staticmethod
    def reset_attempts(username: str):
        """Reset failed attempts (after successful login)"""
        redis_client.delete(f"login_attempts:{username}")

    @staticmethod
    def get_failed_attempts(username: str) -> int:
        """Get number of failed attempts"""
        attempts = redis_client.get(f"login_attempts:{username}")
        return int(attempts) if attempts else 0
```

**Integration in Login:**

```python
# auth/services/auth_service.py
class AuthService:
    @staticmethod
    def login_user(db: Session, username: str, password: str) -> Tuple[Optional[Dict], Optional[str]]:
        # Check if account is locked
        if LockoutService.is_account_locked(username):
            remaining = LockoutService.get_remaining_lockout_time(username)
            minutes = remaining // 60
            return None, f"Account is locked due to too many failed attempts. Try again in {minutes} minutes."

        # Existing login logic
        user = UserService.get_user_by_username(db, username)
        if not user or not verify_password(password, user.password_hash):
            # Record failed attempt
            LockoutService.record_failed_attempt(username)

            remaining_attempts = LockoutService.MAX_ATTEMPTS - LockoutService.get_failed_attempts(username)
            if remaining_attempts > 0:
                return None, f"Invalid credentials. {remaining_attempts} attempts remaining."
            else:
                return None, "Account locked due to too many failed attempts."

        # Successful login - reset attempts
        LockoutService.reset_attempts(username)

        # ... generate tokens ...
```

---

#### 5. JWT Token Blacklist (Logout)

**Why:** Allow users to logout and invalidate tokens.

**Current Issue:** JWT tokens valid until expiration, even after logout.

**Solution:**

```python
# auth/schemas/auth.py
@strawberry.mutation
def logout(self, info, refresh_token: str) -> MessageResponse:
    """Logout user and blacklist tokens"""
    from auth.services.token_service import token_service
    from auth.utils.jwt_handler import jwt_handler

    # Get access token from Authorization header
    auth_header = info.context.get("request").headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header[7:]

        # Blacklist both tokens
        token_service.blacklist_token(access_token, ttl=30 * 60)  # 30 min
        token_service.blacklist_token(refresh_token, ttl=7 * 24 * 60 * 60)  # 7 days

    return MessageResponse(success=True, message="Logged out successfully")

@strawberry.mutation
def logout_all_devices(self, info, user_id: int) -> MessageResponse:
    """Logout from all devices"""
    # Invalidate all user's tokens
    token_service.invalidate_all_user_tokens(user_id)

    return MessageResponse(success=True, message="Logged out from all devices")
```

**Check blacklist in auth dependency:**

```python
# auth/dependencies/auth.py
def get_current_user(info: Info) -> UserModel:
    token = extract_token(info)

    # Check if token is blacklisted
    if token_service.is_token_blacklisted(token):
        raise Exception("Token has been revoked")

    # ... rest of validation ...
```

---

### 🟡 Tier 2: Important for UX (Medium Priority)

#### 6. Session Management

**Why:** Let users see and manage active sessions/devices.

**Implementation:**

```python
# auth/models/session.py
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON
from core.models.base import BaseModel

class SessionModel(BaseModel):
    """Active user sessions"""
    __tablename__ = "sessions"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    refresh_token_hash = Column(String(255), nullable=False, unique=True)
    device_info = Column(JSON)  # User-Agent, IP, etc.
    ip_address = Column(String(45))
    last_activity = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="sessions")
```

**GraphQL Queries:**

```graphql
query {
  activeSessions {
    id
    deviceInfo {
      browser
      os
      device
    }
    ipAddress
    lastActivity
    isCurrent
  }
}

mutation {
  revokeSession(sessionId: 123) {
    success
    message
  }
}
```

---

#### 7. Login History & Notifications

**Why:** Security awareness, detect suspicious activity.

```python
# auth/models/login_history.py
class LoginHistoryModel(BaseModel):
    """Login attempt history"""
    __tablename__ = "login_history"

    user_id = Column(Integer, ForeignKey("users.id"))
    username = Column(String(255))
    success = Column(Boolean, default=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    location = Column(JSON)  # Country, city from IP
    timestamp = Column(DateTime, default=datetime.utcnow)
    failure_reason = Column(String(255))
```

**Features:**
- Log every login attempt (success + failure)
- Email notification on login from new device/location
- GraphQL query to view login history
- Detect anomalies (login from unusual location)

---

#### 8. Email Change Flow

**Why:** Users need to update email securely.

**Current:** No way to change email.

**Flow:**
1. User requests email change
2. Verification email sent to NEW email
3. Confirmation email sent to OLD email
4. Both must be verified to complete change

```graphql
mutation {
  requestEmailChange(input: {
    newEmail: "new@example.com"
    password: "current_password"
  }) {
    success
    message
  }
}

mutation {
  verifyEmailChange(input: {
    token: "verification_token"
  }) {
    success
    message
  }
}
```

---

#### 9. Social Auth Management

**Why:** Users should manage their OAuth connections.

**GraphQL:**

```graphql
query {
  oauthConnections {
    provider  # google, telegram
    providerEmail
    connectedAt
  }
}

mutation {
  linkOAuthProvider(input: {
    provider: "google"
    idToken: "..."
  }) {
    success
    message
  }
}

mutation {
  unlinkOAuthProvider(provider: "google") {
    success
    message
  }
}
```

**Already implemented in `auth/services/oauth_service.py`:**
- `get_user_oauth_connections()`
- `unlink_oauth_connection()`

Just need to add GraphQL layer.

---

### 🟢 Tier 3: Nice to Have (Low Priority)

#### 10. Magic Link Login (Passwordless)

**Why:** Better UX, no need to remember password.

**Flow:**
1. User enters email
2. Receive email with one-time login link
3. Click link → automatically logged in

```graphql
mutation {
  requestMagicLink(email: "user@example.com") {
    success
    message
  }
}
```

**Token:** Short-lived (15 min), one-time use, stored in Redis.

---

#### 11. Device Fingerprinting

**Why:** Detect suspicious logins from unknown devices.

**Implementation:**
- Collect device info (User-Agent, screen resolution, timezone, etc.)
- Generate fingerprint hash
- Store in session
- Flag login from new device

---

#### 12. CAPTCHA Integration

**Why:** Prevent bot attacks on registration/login.

**Options:**
- Google reCAPTCHA v3 (invisible)
- hCaptcha
- Cloudflare Turnstile

```graphql
mutation {
  register(input: {
    username: "user"
    email: "user@example.com"
    password: "pass"
    captchaToken: "recaptcha_token"
  }) {
    accessToken
    refreshToken
  }
}
```

---

#### 13. API Keys (Machine-to-Machine Auth)

**Why:** Allow services to authenticate without user context.

```python
# auth/models/api_key.py
class APIKeyModel(BaseModel):
    __tablename__ = "api_keys"

    user_id = Column(Integer, ForeignKey("users.id"))
    key_hash = Column(String(255), unique=True)
    name = Column(String(100))  # "Production API", "Development"
    last_used = Column(DateTime)
    expires_at = Column(DateTime)
    scopes = Column(JSON)  # ["read:users", "write:concepts"]
```

**Usage:**
```bash
curl -H "X-API-Key: your_api_key" https://api.example.com/graphql
```

---

#### 14. SSO/SAML (Enterprise)

**Why:** For enterprise customers with corporate identity providers.

**Providers:**
- Okta
- Azure AD
- Google Workspace

**Complex but valuable for B2B SaaS.**

---

## Implementation Priority

### Phase 1: Security Essentials (2-3 weeks)
1. ✅ JWT Refresh Token Rotation
2. ✅ Password Policy Enforcement
3. ✅ Account Lockout
4. ✅ JWT Blacklist (Logout)

### Phase 2: 2FA (1-2 weeks)
5. ✅ Two-Factor Authentication (TOTP)

### Phase 3: User Experience (2-3 weeks)
6. ✅ Session Management
7. ✅ Login History & Notifications
8. ✅ Email Change Flow
9. ✅ Social Auth Management UI

### Phase 4: Advanced Features (optional)
10. Magic Link Login
11. Device Fingerprinting
12. CAPTCHA Integration
13. API Keys

---

## Dependencies to Add

```txt
# requirements.txt

# For 2FA
pyotp
qrcode[pil]

# For password strength
zxcvbn  # Optional: advanced password strength estimation

# For CAPTCHA (if implementing)
# requests  # Already have httpx

# For device fingerprinting
user-agents
geoip2  # For IP geolocation
```

---

## Database Migrations Needed

```bash
# New tables
alembic revision --autogenerate -m "Add 2FA fields to users"
alembic revision --autogenerate -m "Add sessions table"
alembic revision --autogenerate -m "Add login_history table"
alembic revision --autogenerate -m "Add api_keys table"
```

---

## Testing Strategy

### Unit Tests
- Password validation
- TOTP generation/verification
- Token blacklisting
- Lockout logic

### Integration Tests
- 2FA enrollment flow
- Login with 2FA
- Session management
- Email change flow
- Password rotation with history

### Security Tests
- Brute force protection
- Token reuse prevention
- Session hijacking prevention
- CSRF protection

---

## Monitoring & Metrics

**Key Metrics to Track:**
- Failed login attempts per user/IP
- 2FA adoption rate
- Average session duration
- Password reset requests
- OAuth usage vs traditional login
- Account lockout frequency

**Alerting:**
- Spike in failed logins (DDoS/breach)
- Multiple account lockouts (attack)
- Unusual login patterns
- High rate of password resets

---

## Security Checklist

Before deploying improvements:

- [ ] All passwords hashed with bcrypt (already done)
- [ ] HTTPS enforced in production
- [ ] JWT secrets rotated regularly
- [ ] Rate limiting on all auth endpoints
- [ ] 2FA enforced for admin accounts
- [ ] Session tokens stored securely (httpOnly cookies)
- [ ] CSRF protection enabled
- [ ] Security headers configured (nginx)
- [ ] Audit logging for sensitive operations
- [ ] Regular security audits
- [ ] Dependency vulnerability scanning
- [ ] Secrets not in code/git

---

## Resources

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

---

**Recommended Next Steps:**

1. Start with **Phase 1** (Security Essentials) - most critical
2. Implement **2FA** (Phase 2) - highly requested feature
3. Add **Session Management** (Phase 3) - improves UX significantly
4. Consider **Phase 4** based on user feedback and business needs

This roadmap will significantly improve both security and user experience of your auth system! 🚀
