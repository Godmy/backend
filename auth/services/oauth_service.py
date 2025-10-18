"""
OAuth Service for Google and Telegram authentication

Handles OAuth flow for multiple providers
"""

import hashlib
import hmac
import logging
import os
from typing import Any, Dict, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from auth.models.oauth import OAuthConnectionModel
from auth.models.user import UserModel
from auth.services.user_service import UserService
from auth.utils.jwt_handler import jwt_handler
from auth.utils.security import hash_password

logger = logging.getLogger(__name__)


class OAuthService:
    """Service for OAuth authentication"""

    # OAuth Providers
    GOOGLE = "google"
    TELEGRAM = "telegram"

    @staticmethod
    def get_google_client_id() -> str:
        """Get Google OAuth client ID from environment"""
        return os.getenv("GOOGLE_CLIENT_ID", "")

    @staticmethod
    def get_google_client_secret() -> str:
        """Get Google OAuth client secret from environment"""
        return os.getenv("GOOGLE_CLIENT_SECRET", "")

    @staticmethod
    def get_telegram_bot_token() -> str:
        """Get Telegram bot token from environment"""
        return os.getenv("TELEGRAM_BOT_TOKEN", "")

    @staticmethod
    async def verify_google_token(id_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Google ID token

        Args:
            id_token: Google ID token from frontend

        Returns:
            User info dict if valid, None otherwise
        """
        try:
            from google.auth.transport import requests
            from google.oauth2 import id_token as google_id_token

            client_id = OAuthService.get_google_client_id()
            if not client_id:
                logger.error("GOOGLE_CLIENT_ID not configured")
                return None

            # Verify token
            idinfo = google_id_token.verify_oauth2_token(id_token, requests.Request(), client_id)

            # Token is valid
            return {
                "provider_user_id": idinfo["sub"],
                "email": idinfo.get("email"),
                "email_verified": idinfo.get("email_verified", False),
                "name": idinfo.get("name"),
                "given_name": idinfo.get("given_name"),
                "family_name": idinfo.get("family_name"),
                "picture": idinfo.get("picture"),
                "locale": idinfo.get("locale"),
            }

        except Exception as e:
            logger.error(f"Google token verification failed: {e}")
            return None

    @staticmethod
    def verify_telegram_auth(auth_data: Dict[str, str]) -> bool:
        """
        Verify Telegram Login Widget data

        Args:
            auth_data: Data from Telegram Login Widget

        Returns:
            True if valid, False otherwise
        """
        try:
            bot_token = OAuthService.get_telegram_bot_token()
            if not bot_token:
                logger.error("TELEGRAM_BOT_TOKEN not configured")
                return False

            # Check required fields
            required_fields = ["id", "auth_date", "hash"]
            if not all(field in auth_data for field in required_fields):
                logger.error("Missing required Telegram auth fields")
                return False

            # Extract hash
            received_hash = auth_data.pop("hash")

            # Create data check string
            data_check_arr = [f"{k}={v}" for k, v in sorted(auth_data.items())]
            data_check_string = "\n".join(data_check_arr)

            # Calculate secret key
            secret_key = hashlib.sha256(bot_token.encode()).digest()

            # Calculate hash
            calculated_hash = hmac.new(
                secret_key, data_check_string.encode(), hashlib.sha256
            ).hexdigest()

            # Verify hash
            if calculated_hash != received_hash:
                logger.error("Telegram auth hash verification failed")
                return False

            # Check auth date (optional: add expiration check)
            # auth_date = int(auth_data.get("auth_date", 0))
            # current_time = int(time.time())
            # if current_time - auth_date > 86400:  # 24 hours
            #     logger.error("Telegram auth data expired")
            #     return False

            return True

        except Exception as e:
            logger.error(f"Telegram auth verification failed: {e}")
            return False

    @staticmethod
    def find_or_create_oauth_connection(
        db: Session,
        user_id: int,
        provider: str,
        provider_user_id: str,
        provider_data: Dict[str, Any],
    ) -> OAuthConnectionModel:
        """
        Find existing OAuth connection or create new one

        Args:
            db: Database session
            user_id: User ID
            provider: OAuth provider name
            provider_user_id: User ID from provider
            provider_data: Additional data from provider

        Returns:
            OAuth connection model
        """
        # Try to find existing connection
        connection = (
            db.query(OAuthConnectionModel)
            .filter(
                OAuthConnectionModel.user_id == user_id,
                OAuthConnectionModel.provider == provider,
                OAuthConnectionModel.provider_user_id == provider_user_id,
            )
            .first()
        )

        if connection:
            # Update existing connection
            connection.provider_username = provider_data.get("username")
            connection.provider_email = provider_data.get("email")
            connection.extra_data = provider_data
            db.commit()
            logger.info(f"Updated OAuth connection for user {user_id}, provider {provider}")
        else:
            # Create new connection
            connection = OAuthConnectionModel(
                user_id=user_id,
                provider=provider,
                provider_user_id=provider_user_id,
                provider_username=provider_data.get("username"),
                provider_email=provider_data.get("email"),
                extra_data=provider_data,
            )
            db.add(connection)
            db.commit()
            db.refresh(connection)
            logger.info(f"Created OAuth connection for user {user_id}, provider {provider}")

        return connection

    @staticmethod
    async def authenticate_with_google(
        db: Session, id_token: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate user with Google OAuth

        Args:
            db: Database session
            id_token: Google ID token

        Returns:
            Tuple of (auth_data, error_message)
        """
        # Verify Google token
        google_data = await OAuthService.verify_google_token(id_token)
        if not google_data:
            return None, "Invalid Google token"

        provider_user_id = google_data["provider_user_id"]
        email = google_data.get("email")

        # Check if OAuth connection exists
        oauth_conn = (
            db.query(OAuthConnectionModel)
            .filter(
                OAuthConnectionModel.provider == OAuthService.GOOGLE,
                OAuthConnectionModel.provider_user_id == provider_user_id,
            )
            .first()
        )

        if oauth_conn:
            # Existing user with Google connection
            user = oauth_conn.user
        else:
            # New user or existing user without Google connection
            user = None
            if email:
                # Try to find user by email
                user = UserService.get_user_by_email(db, email)

            if user:
                # Link Google to existing user
                OAuthService.find_or_create_oauth_connection(
                    db, user.id, OAuthService.GOOGLE, provider_user_id, google_data
                )
            else:
                # Create new user
                username = email.split("@")[0] if email else f"google_{provider_user_id[:10]}"
                # Make username unique
                base_username = username
                counter = 1
                while UserService.get_user_by_username(db, username):
                    username = f"{base_username}{counter}"
                    counter += 1

                # Create user with random password (won't be used)
                import secrets

                random_password = secrets.token_urlsafe(32)
                password_hash = hash_password(random_password)

                user = UserModel(
                    username=username,
                    email=email or f"{provider_user_id}@google.oauth",
                    password_hash=password_hash,
                    is_verified=google_data.get(
                        "email_verified", True
                    ),  # Trust Google verification
                )
                db.add(user)
                db.commit()
                db.refresh(user)

                # Create OAuth connection
                OAuthService.find_or_create_oauth_connection(
                    db, user.id, OAuthService.GOOGLE, provider_user_id, google_data
                )

                logger.info(f"Created new user via Google OAuth: {username}")

        # Create JWT tokens
        token_data = {"sub": user.username, "user_id": user.id, "email": user.email}
        access_token = jwt_handler.create_access_token(token_data)
        refresh_token = jwt_handler.create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }, None

    @staticmethod
    def authenticate_with_telegram(
        db: Session, telegram_data: Dict[str, str]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate user with Telegram

        Args:
            db: Database session
            telegram_data: Data from Telegram Login Widget

        Returns:
            Tuple of (auth_data, error_message)
        """
        # Verify Telegram data
        auth_data_copy = telegram_data.copy()
        if not OAuthService.verify_telegram_auth(auth_data_copy):
            return None, "Invalid Telegram authentication data"

        provider_user_id = telegram_data["id"]
        username = telegram_data.get("username", f"telegram_{provider_user_id}")
        first_name = telegram_data.get("first_name", "")
        last_name = telegram_data.get("last_name", "")

        # Check if OAuth connection exists
        oauth_conn = (
            db.query(OAuthConnectionModel)
            .filter(
                OAuthConnectionModel.provider == OAuthService.TELEGRAM,
                OAuthConnectionModel.provider_user_id == provider_user_id,
            )
            .first()
        )

        if oauth_conn:
            # Existing user with Telegram connection
            user = oauth_conn.user
        else:
            # New user - create
            # Make username unique
            base_username = username
            counter = 1
            while UserService.get_user_by_username(db, username):
                username = f"{base_username}{counter}"
                counter += 1

            # Create user with random password (won't be used)
            import secrets

            random_password = secrets.token_urlsafe(32)
            password_hash = hash_password(random_password)

            user = UserModel(
                username=username,
                email=f"{provider_user_id}@telegram.oauth",  # Telegram doesn't provide email
                password_hash=password_hash,
                is_verified=True,  # Trust Telegram
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Create OAuth connection
            OAuthService.find_or_create_oauth_connection(
                db, user.id, OAuthService.TELEGRAM, provider_user_id, telegram_data
            )

            logger.info(f"Created new user via Telegram OAuth: {username}")

        # Create JWT tokens
        token_data = {"sub": user.username, "user_id": user.id, "email": user.email}
        access_token = jwt_handler.create_access_token(token_data)
        refresh_token = jwt_handler.create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }, None

    @staticmethod
    def get_user_oauth_connections(db: Session, user_id: int) -> list:
        """
        Get all OAuth connections for user

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of OAuth connections
        """
        return db.query(OAuthConnectionModel).filter(OAuthConnectionModel.user_id == user_id).all()

    @staticmethod
    def unlink_oauth_connection(
        db: Session, user_id: int, provider: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Unlink OAuth provider from user

        Args:
            db: Database session
            user_id: User ID
            provider: Provider name

        Returns:
            Tuple of (success, error_message)
        """
        connection = (
            db.query(OAuthConnectionModel)
            .filter(
                OAuthConnectionModel.user_id == user_id, OAuthConnectionModel.provider == provider
            )
            .first()
        )

        if not connection:
            return False, f"No {provider} connection found"

        db.delete(connection)
        db.commit()
        logger.info(f"Unlinked {provider} for user {user_id}")

        return True, None


# Convenience function for getting user by username
def get_user_by_username(db: Session, username: str) -> Optional[UserModel]:
    """Get user by username"""
    return db.query(UserModel).filter(UserModel.username == username).first()


# Add to UserService if not exists
if not hasattr(UserService, "get_user_by_username"):
    UserService.get_user_by_username = staticmethod(get_user_by_username)
