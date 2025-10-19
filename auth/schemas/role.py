from typing import List, Optional

import strawberry

from auth.dependencies.auth import get_required_user


@strawberry.type
class Permission:
    id: int
    role_id: int
    resource: str
    action: str
    scope: str


@strawberry.type
class Role:
    id: int
    name: str
    description: Optional[str]
    permissions: List[Permission]


@strawberry.input
class PermissionInput:
    resource: str
    action: str
    scope: str = "own"


@strawberry.input
class RoleInput:
    name: str
    description: Optional[str] = None


@strawberry.input
class RoleUpdateInput:
    name: Optional[str] = None
    description: Optional[str] = None


@strawberry.type
class RoleQuery:
    @strawberry.field
    async def roles(self, info) -> List[Role]:
        """Получение списка всех ролей (только для администраторов)"""
        from auth.models.role import RoleModel
        from auth.services.permission_service import PermissionService
        from core.database import get_db

        current_user = await get_required_user(info)
        db = next(get_db())

        # Проверяем права доступа
        if not PermissionService.check_permission(db, current_user["id"], "role", "read"):
            raise Exception("Insufficient permissions")

        roles = db.query(RoleModel).all()

        result = []
        for role in roles:
            permissions = [
                Permission(
                    id=perm.id,
                    role_id=perm.role_id,
                    resource=perm.resource,
                    action=perm.action,
                    scope=perm.scope,
                )
                for perm in role.permissions
            ]
            result.append(
                Role(
                    id=role.id,
                    name=role.name,
                    description=role.description,
                    permissions=permissions,
                )
            )

        return result

    @strawberry.field
    async def role(self, info, role_id: int) -> Role:
        """Получение роли по ID (только для администраторов)"""
        from auth.models.role import RoleModel
        from auth.services.permission_service import PermissionService
        from core.database import get_db

        current_user = await get_required_user(info)
        db = next(get_db())

        # Проверяем права доступа
        if not PermissionService.check_permission(db, current_user["id"], "role", "read"):
            raise Exception("Insufficient permissions")

        role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
        if not role:
            raise Exception("Role not found")

        permissions = [
            Permission(
                id=perm.id,
                role_id=perm.role_id,
                resource=perm.resource,
                action=perm.action,
                scope=perm.scope,
            )
            for perm in role.permissions
        ]

        return Role(
            id=role.id, name=role.name, description=role.description, permissions=permissions
        )

    @strawberry.field
    async def my_roles(self, info) -> List[Role]:
        """Получение ролей текущего пользователя"""
        from auth.models.user import UserModel
        from core.database import get_db

        current_user = await get_required_user(info)
        db = next(get_db())

        user = db.query(UserModel).filter(UserModel.id == current_user["id"]).first()
        if not user:
            raise Exception("User not found")

        result = []
        for role in user.roles:
            permissions = [
                Permission(
                    id=perm.id,
                    role_id=perm.role_id,
                    resource=perm.resource,
                    action=perm.action,
                    scope=perm.scope,
                )
                for perm in role.permissions
            ]
            result.append(
                Role(
                    id=role.id,
                    name=role.name,
                    description=role.description,
                    permissions=permissions,
                )
            )

        return result


