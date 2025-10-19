from typing import List

from sqlalchemy.orm import Session

from auth.models.permission import PermissionModel
from auth.models.role import RoleModel
from auth.models.user import UserModel


class PermissionService:
    @staticmethod
    def check_permission(db: Session, user_id: int, resource: str, action: str) -> bool:
        """Проверка прав доступа пользователя"""
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return False

        # Администраторы имеют все права
        if any(role.name == "admin" for role in user.roles):
            return True

        # Проверка прав для каждой роли пользователя
        for role in user.roles:
            for permission in role.permissions:
                if (permission.resource == resource or permission.resource == "*") and (
                    permission.action == action or permission.action == "*"
                ):
                    return True

        return False

    @staticmethod
    def get_user_permissions(db: Session, user_id: int) -> List[dict]:
        """Получение всех прав пользователя"""
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return []

        permissions = []
        for role in user.roles:
            for permission in role.permissions:
                permissions.append(
                    {
                        "resource": permission.resource,
                        "action": permission.action,
                        "scope": permission.scope,
                    }
                )

        return permissions

    @staticmethod
    def create_permission(
        db: Session, role_id: int, resource: str, action: str, scope: str = "own"
    ) -> PermissionModel:
        """Создание нового права"""
        permission = PermissionModel(role_id=role_id, resource=resource, action=action, scope=scope)

        db.add(permission)
        db.commit()
        db.refresh(permission)

        return permission
