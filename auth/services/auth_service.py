from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from auth.services.user_service import UserService
from auth.utils.jwt_handler import jwt_handler

class AuthService:
    @staticmethod
    def register_user(
        db: Session,
        username: str,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Регистрация нового пользователя"""
        user, error = UserService.create_user(db, username, email, password, first_name, last_name)
        if error:
            return None, error
        
        # Создание токенов
        token_data = {"sub": user.username, "user_id": user.id, "email": user.email}
        access_token = jwt_handler.create_access_token(token_data)
        refresh_token = jwt_handler.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }, None

    @staticmethod
    def login_user(db: Session, username: str, password: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Аутентификация пользователя"""
        user = UserService.authenticate_user(db, username, password)
        if not user:
            return None, "Invalid credentials"
        
        # Создание токенов
        token_data = {"sub": user.username, "user_id": user.id, "email": user.email}
        access_token = jwt_handler.create_access_token(token_data)
        refresh_token = jwt_handler.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }, None

    @staticmethod
    def refresh_tokens(refresh_token: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Обновление access token"""
        new_access_token = jwt_handler.refresh_access_token(refresh_token)
        if not new_access_token:
            return None, "Invalid refresh token"
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }, None

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Верификация токена"""
        return jwt_handler.verify_token(token)