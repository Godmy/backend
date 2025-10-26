from typing import Optional

import strawberry

from auth.dependencies.auth import get_required_user


@strawberry.input
class UserRegistrationInput:
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


@strawberry.input
class UserLoginInput:
    username: str
    password: str


@strawberry.input
class RefreshTokenInput:
    refresh_token: str


@strawberry.input
class EmailVerificationInput:
    token: str


@strawberry.input
class PasswordResetRequestInput:
    email: str


@strawberry.input
class PasswordResetInput:
    token: str
    new_password: str


@strawberry.input
class GoogleAuthInput:
    id_token: str


@strawberry.input
class TelegramAuthInput:
    id: str
    auth_date: str
    hash: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None


@strawberry.type
class AuthPayload:
    access_token: str
    refresh_token: str
    token_type: str


@strawberry.type
class MessageResponse:
    success: bool
    message: str


@strawberry.type
class AuthMutation:
    @strawberry.mutation
    def register(self, info, input: UserRegistrationInput) -> AuthPayload:
        from auth.services.auth_service import AuthService
        from auth.services.token_service import token_service
        from core.email_service import email_service

        # Use DB session from context (no connection leak)
        db = info.context["db"]
        result, error = AuthService.register_user(
            db, input.username, input.email, input.password, input.first_name, input.last_name
        )

        if error:
            raise Exception(error)

        # Create verification token and send email
        user = result["user"]
        verification_token = token_service.create_verification_token(user.id)

        # Send verification email (non-blocking, just log if fails)
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

    @strawberry.mutation
    def verify_email(self, info, input: EmailVerificationInput) -> MessageResponse:
        """Verify email address with token"""
        from auth.services.token_service import token_service
        from auth.services.user_service import UserService

        # Verify token and get user ID
        user_id = token_service.verify_verification_token(input.token)

        if not user_id:
            return MessageResponse(success=False, message="Invalid or expired verification token")

        # Mark user as verified
        # Use DB session from context (no connection leak)
        db = info.context["db"]
        user = UserService.get_user_by_id(db, user_id)

        if not user:
            return MessageResponse(success=False, message="User not found")

        if user.is_verified:
            return MessageResponse(success=True, message="Email already verified")

        # Update user verification status
        user.is_verified = True
        db.commit()

        return MessageResponse(success=True, message="Email verified successfully")

    @strawberry.mutation
    def resend_verification_email(self, info, email: str) -> MessageResponse:
        """Resend verification email"""
        from auth.services.token_service import token_service
        from auth.services.user_service import UserService
        from core.email_service import email_service

        # Check rate limit
        if not token_service.check_rate_limit(email, max_requests=3):
            remaining_time = token_service.get_rate_limit_remaining(email)
            minutes = remaining_time // 60
            return MessageResponse(
                success=False, message=f"Too many requests. Please try again in {minutes} minutes"
            )

        # Find user by email
        # Use DB session from context (no connection leak)
        db = info.context["db"]
        user = UserService.get_user_by_email(db, email)

        if not user:
            # Don't reveal if email exists
            return MessageResponse(
                success=True,
                message="If this email is registered, you will receive a verification link",
            )

        if user.is_verified:
            return MessageResponse(success=False, message="Email already verified")

        # Create new token and send email
        verification_token = token_service.create_verification_token(user.id)
        email_sent = email_service.send_verification_email(
            to_email=email, username=user.username, token=verification_token
        )

        if not email_sent:
            return MessageResponse(
                success=False, message="Failed to send email. Please try again later"
            )

        return MessageResponse(success=True, message="Verification email sent")

    @strawberry.mutation
    def request_password_reset(self, info, input: PasswordResetRequestInput) -> MessageResponse:
        """Request password reset link"""
        from auth.services.token_service import token_service
        from auth.services.user_service import UserService
        from core.email_service import email_service

        # Check rate limit
        if not token_service.check_rate_limit(input.email, max_requests=3):
            remaining_time = token_service.get_rate_limit_remaining(input.email)
            minutes = remaining_time // 60
            return MessageResponse(
                success=False, message=f"Too many requests. Please try again in {minutes} minutes"
            )

        # Find user by email
        # Use DB session from context (no connection leak)
        db = info.context["db"]
        user = UserService.get_user_by_email(db, input.email)

        if not user:
            # Don't reveal if email exists (security best practice)
            return MessageResponse(
                success=True,
                message="If this email is registered, you will receive a password reset link",
            )

        # Create reset token and send email
        reset_token = token_service.create_reset_token(user.id)
        email_sent = email_service.send_password_reset_email(
            to_email=input.email, username=user.username, token=reset_token
        )

        if not email_sent:
            return MessageResponse(
                success=False, message="Failed to send email. Please try again later"
            )

        return MessageResponse(success=True, message="Password reset link sent to your email")

    @strawberry.mutation
    def reset_password(self, info, input: PasswordResetInput) -> MessageResponse:
        """Reset password with token"""
        from auth.services.token_service import token_service
        from auth.services.user_service import UserService
        from auth.utils.security import hash_password

        # Verify token and get user ID
        user_id = token_service.verify_reset_token(input.token)

        if not user_id:
            return MessageResponse(success=False, message="Invalid or expired reset token")

        # Get user
        # Use DB session from context (no connection leak)
        db = info.context["db"]
        user = UserService.get_user_by_id(db, user_id)

        if not user:
            return MessageResponse(success=False, message="User not found")

        # Validate password (basic validation, add more as needed)
        if len(input.new_password) < 8:
            return MessageResponse(
                success=False, message="Password must be at least 8 characters long"
            )

        # Update password
        user.password_hash = hash_password(input.new_password)
        db.commit()

        # Invalidate all existing tokens for this user
        token_service.invalidate_all_user_tokens(user_id)

        return MessageResponse(success=True, message="Password reset successfully")

    @strawberry.mutation
    def login(self, info, input: UserLoginInput) -> AuthPayload:
        from auth.services.auth_service import AuthService

        # Use DB session from context (no connection leak)
        db = info.context["db"]
        result, error = AuthService.login_user(db, input.username, input.password)

        if error:
            raise Exception(error)

        return AuthPayload(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
        )

    @strawberry.mutation
    def refresh_token(self, info, input: RefreshTokenInput) -> AuthPayload:
        from auth.services.auth_service import AuthService

        result, error = AuthService.refresh_tokens(input.refresh_token)

        if error:
            raise Exception(error)

        return AuthPayload(
            access_token=result["access_token"],
            refresh_token=input.refresh_token,  # Refresh token остается тем же
            token_type=result["token_type"],
        )

    @strawberry.mutation
    async def login_with_google(self, info, input: GoogleAuthInput) -> AuthPayload:
        """Authenticate with Google OAuth"""
        from auth.services.oauth_service import OAuthService

        # Use DB session from context (no connection leak)
        db = info.context["db"]
        result, error = await OAuthService.authenticate_with_google(db, input.id_token)

        if error:
            raise Exception(error)

        return AuthPayload(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
        )

    @strawberry.mutation
    def login_with_telegram(self, info, input: TelegramAuthInput) -> AuthPayload:
        """Authenticate with Telegram"""
        from auth.services.oauth_service import OAuthService

        # Convert input to dict
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

        # Use DB session from context (no connection leak)
        db = info.context["db"]
        result, error = OAuthService.authenticate_with_telegram(db, telegram_data)

        if error:
            raise Exception(error)

        return AuthPayload(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
        )
