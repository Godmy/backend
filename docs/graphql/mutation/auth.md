# Authentication Mutations

## Register

Register a new user account. Automatically sends verification email.

```graphql
mutation RegisterUser {
  register(input: {
    username: "newuser"
    email: "newuser@example.com"
    password: "SecurePass123!"
    firstName: "Иван"
    lastName: "Иванов"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

**Expected response:**
```json
{
  "data": {
    "register": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "tokenType": "bearer"
    }
  }
}
```

---

## Login

Login with username and password.

```graphql
mutation Login {
  login(input: {
    username: "admin"
    password: "Admin123!"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

**Expected response:**
```json
{
  "data": {
    "login": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "tokenType": "bearer"
    }
  }
}
```

**Important:** Save the `accessToken` for use in protected requests!

---

## Refresh Token

Get new access token using refresh token.

```graphql
mutation RefreshToken {
  refreshToken(input: {
    refreshToken: "YOUR_REFRESH_TOKEN_HERE"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

---

## Verify Email

Verify user email address using token from email.

```graphql
mutation VerifyEmail {
  verifyEmail(input: {
    token: "token_from_email"
  }) {
    success
    message
  }
}
```

**Token TTL:** 24 hours

---

## Request Password Reset

Request password reset email.

```graphql
mutation RequestPasswordReset {
  requestPasswordReset(input: {
    email: "user@example.com"
  }) {
    success
    message
  }
}
```

**Token TTL:** 1 hour
**Rate limiting:** 3 requests/hour per email

---

## Reset Password

Reset password using token from email.

```graphql
mutation ResetPassword {
  resetPassword(input: {
    token: "token_from_email"
    newPassword: "NewPass123!"
  }) {
    success
    message
  }
}
```

---

## OAuth - Login with Google

Login using Google OAuth ID token.

```graphql
mutation LoginWithGoogle {
  loginWithGoogle(input: {
    idToken: "google_id_token_from_frontend"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

**Setup required:**
- `GOOGLE_CLIENT_ID` in .env
- `GOOGLE_CLIENT_SECRET` in .env

See [docs/OAUTH_SETUP.md](../../OAUTH_SETUP.md) for details.

---

## OAuth - Login with Telegram

Login using Telegram authentication data.

```graphql
mutation LoginWithTelegram {
  loginWithTelegram(input: {
    id: "123456789"
    authDate: "1640000000"
    hash: "telegram_hmac_hash"
    firstName: "John"
    username: "johndoe"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

**Setup required:**
- `TELEGRAM_BOT_TOKEN` in .env

See [docs/OAUTH_SETUP.md](../../OAUTH_SETUP.md) for details.

---

## Token Expiration

- **Access tokens:** 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Refresh tokens:** 7 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
- **Verification tokens:** 24 hours
- **Reset tokens:** 1 hour
