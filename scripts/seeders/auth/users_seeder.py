"""
Сидер для создания тестовых пользователей
Зависит от ролей
"""

import logging

from auth.models import RoleModel, UserModel, UserRoleModel
from auth.models.profile import UserProfileModel
from auth.utils.security import hash_password
from scripts.seeders.base import BaseSeeder, SeederMetadata, registry

logger = logging.getLogger(__name__)


@registry.register("users")
class UsersSeeder(BaseSeeder):
    """Создание тестовых пользователей"""

    @property
    def metadata(self) -> SeederMetadata:
        return SeederMetadata(
            name="users",
            version="1.0.0",
            description="Создание тестовых пользователей (5 пользователей)",
            dependencies=["roles"],  # Зависит от ролей
        )

    def should_run(self) -> bool:
        """Проверить, есть ли уже пользователи"""
        return self.db.query(UserModel).first() is None

    def seed(self) -> None:
        """Создать тестовых пользователей"""

        # Получаем роли
        roles = {r.name: r for r in self.db.query(RoleModel).all()}

        users_data = [
            {
                "username": "admin",
                "email": "admin@multipult.dev",
                "password": "Admin123!",
                "is_active": True,
                "is_verified": True,
                "role": "admin",
                "profile": {
                    "first_name": "Администратор",
                    "last_name": "Системы",
                    "bio": "Главный администратор системы МультиПУЛЬТ",
                },
            },
            {
                "username": "moderator",
                "email": "moderator@multipult.dev",
                "password": "Moderator123!",
                "is_active": True,
                "is_verified": True,
                "role": "moderator",
                "profile": {
                    "first_name": "Модератор",
                    "last_name": "Контента",
                    "bio": "Модератор и проверяющий контент",
                },
            },
            {
                "username": "editor",
                "email": "editor@multipult.dev",
                "password": "Editor123!",
                "is_active": True,
                "is_verified": True,
                "role": "editor",
                "profile": {
                    "first_name": "Редактор",
                    "last_name": "Словарей",
                    "bio": "Редактор переводов и концепций",
                },
            },
            {
                "username": "testuser",
                "email": "user@multipult.dev",
                "password": "User123!",
                "is_active": True,
                "is_verified": True,
                "role": "user",
                "profile": {
                    "first_name": "Тестовый",
                    "last_name": "Пользователь",
                    "bio": "Обычный пользователь системы",
                },
            },
            {
                "username": "john_doe",
                "email": "john.doe@example.com",
                "password": "John123!",
                "is_active": True,
                "is_verified": False,
                "role": "user",
                "profile": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "bio": "Learning multiple languages",
                },
            },
        ]

        users_created = 0
        profiles_created = 0
        user_roles_created = 0

        for user_data in users_data:
            # Создаем пользователя
            user = UserModel(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                is_active=user_data["is_active"],
                is_verified=user_data["is_verified"],
            )
            self.db.add(user)
            self.db.flush()
            users_created += 1

            # Создаем профиль
            profile = UserProfileModel(
                user_id=user.id,
                first_name=user_data["profile"]["first_name"],
                last_name=user_data["profile"]["last_name"],
                bio=user_data["profile"]["bio"],
            )
            self.db.add(profile)
            profiles_created += 1

            # Назначаем роль
            role = roles[user_data["role"]]
            user_role = UserRoleModel(user_id=user.id, role_id=role.id)
            self.db.add(user_role)
            user_roles_created += 1

        self.db.commit()
        self.metadata.records_created = users_created + profiles_created + user_roles_created

        self.logger.info(f"Added {users_created} users with profiles")
        self.logger.info("Login credentials:")
        for user_data in users_data:
            self.logger.info(
                f"  {user_data['username']} / {user_data['password']} ({user_data['role']})"
            )
