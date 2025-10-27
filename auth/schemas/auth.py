"""
GraphQL schemas for authentication, registration, and user session management.
"""

from typing import Optional
import strawberry
from auth.dependencies.auth import get_required_user

# ============================================================================
# Inputs
# ============================================================================

@strawberry.input(description="Input for user registration.")
class UserRegistrationInput:
    username: str = strawberry.field(description="Username (must be unique).")
    email: str = strawberry.field(description="Email (must be unique).")
    password: str = strawberry.field(description="Password (min 8 characters).")
    first_name: Optional[str] = strawberry.field(default=None, description="User's first name.")
    last_name: Optional[str] = strawberry.field(default=None, description="User's last name.")

@strawberry.input(description="Input for user login.")
class UserLoginInput:
    username: str = strawberry.field(description="Username or email.")
    password: str = strawberry.field(description="Password.")

@strawberry.input(description="Input for refreshing an access token.")
class RefreshTokenInput:
    refresh_token: str = strawberry.field(description="The refresh token received during login.")

@strawberry.input(description="Input for email verification.")
class EmailVerificationInput:
    token: str = strawberry.field(description="The verification token from the email.")

@strawberry.input(description="Input for requesting a password reset.")
class PasswordResetRequestInput:
    email: str = strawberry.field(description="The user's email address to send the reset link to.")

@strawberry.input(description="Input for resetting a password.")
class PasswordResetInput:
    token: str = strawberry.field(description="The password reset token from the email.")
    new_password: str = strawberry.field(description="The new password (min 8 characters).")

@strawberry.input(description="Input for Google OAuth authentication.")
class GoogleAuthInput:
    id_token: str = strawberry.field(description="The ID token received from Google.")

@strawberry.input(description="Input for Telegram OAuth authentication.")
class TelegramAuthInput:
    id: str = strawberry.field(description="User ID from Telegram.")
    auth_date: str = strawberry.field(description="Authentication date from Telegram.")
    hash: str = strawberry.field(description="HMAC hash to verify data integrity.")
    first_name: Optional[str] = strawberry.field(default=None, description="User's first name from Telegram.")
    last_name: Optional[str] = strawberry.field(default=None, description="User's last name from Telegram.")
    username: Optional[str] = strawberry.field(default=None, description="Username from Telegram.")
    photo_url: Optional[str] = strawberry.field(default=None, description="Profile photo URL from Telegram.")

# ============================================================================
# Payloads & Responses
# ============================================================================

@strawberry.type(description="Payload containing authentication tokens.")
class AuthPayload:
    access_token: str = strawberry.field(description="JWT access token for authenticated requests.")
    refresh_token: str = strawberry.field(description="Token to get a new access token without re-authenticating.")
    token_type: str = strawberry.field(description="Token type (always 'bearer').")

@strawberry.type(description="Generic response with a success status and a message.")
class MessageResponse:
    success: bool = strawberry.field(description="Indicates if the operation was successful.")
    message: str = strawberry.field(description="A descriptive message about the result.")

# ============================================================================
# Mutations
# ============================================================================

