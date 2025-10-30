# OAuth Authentication Setup Guide

Complete guide for implementing Google and Telegram OAuth authentication in your application.

## Table of Contents

- [Overview](#overview)
- [Google OAuth Setup](#google-oauth-setup)
- [Telegram OAuth Setup](#telegram-oauth-setup)
- [GraphQL API](#graphql-api)
- [Frontend Integration](#frontend-integration)
- [Testing](#testing)
- [Security Best Practices](#security-best-practices)

---

## Overview

The application supports OAuth authentication through:

1. **Google OAuth 2.0** - Sign in with Google
2. **Telegram Login Widget** - Sign in with Telegram

### How It Works

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│   Frontend  │       │   Backend    │       │   Provider  │
│   (React)   │       │   (GraphQL)  │       │ (Google/TG) │
└──────┬──────┘       └──────┬───────┘       └──────┬──────┘
       │                     │                       │
       │ 1. User clicks      │                       │
       │    "Sign in"        │                       │
       ├────────────────────►│                       │
       │                     │                       │
       │ 2. Redirect to      │                       │
       │    provider         │                       │
       ├─────────────────────┼──────────────────────►│
       │                     │                       │
       │ 3. User authorizes  │                       │
       │    (enters creds)   │                       │
       │                     │                       │
       │ 4. Provider returns │                       │
       │    token/data       │                       │
       │◄────────────────────┼───────────────────────┤
       │                     │                       │
       │ 5. Send token to    │                       │
       │    backend          │                       │
       ├────────────────────►│                       │
       │                     │ 6. Verify token       │
       │                     ├──────────────────────►│
       │                     │ 7. User data          │
       │                     │◄──────────────────────┤
       │                     │                       │
       │                     │ 8. Create/link user   │
       │                     │    in database        │
       │                     │                       │
       │ 9. Return JWT       │                       │
       │◄────────────────────┤                       │
       │                     │                       │
```

### User Creation Logic

- **First-time OAuth login**: Creates new user with:
  - Username from email (Google) or Telegram username
  - Random secure password (not used for OAuth login)
  - Auto-verified status (`is_verified: true`)
  - OAuth connection record in `oauth_connections` table

- **Existing email**: Links OAuth provider to existing account
- **Existing OAuth connection**: Returns existing user

---

## Google OAuth Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **Google+ API** or **Google Identity API**

### Step 2: Create OAuth 2.0 Credentials

1. Navigate to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Select **Web application** as application type
4. Configure OAuth consent screen:
   - **Application name**: Your app name
   - **Support email**: Your email
   - **Authorized domains**: Your domain (e.g., `yourdomain.com`)

### Step 3: Configure Authorized URIs

**Authorized JavaScript origins:**
```
http://localhost:5173
http://localhost:3000
https://yourdomain.com
```

**Authorized redirect URIs:**
```
http://localhost:5173/auth/google/callback
https://yourdomain.com/auth/google/callback
```

### Step 4: Copy Credentials

After creating, you'll receive:
- **Client ID**: `123456789-abcdefg.apps.googleusercontent.com`
- **Client Secret**: `GOCSPX-AbCdEfGhIjKlMnOpQrStUvWxYz`

### Step 5: Update Environment Variables

```bash
# .env
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-AbCdEfGhIjKlMnOpQrStUvWxYz
```

---

## Telegram OAuth Setup

### Step 1: Create Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow instructions to create bot:
   - Choose bot name (e.g., "MyApp Login Bot")
   - Choose username (e.g., "myapp_login_bot")
4. **Copy the bot token** (format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Configure Login Widget Domain

1. Send `/setdomain` command to BotFather
2. Select your bot
3. Enter your domain:
   - For development: `localhost` or `127.0.0.1`
   - For production: `yourdomain.com`

### Step 3: Update Environment Variables

```bash
# .env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### Step 4: Add Login Widget to Frontend

Add Telegram script to your HTML:

```html
<script async src="https://telegram.org/js/telegram-widget.js?22"
        data-telegram-login="myapp_login_bot"
        data-size="large"
        data-onauth="onTelegramAuth(user)"
        data-request-access="write"></script>
```

---

## GraphQL API

### Mutations

#### 1. Login with Google

```graphql
mutation LoginWithGoogle {
  loginWithGoogle(input: {
    idToken: "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE..."
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

**Input:**
- `idToken` (String!): Google ID token from frontend

**Response:**
```json
{
  "data": {
    "loginWithGoogle": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "tokenType": "bearer"
    }
  }
}
```

#### 2. Login with Telegram

```graphql
mutation LoginWithTelegram {
  loginWithTelegram(input: {
    id: "123456789"
    authDate: "1640000000"
    hash: "abc123def456..."
    firstName: "John"
    lastName: "Doe"
    username: "johndoe"
    photoUrl: "https://t.me/i/userpic/..."
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

**Input:**
- `id` (String!): Telegram user ID
- `authDate` (String!): Authentication timestamp
- `hash` (String!): HMAC-SHA256 signature
- `firstName` (String): User's first name
- `lastName` (String): User's last name
- `username` (String): Telegram username
- `photoUrl` (String): Profile photo URL

**Response:**
```json
{
  "data": {
    "loginWithTelegram": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "tokenType": "bearer"
    }
  }
}
```

---

## Frontend Integration

### Google OAuth (React + @react-oauth/google)

#### 1. Install Package

```bash
npm install @react-oauth/google
```

#### 2. Setup Provider

```tsx
// App.tsx
import { GoogleOAuthProvider } from '@react-oauth/google';

function App() {
  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
      <YourApp />
    </GoogleOAuthProvider>
  );
}
```

#### 3. Login Button Component

```tsx
// GoogleLoginButton.tsx
import { useGoogleLogin } from '@react-oauth/google';
import { useMutation } from '@apollo/client';
import { LOGIN_WITH_GOOGLE } from './graphql/mutations';

export const GoogleLoginButton = () => {
  const [loginWithGoogle] = useMutation(LOGIN_WITH_GOOGLE);

  const handleGoogleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        const { data } = await loginWithGoogle({
          variables: {
            input: { idToken: tokenResponse.credential }
          }
        });

        // Save tokens
        localStorage.setItem('accessToken', data.loginWithGoogle.accessToken);
        localStorage.setItem('refreshToken', data.loginWithGoogle.refreshToken);

        // Redirect to dashboard
        window.location.href = '/dashboard';
      } catch (error) {
        console.error('Google login failed:', error);
        alert('Login failed. Please try again.');
      }
    },
    onError: () => {
      console.error('Google login error');
      alert('Google login failed. Please try again.');
    }
  });

  return (
    <button onClick={() => handleGoogleLogin()}>
      Sign in with Google
    </button>
  );
};
```

#### 4. GraphQL Mutation

```tsx
// graphql/mutations.ts
import { gql } from '@apollo/client';

export const LOGIN_WITH_GOOGLE = gql`
  mutation LoginWithGoogle($input: GoogleAuthInput!) {
    loginWithGoogle(input: $input) {
      accessToken
      refreshToken
      tokenType
    }
  }
`;
```

### Telegram OAuth (React)

#### 1. Create Telegram Login Component

```tsx
// TelegramLoginButton.tsx
import { useEffect, useRef } from 'react';
import { useMutation } from '@apollo/client';
import { LOGIN_WITH_TELEGRAM } from './graphql/mutations';

export const TelegramLoginButton = () => {
  const [loginWithTelegram] = useMutation(LOGIN_WITH_TELEGRAM);
  const scriptRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Define callback for Telegram widget
    (window as any).onTelegramAuth = async (user: any) => {
      try {
        const { data } = await loginWithTelegram({
          variables: {
            input: {
              id: user.id.toString(),
              authDate: user.auth_date.toString(),
              hash: user.hash,
              firstName: user.first_name,
              lastName: user.last_name,
              username: user.username,
              photoUrl: user.photo_url
            }
          }
        });

        // Save tokens
        localStorage.setItem('accessToken', data.loginWithTelegram.accessToken);
        localStorage.setItem('refreshToken', data.loginWithTelegram.refreshToken);

        // Redirect to dashboard
        window.location.href = '/dashboard';
      } catch (error) {
        console.error('Telegram login failed:', error);
        alert('Login failed. Please try again.');
      }
    };

    // Inject Telegram script
    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.setAttribute('data-telegram-login', 'YOUR_BOT_USERNAME');
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-onauth', 'onTelegramAuth(user)');
    script.setAttribute('data-request-access', 'write');
    script.async = true;

    if (scriptRef.current) {
      scriptRef.current.appendChild(script);
    }

    return () => {
      // Cleanup
      delete (window as any).onTelegramAuth;
    };
  }, [loginWithTelegram]);

  return <div ref={scriptRef}></div>;
};
```

#### 2. GraphQL Mutation

```tsx
// graphql/mutations.ts
export const LOGIN_WITH_TELEGRAM = gql`
  mutation LoginWithTelegram($input: TelegramAuthInput!) {
    loginWithTelegram(input: $input) {
      accessToken
      refreshToken
      tokenType
    }
  }
`;
```

### Combined Login Page

```tsx
// LoginPage.tsx
import { GoogleLoginButton } from './GoogleLoginButton';
import { TelegramLoginButton } from './TelegramLoginButton';

export const LoginPage = () => {
  return (
    <div className="login-page">
      <h1>Sign in to MyApp</h1>

      <div className="oauth-buttons">
        <GoogleLoginButton />
        <TelegramLoginButton />
      </div>

      <div className="divider">
        <span>OR</span>
      </div>

      <form className="email-login">
        {/* Traditional email/password login */}
      </form>
    </div>
  );
};
```

---

## Testing

### Manual Testing

#### 1. Start Services

```bash
docker-compose -f docker-compose.dev.yml up -d
```

#### 2. Test Google OAuth

1. Open GraphQL Playground: http://localhost:8000/graphql
2. Get Google ID token from frontend (use Google's OAuth playground)
3. Execute mutation:

```graphql
mutation {
  loginWithGoogle(input: {
    idToken: "YOUR_GOOGLE_ID_TOKEN"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

#### 3. Test Telegram OAuth

1. Get auth data from Telegram Login Widget
2. Execute mutation:

```graphql
mutation {
  loginWithTelegram(input: {
    id: "123456789"
    authDate: "1640000000"
    hash: "calculated_hash_from_telegram"
    firstName: "John"
    username: "johndoe"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

#### 4. Verify Database

```bash
# Check users table
docker exec -it templates_db_dev psql -U template_user -d templates

\c templates
SELECT * FROM users WHERE email LIKE '%@google.oauth' OR email LIKE '%@telegram.oauth';

# Check OAuth connections
SELECT * FROM oauth_connections;
```

### Automated Testing

```bash
# Run OAuth tests
pytest tests/test_oauth.py -v

# Run specific test
pytest tests/test_oauth.py::TestGoogleOAuth::test_login_with_google -v
```

---

## Security Best Practices

### 1. Token Verification

The backend **ALWAYS verifies** tokens with the provider:

- **Google**: Verifies ID token signature with Google's public keys
- **Telegram**: Verifies HMAC signature using bot token as secret

**Never trust tokens from the frontend without verification!**

### 2. HTTPS in Production

```env
# Production .env
FRONTEND_URL=https://yourdomain.com

# Ensure CORS allows only your domain
ALLOWED_ORIGINS=https://yourdomain.com
```

### 3. OAuth Credentials Security

- **Never commit** `.env` file to Git
- Store credentials in secure vault (AWS Secrets Manager, HashiCorp Vault)
- Rotate credentials periodically
- Use separate credentials for dev/staging/production

### 4. Client-Side Storage

```tsx
// DON'T store tokens in localStorage if possible (XSS vulnerable)
// localStorage.setItem('accessToken', token);

// BETTER: Use httpOnly cookies (set from backend)
// Or use secure session storage with proper CSP headers
```

### 5. Rate Limiting

Consider adding rate limiting for OAuth endpoints:

```python
# TODO: Add rate limiting
# Example: Max 10 OAuth attempts per IP per minute
```

### 6. Account Linking

When existing user logs in with OAuth:

- Check if email matches existing account
- Ask user to confirm account linking
- Send notification email about new OAuth connection

### 7. Audit Logging

Log all OAuth events:

```python
logger.info(
    "oauth_login_success",
    provider="google",
    user_id=user.id,
    email=user.email,
    ip_address=request.client.host
)
```

---

## Troubleshooting

### Google OAuth Issues

#### "Invalid token" error

**Cause**: Token expired or invalid Client ID

**Solution**:
1. Check `GOOGLE_CLIENT_ID` matches the one from Google Console
2. Ensure token is fresh (tokens expire after ~1 hour)
3. Verify OAuth consent screen is configured correctly

#### "Redirect URI mismatch"

**Cause**: Frontend redirect URI not authorized

**Solution**:
1. Add redirect URI to Google Console
2. Ensure exact match (including trailing slash)
3. Check http vs https

### Telegram OAuth Issues

#### "Invalid hash" error

**Cause**: HMAC verification failed

**Solution**:
1. Check `TELEGRAM_BOT_TOKEN` is correct
2. Ensure all auth data fields are included
3. Verify domain is set correctly in BotFather

#### "auth_date too old" (if implemented)

**Cause**: Telegram auth data expired

**Solution**:
1. Check system time is synchronized
2. Reduce acceptable auth age window
3. Ask user to authenticate again

### Database Issues

#### "oauth_connections table does not exist"

**Cause**: Missing migration

**Solution**:
```bash
# Run migrations
alembic upgrade head

# Or create table manually
docker exec -it templates_db_dev psql -U template_user -d templates
# Then create table using schema from auth/models/oauth.py
```

---

## Environment Variables Reference

### Required for Google OAuth

```env
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_client_secret
```

### Required for Telegram OAuth

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### Optional OAuth Settings

```env
# Auto-verify OAuth users (default: true)
OAUTH_AUTO_VERIFY=true

# Allow account linking by email (default: true)
OAUTH_LINK_BY_EMAIL=true
```

---

## Next Steps

### Production Checklist

- [ ] Configure production OAuth credentials
- [ ] Set up HTTPS with valid SSL certificate
- [ ] Configure CORS for production domain
- [ ] Implement rate limiting
- [ ] Set up audit logging
- [ ] Test OAuth flow in production environment
- [ ] Monitor OAuth success/failure rates
- [ ] Set up alerts for OAuth errors

### Optional Enhancements

- [ ] Add GitHub OAuth
- [ ] Add Microsoft OAuth
- [ ] Add Apple Sign In
- [ ] Implement account unlinking
- [ ] Add OAuth connections management page
- [ ] Send email notifications on new OAuth connections
- [ ] Implement OAuth token refresh (for providers that support it)

---

## Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Telegram Login Widget Documentation](https://core.telegram.org/widgets/login)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)

---

**Ready to authenticate!** Your OAuth system is now fully configured and documented.
