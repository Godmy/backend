"""
Сидер для инициализации ролей и прав доступа
Второй этап - зависит только от БД, не зависит от языков
"""

import logging

from auth.models import PermissionModel, RoleModel
from scripts.seeders.base import BaseSeeder, SeederMetadata, registry

logger = logging.getLogger(__name__)


@registry.register("roles")
class RolesSeeder(BaseSeeder):
    """Инициализация ролей и прав доступа"""

    @property
    def metadata(self) -> SeederMetadata:
        return SeederMetadata(
            name="roles",
            version="1.0.0",
            description="Инициализация системы ролей и прав доступа (5 ролей)",
            dependencies=[],  # Не зависит от языков
        )

    def should_run(self) -> bool:
        """Проверить, есть ли уже роли"""
        return self.db.query(RoleModel).first() is None

    def seed(self) -> None:
        """Создать роли и права доступа"""

        # Создаем роли
        roles_data = [
            {
                "name": "guest",
                "description": "Guest user - read-only access to public content",
            },
            {
                "name": "user",
                "description": "Regular user - can view and create own content",
            },
            {
                "name": "editor",
                "description": "Editor - can manage content and translations",
            },
            {
                "name": "moderator",
                "description": "Moderator - can manage users and review content",
            },
            {
                "name": "admin",
                "description": "Administrator - full system access",
            },
        ]

        # Batch insert ролей
        created_roles = self.batch_insert(RoleModel, roles_data)
        self.db.flush()

        # Получаем созданные роли с ID
        roles = {r.name: r for r in self.db.query(RoleModel).all()}

        # Создаем права доступа
        permissions_data = []

        # Guest - только чтение
        permissions_data.extend(
            [
                {
                    "role_id": roles["guest"].id,
                    "resource": "concepts",
                    "action": "read",
                    "scope": "all",
                },
                {
                    "role_id": roles["guest"].id,
                    "resource": "dictionaries",
                    "action": "read",
                    "scope": "all",
                },
                {
                    "role_id": roles["guest"].id,
                    "resource": "languages",
                    "action": "read",
                    "scope": "all",
                },
            ]
        )

        # User - чтение + создание своего контента
        permissions_data.extend(
            [
                {
                    "role_id": roles["user"].id,
                    "resource": "concepts",
                    "action": "read",
                    "scope": "all",
                },
                {
                    "role_id": roles["user"].id,
                    "resource": "concepts",
                    "action": "create",
                    "scope": "own",
                },
                {
                    "role_id": roles["user"].id,
                    "resource": "dictionaries",
                    "action": "read",
                    "scope": "all",
                },
                {
                    "role_id": roles["user"].id,
                    "resource": "dictionaries",
                    "action": "create",
                    "scope": "own",
                },
                {
                    "role_id": roles["user"].id,
                    "resource": "languages",
                    "action": "read",
                    "scope": "all",
                },
            ]
        )

        # Editor - управление всем контентом
        permissions_data.extend(
            [
                {
                    "role_id": roles["editor"].id,
                    "resource": "concepts",
                    "action": "read",
                    "scope": "all",
                },
                {
                    "role_id": roles["editor"].id,
                    "resource": "concepts",
                    "action": "create",
                    "scope": "all",
                },
                {
                    "role_id": roles["editor"].id,
                    "resource": "concepts",
                    "action": "update",
                    "scope": "all",
                },
                {
                    "role_id": roles["editor"].id,
                    "resource": "concepts",
                    "action": "delete",
                    "scope": "all",
                },
                {
                    "role_id": roles["editor"].id,
                    "resource": "dictionaries",
                    "action": "read",
                    "scope": "all",
                },
                {
                    "role_id": roles["editor"].id,
                    "resource": "dictionaries",
                    "action": "create",
                    "scope": "all",
                },
                {
                    "role_id": roles["editor"].id,
                    "resource": "dictionaries",
                    "action": "update",
                    "scope": "all",
                },
                {
                    "role_id": roles["editor"].id,
                    "resource": "dictionaries",
                    "action": "delete",
                    "scope": "all",
                },
                {
                    "role_id": roles["editor"].id,
                    "resource": "languages",
                    "action": "read",
                    "scope": "all",
                },
                {
                    "role_id": roles["editor"].id,
                    "resource": "languages",
                    "action": "create",
                    "scope": "all",
                },
                {
                    "role_id": roles["editor"].id,
                    "resource": "languages",
                    "action": "update",
                    "scope": "all",
                },
            ]
        )

        # Moderator - + управление пользователями
        permissions_data.extend(
            [
                {
                    "role_id": roles["moderator"].id,
                    "resource": "users",
                    "action": "read",
                    "scope": "all",
                },
                {
                    "role_id": roles["moderator"].id,
                    "resource": "users",
                    "action": "update",
                    "scope": "all",
                },
                {
                    "role_id": roles["moderator"].id,
                    "resource": "users",
                    "action": "delete",
                    "scope": "all",
                },
            ]
        )

        # Admin - полный доступ
        permissions_data.append(
            {"role_id": roles["admin"].id, "resource": "*", "action": "*", "scope": "all"}
        )

        # Batch insert прав доступа
        created_permissions = self.batch_insert(PermissionModel, permissions_data)

        self.db.commit()
        self.metadata.records_created = created_roles + created_permissions

        self.logger.info(f"Added {created_roles} roles")
        self.logger.info(f"Added {created_permissions} permissions")