@strawberry.type
class AuthMutation:
    @strawberry.mutation(description="""Registers a new user account.

Example:
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
  }
}
```
""")
    def register(self, info, input: UserRegistrationInput) -> AuthPayload:
        from auth.services.auth_service import AuthService
        from auth.services.token_service import token_service
        from core.email_service import email_service

        db = info.context["db"]
        result, error = AuthService.register_user(
            db, input.username, input.email, input.password, input.first_name, input.last_name
        )
        if error:
            raise Exception(error)

        user = result["user"]
        verification_token = token_service.create_verification_token(user.id)
        email_sent = email_service.send_verification_email(
            to_email=input.email, username=input.username, token=verification_token
        )
        if not email_sent:
            import logging
            logging.warning(f"Failed to send verification email to {input.email}")

        return AuthPayload(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
        )

    @strawberry.mutation(description="""Logs in a user with username and password.

Example:
```graphql
mutation Login {
  login(input: {
    username: "admin"
    password: "Admin123!"
  }) {
    accessToken
    refreshToken
  }
}
```
""")
    def login(self, info, input: UserLoginInput) -> AuthPayload:
        from auth.services.auth_service import AuthService
        db = info.context["db"]
        result, error = AuthService.login_user(db, input.username, input.password)
        if error:
            raise Exception(error)
        return AuthPayload(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
        )

    @strawberry.mutation(description="""Refreshes an access token using a refresh token.

Example:
```graphql
mutation RefreshToken {
  refreshToken(input: {
    refreshToken: "YOUR_REFRESH_TOKEN_HERE"
  }) {
    accessToken
    refreshToken
  }
}
```
""")
    def refresh_token(self, info, input: RefreshTokenInput) -> AuthPayload:
        from auth.services.auth_service import AuthService
        result, error = AuthService.refresh_tokens(input.refresh_token)
        if error:
            raise Exception(error)
        return AuthPayload(
            access_token=result["access_token"],
            refresh_token=input.refresh_token,
            token_type=result["token_type"],
        )

    @strawberry.mutation(description="""Verifies a user's email address using a token from the verification email.

Example:
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
""")
    def verify_email(self, info, input: EmailVerificationInput) -> MessageResponse:
        from auth.services.token_service import token_service
        from auth.services.user_service import UserService

        user_id = token_service.verify_verification_token(input.token)
        if not user_id:
            return MessageResponse(success=False, message="Invalid or expired verification token")

        db = info.context["db"]
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return MessageResponse(success=False, message="User not found")
        if user.is_verified:
            return MessageResponse(success=True, message="Email already verified")

        user.is_verified = True
        db.commit()
        return MessageResponse(success=True, message="Email verified successfully")

    @strawberry.mutation(description="Resends the email verification link.")
    def resend_verification_email(self, info, email: str) -> MessageResponse:
        from auth.services.token_service import token_service
        from auth.services.user_service import UserService
        from core.email_service import email_service

        if not token_service.check_rate_limit(email, max_requests=3):
            remaining_time = token_service.get_rate_limit_remaining(email)
            minutes = remaining_time // 60
            return MessageResponse(
                success=False, message=f"Too many requests. Please try again in {minutes} minutes"
            )

        db = info.context["db"]
        user = UserService.get_user_by_email(db, email)
        if not user:
            return MessageResponse(
                success=True,
                message="If this email is registered, you will receive a verification link",
            )
        if user.is_verified:
            return MessageResponse(success=False, message="Email already verified")

        verification_token = token_service.create_verification_token(user.id)
        email_sent = email_service.send_verification_email(
            to_email=email, username=user.username, token=verification_token
        )
        if not email_sent:
            return MessageResponse(
                success=False, message="Failed to send email. Please try again later"
            )
        return MessageResponse(success=True, message="Verification email sent")

    @strawberry.mutation(description="""Requests a password reset email to be sent.

Example:
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
""")
    def request_password_reset(self, info, input: PasswordResetRequestInput) -> MessageResponse:
        from auth.services.token_service import token_service
        from auth.services.user_service import UserService
        from core.email_service import email_service

        if not token_service.check_rate_limit(input.email, max_requests=3):
            remaining_time = token_service.get_rate_limit_remaining(input.email)
            minutes = remaining_time // 60
            return MessageResponse(
                success=False, message=f"Too many requests. Please try again in {minutes} minutes"
            )

        db = info.context["db"]
        user = UserService.get_user_by_email(db, input.email)
        if not user:
            return MessageResponse(
                success=True,
                message="If this email is registered, you will receive a password reset link",
            )

        reset_token = token_service.create_reset_token(user.id)
        email_sent = email_service.send_password_reset_email(
            to_email=input.email, username=user.username, token=reset_token
        )
        if not email_sent:
            return MessageResponse(
                success=False, message="Failed to send email. Please try again later"
            )
        return MessageResponse(success=True, message="Password reset link sent to your email")

    @strawberry.mutation(description="""Resets the user's password using a token from the reset email.

Example:
```graphql
mutation ResetPassword {
  resetPassword(input: {
    token: "token_from_email"
    newPassword: "NewSecurePassword123!"
  }) {
    success
    message
  }
}
```
""")
    def reset_password(self, info, input: PasswordResetInput) -> MessageResponse:
        from auth.services.token_service import token_service
        from auth.services.user_service import UserService
        from auth.utils.security import hash_password

        user_id = token_service.verify_reset_token(input.token)
        if not user_id:
            return MessageResponse(success=False, message="Invalid or expired reset token")

        db = info.context["db"]
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return MessageResponse(success=False, message="User not found")

        if len(input.new_password) < 8:
            return MessageResponse(
                success=False, message="Password must be at least 8 characters long"
            )

        user.password_hash = hash_password(input.new_password)
        db.commit()
        token_service.invalidate_all_user_tokens(user_id)
        return MessageResponse(success=True, message="Password reset successfully")

    @strawberry.mutation(description="""Authenticates a user with a Google ID token.

Example:
```graphql
mutation LoginWithGoogle {
  loginWithGoogle(input: {
    idToken: "google_id_token_from_frontend"
  }) {
    accessToken
    refreshToken
  }
}
```
""")
    async def login_with_google(self, info, input: GoogleAuthInput) -> AuthPayload:
        from auth.services.oauth_service import OAuthService
        db = info.context["db"]
        result, error = await OAuthService.authenticate_with_google(db, input.id_token)
        if error:
            raise Exception(error)
        return AuthPayload(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
        )

    @strawberry.mutation(description="""Authenticates a user with Telegram authentication data.

Example:
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
  }
}
```
""")
    def login_with_telegram(self, info, input: TelegramAuthInput) -> AuthPayload:
        from auth.services.oauth_service import OAuthService
        telegram_data = {
            "id": input.id,
            "auth_date": input.auth_date,
            "hash": input.hash,
        }
        if input.first_name:
            telegram_data["first_name"] = input.first_name
        if input.last_name:
            telegram_data["last_name"] = input.last_name
        if input.username:
            telegram_data["username"] = input.username
        if input.photo_url:
            telegram_data["photo_url"] = input.photo_url

        db = info.context["db"]
        result, error = OAuthService.authenticate_with_telegram(db, telegram_data)
        if error:
            raise Exception(error)
        return AuthPayload(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
        )
