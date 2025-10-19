"""
Token service for email verification and password reset

Manages temporary tokens stored in Redis with TTL
"""

import logging
import secrets
from typing import Optional

from core.redis_client import redis_client

logger = logging.getLogger(__name__)


class TokenService:
    """Service for managing verification and reset tokens"""

    # Token expiration times (in seconds)
    VERIFICATION_TOKEN_TTL = 24 * 60 * 60  # 24 hours
    RESET_TOKEN_TTL = 60 * 60  # 1 hour
    RATE_LIMIT_TTL = 60 * 60  # 1 hour for rate limiting

    # Key prefixes
    VERIFICATION_PREFIX = "verify:"
    RESET_PREFIX = "reset:"
    RATE_LIMIT_PREFIX = "rate:email:"

    @staticmethod
    def generate_token() -> str:
        """
        Generate a secure random token

        Returns:
            URL-safe token string
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_verification_token(user_id: int) -> str:
        """
        Create email verification token

        Args:
            user_id: User ID to associate with token

        Returns:
            Generated token
        """
        token = TokenService.generate_token()
        key = f"{TokenService.VERIFICATION_PREFIX}{token}"

        success = redis_client.set(
            key, str(user_id), expire_seconds=TokenService.VERIFICATION_TOKEN_TTL
        )

        if success:
            logger.info(f"Verification token created for user {user_id}")
        else:
            logger.error(f"Failed to create verification token for user {user_id}")

        return token

    @staticmethod
    def verify_verification_token(token: str) -> Optional[int]:
        """
        Verify and consume verification token

        Args:
            token: Token to verify

        Returns:
            User ID if valid, None otherwise
        """
        key = f"{TokenService.VERIFICATION_PREFIX}{token}"
        user_id_str = redis_client.get(key)

        if user_id_str:
            # Delete token after use (one-time use)
            redis_client.delete(key)
            logger.info(f"Verification token used for user {user_id_str}")
            return int(user_id_str)

        logger.warning(f"Invalid or expired verification token: {token[:10]}...")
        return None

    @staticmethod
    def create_reset_token(user_id: int) -> str:
        """
        Create password reset token

        Args:
            user_id: User ID to associate with token

        Returns:
            Generated token
        """
        token = TokenService.generate_token()
        key = f"{TokenService.RESET_PREFIX}{token}"

        success = redis_client.set(key, str(user_id), expire_seconds=TokenService.RESET_TOKEN_TTL)

        if success:
            logger.info(f"Reset token created for user {user_id}")
        else:
            logger.error(f"Failed to create reset token for user {user_id}")

        return token

    @staticmethod
    def verify_reset_token(token: str) -> Optional[int]:
        """
        Verify and consume reset token

        Args:
            token: Token to verify

        Returns:
            User ID if valid, None otherwise
        """
        key = f"{TokenService.RESET_PREFIX}{token}"
        user_id_str = redis_client.get(key)

        if user_id_str:
            # Delete token after use (one-time use)
            redis_client.delete(key)
            logger.info(f"Reset token used for user {user_id_str}")
            return int(user_id_str)

        logger.warning(f"Invalid or expired reset token: {token[:10]}...")
        return None

    @staticmethod
    def check_rate_limit(email: str, max_requests: int = 3) -> bool:
        """
        Check if email has exceeded rate limit for token requests

        Args:
            email: Email address to check
            max_requests: Maximum requests allowed per hour

        Returns:
            True if under limit, False if exceeded
        """
        key = f"{TokenService.RATE_LIMIT_PREFIX}{email}"
        count = redis_client.get(key)

        if count is None:
            # First request
            redis_client.set(key, "1", expire_seconds=TokenService.RATE_LIMIT_TTL)
            return True

        current_count = int(count)
        if current_count >= max_requests:
            logger.warning(f"Rate limit exceeded for email: {email}")
            return False

        # Increment counter
        redis_client.incr(key)
        return True

    @staticmethod
    def get_rate_limit_remaining(email: str) -> int:
        """
        Get remaining time for rate limit

        Args:
            email: Email address

        Returns:
            Remaining seconds, -1 if no limit
        """
        key = f"{TokenService.RATE_LIMIT_PREFIX}{email}"
        return redis_client.ttl(key)

    @staticmethod
    def invalidate_all_user_tokens(user_id: int):
        """
        Invalidate all tokens for a user (verification and reset)

        Args:
            user_id: User ID
        """
        # Find and delete all verification tokens for user
        verify_keys = redis_client.keys(f"{TokenService.VERIFICATION_PREFIX}*")
        for key in verify_keys:
            stored_user_id = redis_client.get(key)
            if stored_user_id and int(stored_user_id) == user_id:
                redis_client.delete(key)
                logger.info(f"Deleted verification token for user {user_id}")

        # Find and delete all reset tokens for user
        reset_keys = redis_client.keys(f"{TokenService.RESET_PREFIX}*")
        for key in reset_keys:
            stored_user_id = redis_client.get(key)
            if stored_user_id and int(stored_user_id) == user_id:
                redis_client.delete(key)
                logger.info(f"Deleted reset token for user {user_id}")

    @staticmethod
    def get_verification_token_ttl(token: str) -> int:
        """
        Get remaining TTL for verification token

        Args:
            token: Token to check

        Returns:
            Remaining seconds, -1 if no expiry, -2 if not found
        """
        key = f"{TokenService.VERIFICATION_PREFIX}{token}"
        return redis_client.ttl(key)

    @staticmethod
    def get_reset_token_ttl(token: str) -> int:
        """
        Get remaining TTL for reset token

        Args:
            token: Token to check

        Returns:
            Remaining seconds, -1 if no expiry, -2 if not found
        """
        key = f"{TokenService.RESET_PREFIX}{token}"
        return redis_client.ttl(key)


# Convenience instance
token_service = TokenService()
