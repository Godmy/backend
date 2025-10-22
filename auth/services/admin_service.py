"""
Admin Service - Business logic for admin operations.

Provides functionality for user management, system statistics, and admin actions.

Implementation for User Story #8 - Admin Panel Features (P1)
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_

from auth.models.user import UserModel
from auth.models.role import RoleModel, UserRoleModel
from core.models.audit_log import AuditLog
from core.models.file import File
from languages.models.concept import ConceptModel
from languages.models.dictionary import DictionaryModel
from languages.models.language import LanguageModel

logger = logging.getLogger(__name__)


class AdminService:
    """Service for admin operations."""

    @staticmethod
    def ban_user(
        db: Session,
        user_id: int,
        admin_user: UserModel,
        reason: Optional[str] = None
    ) -> UserModel:
        """
        Ban a user (set is_active=False).

        Args:
            db: Database session
            user_id: ID of user to ban
            admin_user: Admin performing the action
            reason: Optional reason for ban

        Returns:
            Updated UserModel

        Raises:
            ValueError: If user not found or already banned
        """
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        if not user.is_active:
            raise ValueError(f"User {user.username} is already banned")

        # Cannot ban yourself
        if user.id == admin_user.id:
            raise ValueError("Cannot ban yourself")

        user.is_active = False
        db.commit()
        db.refresh(user)

        logger.info(f"Admin {admin_user.username} banned user {user.username}. Reason: {reason}")

        return user

    @staticmethod
    def unban_user(
        db: Session,
        user_id: int,
        admin_user: UserModel
    ) -> UserModel:
        """
        Unban a user (set is_active=True).

        Args:
            db: Database session
            user_id: ID of user to unban
            admin_user: Admin performing the action

        Returns:
            Updated UserModel

        Raises:
            ValueError: If user not found or not banned
        """
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        if user.is_active:
            raise ValueError(f"User {user.username} is not banned")

        user.is_active = True
        db.commit()
        db.refresh(user)

        logger.info(f"Admin {admin_user.username} unbanned user {user.username}")

        return user

    @staticmethod
    def get_all_users(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        role_name: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[List[UserModel], int]:
        """
        Get all users with filters and pagination.

        Args:
            db: Database session
            limit: Maximum number of results (max 100)
            offset: Offset for pagination
            is_active: Filter by active status
            is_verified: Filter by verified status
            role_name: Filter by role name
            search: Search in username/email

        Returns:
            Tuple of (users list, total count)
        """
        # Limit max results
        limit = min(limit, 100)

        # Build query
        query = db.query(UserModel).options(
            joinedload(UserModel.roles).joinedload(UserRoleModel.role),
            joinedload(UserModel.profile)
        )

        # Apply filters
        if is_active is not None:
            query = query.filter(UserModel.is_active == is_active)

        if is_verified is not None:
            query = query.filter(UserModel.is_verified == is_verified)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    UserModel.username.ilike(search_pattern),
                    UserModel.email.ilike(search_pattern)
                )
            )

        if role_name:
            query = query.join(UserRoleModel).join(RoleModel).filter(
                RoleModel.name == role_name
            )

        # Get total count
        total = query.count()

        # Apply pagination
        users = query.order_by(UserModel.created_at.desc()).offset(offset).limit(limit).all()

        return users, total

    @staticmethod
    def get_system_stats(db: Session) -> Dict[str, Any]:
        """
        Get system statistics.

        Args:
            db: Database session

        Returns:
            Dictionary with system stats
        """
        # User stats
        total_users = db.query(UserModel).count()
        active_users = db.query(UserModel).filter(UserModel.is_active == True).count()
        verified_users = db.query(UserModel).filter(UserModel.is_verified == True).count()

        # New users in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_users_30d = db.query(UserModel).filter(
            UserModel.created_at >= thirty_days_ago
        ).count()

        # Content stats
        total_concepts = db.query(ConceptModel).count()
        total_dictionaries = db.query(DictionaryModel).count()
        total_languages = db.query(LanguageModel).count()

        # File stats
        total_files = db.query(File).count()
        total_file_size = db.query(func.sum(File.size)).scalar() or 0

        # Audit log stats
        total_audit_logs = db.query(AuditLog).count()
        recent_audit_logs = db.query(AuditLog).filter(
            AuditLog.created_at >= thirty_days_ago
        ).count()

        # Role distribution
        role_stats = (
            db.query(RoleModel.name, func.count(UserRoleModel.user_id))
            .join(UserRoleModel, RoleModel.id == UserRoleModel.role_id)
            .group_by(RoleModel.name)
            .all()
        )

        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "verified": verified_users,
                "new_last_30_days": new_users_30d,
                "banned": total_users - active_users
            },
            "content": {
                "concepts": total_concepts,
                "dictionaries": total_dictionaries,
                "languages": total_languages
            },
            "files": {
                "total": total_files,
                "total_size_bytes": total_file_size,
                "total_size_mb": round(total_file_size / (1024 * 1024), 2)
            },
            "audit": {
                "total_logs": total_audit_logs,
                "logs_last_30_days": recent_audit_logs
            },
            "roles": {role: count for role, count in role_stats}
        }

    @staticmethod
    def delete_user_permanently(
        db: Session,
        user_id: int,
        admin_user: UserModel
    ) -> bool:
        """
        Permanently delete a user (hard delete).

        WARNING: This is irreversible!

        Args:
            db: Database session
            user_id: ID of user to delete
            admin_user: Admin performing the action

        Returns:
            True if deleted

        Raises:
            ValueError: If user not found or trying to delete yourself
        """
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        # Cannot delete yourself
        if user.id == admin_user.id:
            raise ValueError("Cannot delete yourself")

        username = user.username

        # Hard delete
        db.delete(user)
        db.commit()

        logger.warning(f"Admin {admin_user.username} permanently deleted user {username}")

        return True

    @staticmethod
    def bulk_assign_role(
        db: Session,
        user_ids: List[int],
        role_name: str,
        admin_user: UserModel
    ) -> int:
        """
        Assign role to multiple users.

        Args:
            db: Database session
            user_ids: List of user IDs
            role_name: Role name to assign
            admin_user: Admin performing the action

        Returns:
            Number of users updated

        Raises:
            ValueError: If role not found
        """
        role = db.query(RoleModel).filter(RoleModel.name == role_name).first()
        if not role:
            raise ValueError(f"Role '{role_name}' not found")

        count = 0
        for user_id in user_ids:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if not user:
                logger.warning(f"User {user_id} not found, skipping")
                continue

            # Check if user already has this role
            existing = db.query(UserRoleModel).filter(
                and_(
                    UserRoleModel.user_id == user_id,
                    UserRoleModel.role_id == role.id
                )
            ).first()

            if existing:
                logger.debug(f"User {user.username} already has role {role_name}")
                continue

            # Assign role
            user_role = UserRoleModel(user_id=user_id, role_id=role.id)
            db.add(user_role)
            count += 1

        db.commit()

        logger.info(f"Admin {admin_user.username} assigned role {role_name} to {count} users")

        return count

    @staticmethod
    def bulk_remove_role(
        db: Session,
        user_ids: List[int],
        role_name: str,
        admin_user: UserModel
    ) -> int:
        """
        Remove role from multiple users.

        Args:
            db: Database session
            user_ids: List of user IDs
            role_name: Role name to remove
            admin_user: Admin performing the action

        Returns:
            Number of users updated

        Raises:
            ValueError: If role not found
        """
        role = db.query(RoleModel).filter(RoleModel.name == role_name).first()
        if not role:
            raise ValueError(f"Role '{role_name}' not found")

        count = db.query(UserRoleModel).filter(
            and_(
                UserRoleModel.user_id.in_(user_ids),
                UserRoleModel.role_id == role.id
            )
        ).delete(synchronize_session=False)

        db.commit()

        logger.info(f"Admin {admin_user.username} removed role {role_name} from {count} users")

        return count
