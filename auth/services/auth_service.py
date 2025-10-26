from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from auth.services.user_service import UserService
from auth.utils.jwt_handler import jwt_handler
from core.structured_logging import get_logger

logger = get_logger(__name__)


class AuthService:
    @staticmethod
    def register_user(
        db: Session,
        username: str,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Регистрация нового пользователя"""
        logger.info(
            "User registration attempt",
            extra={"username": username, "email": email, "event": "user_registration_attempt"}
        )

        user, error = UserService.create_user(db, username, email, password, first_name, last_name)
        if error:
            logger.warning(
                "User registration failed",
                extra={"username": username, "email": email, "error": error, "event": "user_registration_failed"}
            )
            return None, error

        # Создание токенов
        token_data = {"sub": user.username, "user_id": user.id, "email": user.email}
        access_token = jwt_handler.create_access_token(token_data)
        refresh_token = jwt_handler.create_refresh_token(token_data)

        logger.info(
            "User registered successfully",
            extra={"user_id": user.id, "username": username, "email": email, "event": "user_registered"}
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }, None

    @staticmethod
    def login_user(
        db: Session, username: str, password: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Аутентификация пользователя"""
        logger.info(
            "User login attempt",
            extra={"username": username, "event": "user_login_attempt"}
        )

        user = UserService.authenticate_user(db, username, password)
        if not user:
            logger.warning(
                "User login failed - invalid credentials",
                extra={"username": username, "event": "user_login_failed"}
            )
            return None, "Invalid credentials"

        # Создание токенов
        token_data = {"sub": user.username, "user_id": user.id, "email": user.email}
        access_token = jwt_handler.create_access_token(token_data)
        refresh_token = jwt_handler.create_refresh_token(token_data)

        logger.info(
            "User logged in successfully",
            extra={"user_id": user.id, "username": username, "event": "user_logged_in"}
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }, None

    @staticmethod
    def refresh_tokens(refresh_token: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Обновление access token"""
        logger.debug("Token refresh attempt", extra={"event": "token_refresh_attempt"})

        new_access_token = jwt_handler.refresh_access_token(refresh_token)
        if not new_access_token:
            logger.warning("Token refresh failed - invalid refresh token", extra={"event": "token_refresh_failed"})
            return None, "Invalid refresh token"

        logger.info("Token refreshed successfully", extra={"event": "token_refreshed"})
        return {"access_token": new_access_token, "token_type": "bearer"}, None

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Верификация токена"""
        return jwt_handler.verify_token(token)
