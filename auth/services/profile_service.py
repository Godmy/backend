"""
Profile Management Service.

Handles user profile operations: update, email change, password change, account deletion.

Implementation for User Story #3 - User Profile Management (P1)
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from auth.models.profile import UserProfileModel
from auth.models.user import UserModel
from auth.utils.password import hash_password, verify_password

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for managing user profiles"""

    @staticmethod
    def get_or_create_profile(db: Session, user_id: int) -> UserProfileModel:
        """
        Get existing profile or create new one.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            UserProfileModel instance
        """
        profile = db.query(UserProfileModel).filter(UserProfileModel.user_id == user_id).first()

        if not profile:
            profile = UserProfileModel(user_id=user_id)
            db.add(profile)
            db.commit()
            db.refresh(profile)

        return profile

    @staticmethod
    def update_profile(
        db: Session,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        bio: Optional[str] = None,
        language: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> UserProfileModel:
        """
        Update user profile fields.

        Args:
            db: Database session
            user_id: User ID
            first_name: First name (max 50 chars)
            last_name: Last name (max 50 chars)
            bio: Biography (max 500 chars)
            language: Language code (e.g., "en", "ru")
            timezone: Timezone (e.g., "UTC", "Europe/Moscow")

        Returns:
            Updated UserProfileModel

        Raises:
            ValueError: If validation fails
        """
        profile = ProfileService.get_or_create_profile(db, user_id)

        # Validate and update fields
        if first_name is not None:
            if len(first_name) > 50:
                raise ValueError("First name must be 50 characters or less")
            profile.first_name = first_name

        if last_name is not None:
            if len(last_name) > 50:
                raise ValueError("Last name must be 50 characters or less")
            profile.last_name = last_name

        if bio is not None:
            if len(bio) > 500:
                raise ValueError("Bio must be 500 characters or less")
            profile.bio = bio

        if language is not None:
            profile.language = language

        if timezone is not None:
            profile.timezone = timezone

        db.commit()
        db.refresh(profile)

        return profile

    @staticmethod
    def change_password(
        db: Session, user_id: int, current_password: str, new_password: str
    ) -> bool:
        """
        Change user password.

        Args:
            db: Database session
            user_id: User ID
            current_password: Current password for verification
            new_password: New password

        Returns:
            True if password changed successfully

        Raises:
            ValueError: If current password is incorrect or new password is invalid
        """
        user = db.query(UserModel).filter(UserModel.id == user_id).first()

        if not user:
            raise ValueError("User not found")

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")

        # Validate new password
        if len(new_password) < 8:
            raise ValueError("New password must be at least 8 characters long")

        # Update password
        user.hashed_password = hash_password(new_password)
        db.commit()

        logger.info(f"Password changed for user {user_id}")
        return True

    @staticmethod
    def initiate_email_change(
        db: Session, user_id: int, new_email: str, current_password: str
    ) -> str:
        """
        Initiate email change process.

        Verifies password and checks if email is available.
        Returns verification token to be sent to new email.

        Args:
            db: Database session
            user_id: User ID
            new_email: New email address
            current_password: Current password for verification

        Returns:
            Verification token for new email

        Raises:
            ValueError: If validation fails
        """
        from core.redis_client import redis_client
        import secrets

        user = db.query(UserModel).filter(UserModel.id == user_id).first()

        if not user:
            raise ValueError("User not found")

        # Verify password
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")

        # Check if email already in use
        existing_user = db.query(UserModel).filter(UserModel.email == new_email).first()
        if existing_user:
            raise ValueError("Email already in use")

        # Generate verification token
        token = secrets.token_urlsafe(32)

        # Store in Redis with 24 hour expiry
        redis_client.setex(f"email_change:{token}", 86400, f"{user_id}:{new_email}")

        logger.info(f"Email change initiated for user {user_id} to {new_email}")

        return token

    @staticmethod
    def confirm_email_change(db: Session, token: str) -> bool:
        """
        Confirm email change with verification token.

        Args:
            db: Database session
            token: Verification token from email

        Returns:
            True if email changed successfully

        Raises:
            ValueError: If token is invalid or expired
        """
        from core.redis_client import redis_client

        # Get data from Redis
        data = redis_client.get(f"email_change:{token}")
        if not data:
            raise ValueError("Invalid or expired token")

        # Parse data
        user_id_str, new_email = data.decode().split(":", 1)
        user_id = int(user_id_str)

        # Update email
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Check if email is still available
        existing_user = db.query(UserModel).filter(UserModel.email == new_email).first()
        if existing_user and existing_user.id != user_id:
            raise ValueError("Email already in use")

        user.email = new_email
        user.is_verified = True  # Email verified through this process
        db.commit()

        # Delete token from Redis
        redis_client.delete(f"email_change:{token}")

        logger.info(f"Email changed successfully for user {user_id} to {new_email}")

        return True

    @staticmethod
    def delete_account(db: Session, user_id: int, password: str) -> bool:
        """
        Delete user account (soft delete).

        Args:
            db: Database session
            user_id: User ID
            password: Password for verification

        Returns:
            True if account deleted successfully

        Raises:
            ValueError: If password is incorrect
        """
        user = db.query(UserModel).filter(UserModel.id == user_id).first()

        if not user:
            raise ValueError("User not found")

        # Verify password
        if not verify_password(password, user.hashed_password):
            raise ValueError("Password is incorrect")

        # Soft delete user
        user.soft_delete(deleted_by_id=user_id)
        db.commit()

        logger.info(f"Account soft-deleted for user {user_id}")

        return True
