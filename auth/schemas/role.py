'''"""
GraphQL schemas for role and permission management.
"""

from typing import List, Optional
import strawberry
from strawberry.types import Info

from auth.dependencies.auth import get_required_user
from auth.services.permission_service import PermissionService
from auth.models.user import UserModel
from auth.models.role import RoleModel, UserRoleModel
from auth.models.permission import PermissionModel

# ============================================================================
# Types
# ============================================================================

@strawberry.type(description="Represents a single permission.")
class Permission:
    id: int
    role_id: int
    resource: str = strawberry.field(description="The resource this permission applies to (e.g., 'concept', 'user').")
    action: str = strawberry.field(description="The action allowed on the resource (e.g., 'create', 'read', 'update', 'delete').")
    scope: str = strawberry.field(description="The scope of the action (e.g., 'own', 'all').")

@strawberry.type(description="Represents a user role and its associated permissions.")
class Role:
    id: int
    name: str = strawberry.field(description="The unique name of the role (e.g., 'admin', 'editor').")
    description: Optional[str]
    permissions: List[Permission]

# ============================================================================
# Inputs
# ============================================================================

@strawberry.input(description="Input for creating or adding a permission.")
class PermissionInput:
    resource: str = strawberry.field(description="The resource name.")
    action: str = strawberry.field(description="The action name.")
    scope: str = strawberry.field(default="own", description="The scope ('own' or 'all').")

@strawberry.input(description="Input for creating a new role.")
class RoleInput:
    name: str = strawberry.field(description="The name for the new role.")
    description: Optional[str] = strawberry.field(default=None, description="An optional description for the role.")

@strawberry.input(description="Input for updating an existing role.")
class RoleUpdateInput:
    name: Optional[str] = strawberry.field(default=None, description="The new name for the role.")
    description: Optional[str] = strawberry.field(default=None, description="The new description for the role.")

# ============================================================================
# Queries
# ============================================================================

@strawberry.type
class RoleQuery:
    @strawberry.field(description='''Get a list of all roles and their permissions.

**Required permissions:** `admin:read:roles`
''')
    async def roles(self, info: Info) -> List[Role]:
        current_user = await get_required_user(info)
        db = info.context["db"]
        user = db.query(UserModel).filter(UserModel.id == current_user["id"]).first()
        if not PermissionService.check_permission(user, "admin", "read", "roles"):
            raise Exception("Insufficient permissions")

        roles_db = db.query(RoleModel).all()
        return [self._map_role_to_gql(role) for role in roles_db]

    @strawberry.field(description='''Get a single role by its ID.

**Required permissions:** `admin:read:roles`
''')
    async def role(self, info: Info, role_id: int) -> Role:
        current_user = await get_required_user(info)
        db = info.context["db"]
        user = db.query(UserModel).filter(UserModel.id == current_user["id"]).first()
        if not PermissionService.check_permission(user, "admin", "read", "roles"):
            raise Exception("Insufficient permissions")

        role_db = db.query(RoleModel).filter(RoleModel.id == role_id).first()
        if not role_db: raise Exception("Role not found")
        return self._map_role_to_gql(role_db)

    @strawberry.field(description="Get the roles assigned to the current user.")
    async def my_roles(self, info: Info) -> List[Role]:
        current_user_dict = await get_required_user(info)
        db = info.context["db"]
        user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not user: raise Exception("User not found")
        return [self._map_role_to_gql(user_role.role) for user_role in user.roles]

    def _map_role_to_gql(self, role_db: RoleModel) -> Role:
        return Role(
            id=role_db.id, name=role_db.name, description=role_db.description,
            permissions=[Permission(id=p.id, role_id=p.role_id, resource=p.resource, action=p.action, scope=p.scope) for p in role_db.permissions]
        )

# ============================================================================
# Mutations
# ============================================================================

@strawberry.type
class RoleMutation:
    @strawberry.mutation(description='''Create a new role.

