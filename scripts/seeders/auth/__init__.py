"""Сидеры для аутентификации и пользователей"""

from scripts.seeders.auth.roles_seeder import RolesSeeder
from scripts.seeders.auth.users_seeder import UsersSeeder

__all__ = ["RolesSeeder", "UsersSeeder"]
