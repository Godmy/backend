from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from auth.models.user import UserModel
from auth.models.role import RoleModel
from auth.utils.security import hash_password, verify_password, validate_password_strength

class UserService:
    @staticmethod
    def create_user(
        db: Session, 
        username: str, 
        email: str, 
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Tuple[Optional[UserModel], Optional[str]]:
        """Создание нового пользователя"""
        # Проверка существования пользователя
        if db.query(UserModel).filter(UserModel.username == username).first():
            return None, "Username already exists"
        
        if db.query(UserModel).filter(UserModel.email == email).first():
            return None, "Email already exists"
        
        # Валидация пароля
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            return None, message
        
        # Хеширование пароля
        password_hash = hash_password(password)
        
        # Создание пользователя
        user = UserModel(
            username=username,
            email=email,
            password_hash=password_hash
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user, None

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[UserModel]:
        """Аутентификация пользователя"""
        user = db.query(UserModel).filter(UserModel.username == username).first()
        if not user or not user.is_active:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[UserModel]:
        """Получение пользователя по ID"""
        return db.query(UserModel).filter(UserModel.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
        """Получение пользователя по email"""
        return db.query(UserModel).filter(UserModel.email == email).first()

    @staticmethod
    def assign_role_to_user(db: Session, user_id: int, role_name: str) -> bool:
        """Назначение роли пользователю"""
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        role = db.query(RoleModel).filter(RoleModel.name == role_name).first()
        
        if not user or not role:
            return False
        
        if role not in user.roles:
            user.roles.append(role)
            db.commit()
        
        return True

    @staticmethod
    def update_user_password(db: Session, user_id: int, new_password: str) -> Tuple[bool, Optional[str]]:
        """Обновление пароля пользователя"""
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return False, "User not found"
        
        # Валидация пароля
        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            return False, message
        
        user.password_hash = hash_password(new_password)
        db.commit()
        
        return True, None