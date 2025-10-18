from typing import Optional
from strawberry.types import Info
from sqlalchemy.orm import Session
from core.database import get_db
from auth.services.auth_service import AuthService
from auth.services.user_service import UserService

async def get_current_user(info: Info) -> Optional[dict]:
    """Получение текущего пользователя из контекста"""
    request = info.context["request"]
    
    # Получаем токен из заголовка Authorization
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split("Bearer ")[1]
    
    # Верифицируем токен
    payload = AuthService.verify_token(token)
    if not payload:
        return None
    
    # Получаем пользователя из БД
    db: Session = next(get_db())
    user = UserService.get_user_by_id(db, payload.get("user_id"))
    
    if not user or not user.is_active:
        return None
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "is_verified": user.is_verified
    }

async def get_required_user(info: Info) -> dict:
    """Получение текущего пользователя с проверкой аутентификации"""
    user = await get_current_user(info)
    if not user:
        raise Exception("Authentication required")
    return user