**Required permissions:** `admin:create:roles`
''')
    async def create_role(self, info: Info, input: RoleInput) -> Role:
        current_user = await get_required_user(info)
        db = info.context["db"]
        user = db.query(UserModel).filter(UserModel.id == current_user["id"]).first()
        if not PermissionService.check_permission(user, "admin", "create", "roles"):
            raise Exception("Insufficient permissions")

        if db.query(RoleModel).filter(RoleModel.name == input.name).first():
            raise Exception("Role with this name already exists")

        role = RoleModel(**input.__dict__)
        db.add(role)
        db.commit()
        db.refresh(role)
        return Role(id=role.id, name=role.name, description=role.description, permissions=[])

    @strawberry.mutation(description='''Update an existing role\'s name or description.

**Required permissions:** `admin:update:roles`
''')
    async def update_role(self, info: Info, role_id: int, input: RoleUpdateInput) -> Role:
        current_user = await get_required_user(info)
        db = info.context["db"]
        user = db.query(UserModel).filter(UserModel.id == current_user["id"]).first()
        if not PermissionService.check_permission(user, "admin", "update", "roles"):
            raise Exception("Insufficient permissions")

        role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
        if not role: raise Exception("Role not found")

        if input.name is not None:
            if db.query(RoleModel).filter(RoleModel.name == input.name, RoleModel.id != role_id).first():
                raise Exception("Another role with this name already exists")
            role.name = input.name
        if input.description is not None:
            role.description = input.description

        db.commit()
        db.refresh(role)
        return RoleQuery._map_role_to_gql(self, role)

    @strawberry.mutation(description='''Add a permission to a role.

**Required permissions:** `admin:update:roles`
''')
    async def add_permission_to_role(self, info: Info, role_id: int, input: PermissionInput) -> Role:
        current_user = await get_required_user(info)
        db = info.context["db"]
        user = db.query(UserModel).filter(UserModel.id == current_user["id"]).first()
        if not PermissionService.check_permission(user, "admin", "update", "roles"):
            raise Exception("Insufficient permissions")

        role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
        if not role: raise Exception("Role not found")

        if db.query(PermissionModel).filter_by(role_id=role_id, resource=input.resource, action=input.action).first():
            raise Exception("Permission already exists for this role")

        permission = PermissionModel(role_id=role_id, **input.__dict__)
        db.add(permission)
        db.commit()
        db.refresh(role)
        return RoleQuery._map_role_to_gql(self, role)

    @strawberry.mutation(description='''Assign a role to a user.

**Required permissions:** `admin:update:users`
''')
    async def assign_role_to_user(self, info: Info, user_id: int, role_name: str) -> bool:
        from auth.services.user_service import UserService
        current_user = await get_required_user(info)
        db = info.context["db"]
        user = db.query(UserModel).filter(UserModel.id == current_user["id"]).first()
        if not PermissionService.check_permission(user, "admin", "update", "users"):
            raise Exception("Insufficient permissions")

        if not UserService.assign_role_to_user(db, user_id, role_name):
            raise Exception("Failed to assign role to user. User or role may not exist.")
        return True

    @strawberry.mutation(description='''Remove a role from a user.

**Required permissions:** `admin:update:users`
''')
    async def remove_role_from_user(self, info: Info, user_id: int, role_name: str) -> bool:
        current_user = await get_required_user(info)
        db = info.context["db"]
        user = db.query(UserModel).filter(UserModel.id == current_user["id"]).first()
        if not PermissionService.check_permission(user, "admin", "update", "users"):
            raise Exception("Insufficient permissions")

        user_to_modify = db.query(UserModel).filter(UserModel.id == user_id).first()
        role_to_remove = db.query(RoleModel).filter(RoleModel.name == role_name).first()
        if not user_to_modify or not role_to_remove: return False

        user_role = db.query(UserRoleModel).filter(
            UserRoleModel.user_id == user_id, UserRoleModel.role_id == role_to_remove.id
        ).first()

        if user_role:
            db.delete(user_role)
            db.commit()
        return True
'''