@strawberry.type
class RoleMutation:
    @strawberry.mutation
    async def create_role(self, info, input: RoleInput) -> Role:
        """Создание новой роли (только для администраторов)"""
        from auth.models.role import RoleModel
        from auth.services.permission_service import PermissionService
        from core.database import get_db

        current_user = await get_required_user(info)
        db = next(get_db())

        # Проверяем права доступа
        if not PermissionService.check_permission(db, current_user["id"], "role", "create"):
            raise Exception("Insufficient permissions")

        # Проверяем, нет ли уже роли с таким именем
        existing_role = db.query(RoleModel).filter(RoleModel.name == input.name).first()
        if existing_role:
            raise Exception("Role with this name already exists")

        role = RoleModel(name=input.name, description=input.description)
        db.add(role)
        db.commit()
        db.refresh(role)

        return Role(id=role.id, name=role.name, description=role.description, permissions=[])

    @strawberry.mutation
    async def update_role(self, info, role_id: int, input: RoleUpdateInput) -> Role:
        """Обновление роли (только для администраторов)"""
        from auth.models.role import RoleModel
        from auth.services.permission_service import PermissionService
        from core.database import get_db

        current_user = await get_required_user(info)
        db = next(get_db())

        # Проверяем права доступа
        if not PermissionService.check_permission(db, current_user["id"], "role", "update"):
            raise Exception("Insufficient permissions")

        role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
        if not role:
            raise Exception("Role not found")

        # Обновляем поля
        if input.name is not None:
            # Проверяем, нет ли другой роли с таким именем
            existing_role = (
                db.query(RoleModel)
                .filter(RoleModel.name == input.name, RoleModel.id != role_id)
                .first()
            )
            if existing_role:
                raise Exception("Another role with this name already exists")
            role.name = input.name

        if input.description is not None:
            role.description = input.description

        db.commit()
        db.refresh(role)

        permissions = [
            Permission(
                id=perm.id,
                role_id=perm.role_id,
                resource=perm.resource,
                action=perm.action,
                scope=perm.scope,
            )
            for perm in role.permissions
        ]

        return Role(
            id=role.id, name=role.name, description=role.description, permissions=permissions
        )

    @strawberry.mutation
    async def add_permission_to_role(self, info, role_id: int, input: PermissionInput) -> Role:
        """Добавление права к роли (только для администраторов)"""
        from auth.models.permission import PermissionModel
        from auth.models.role import RoleModel
        from auth.services.permission_service import PermissionService
        from core.database import get_db

        current_user = await get_required_user(info)
        db = next(get_db())

        # Проверяем права доступа
        if not PermissionService.check_permission(db, current_user["id"], "role", "update"):
            raise Exception("Insufficient permissions")

        role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
        if not role:
            raise Exception("Role not found")

        # Проверяем, нет ли уже такого права у роли
        existing_permission = (
            db.query(PermissionModel)
            .filter(
                PermissionModel.role_id == role_id,
                PermissionModel.resource == input.resource,
                PermissionModel.action == input.action,
            )
            .first()
        )

        if existing_permission:
            raise Exception("Permission already exists for this role")

        permission = PermissionModel(
            role_id=role_id, resource=input.resource, action=input.action, scope=input.scope
        )
        db.add(permission)
        db.commit()
        db.refresh(role)

        permissions = [
            Permission(
                id=perm.id,
                role_id=perm.role_id,
                resource=perm.resource,
                action=perm.action,
                scope=perm.scope,
            )
            for perm in role.permissions
        ]

        return Role(
            id=role.id, name=role.name, description=role.description, permissions=permissions
        )

    @strawberry.mutation
    async def assign_role_to_user(self, info, user_id: int, role_name: str) -> bool:
        """Назначение роли пользователю (только для администраторов)"""
        from auth.services.permission_service import PermissionService
        from auth.services.user_service import UserService
        from core.database import get_db

        current_user = await get_required_user(info)
        db = next(get_db())

        # Проверяем права доступа
        if not PermissionService.check_permission(db, current_user["id"], "user", "update"):
            raise Exception("Insufficient permissions")

        success = UserService.assign_role_to_user(db, user_id, role_name)
        if not success:
            raise Exception("Failed to assign role to user")

        return True

    @strawberry.mutation
    async def remove_role_from_user(self, info, user_id: int, role_name: str) -> bool:
        """Удаление роли у пользователя (только для администраторов)"""
        from auth.models.role import RoleModel
        from auth.models.user import UserModel
        from auth.services.permission_service import PermissionService
        from core.database import get_db

        current_user = await get_required_user(info)
        db = next(get_db())

        # Проверяем права доступа
        if not PermissionService.check_permission(db, current_user["id"], "user", "update"):
            raise Exception("Insufficient permissions")

        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        role = db.query(RoleModel).filter(RoleModel.name == role_name).first()

        if not user or not role:
            return False

        if role in user.roles:
            user.roles.remove(role)
            db.commit()

        return True
