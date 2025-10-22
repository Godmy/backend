"""
Tests for Admin Panel features.

Tests User Story #8 - Admin Panel Features (P1)
"""

import pytest
from starlette.testclient import TestClient


class TestAdminService:
    """Test AdminService methods."""

    def test_ban_user(self, db_session, admin_user, test_user):
        """Test banning a user."""
        from auth.services.admin_service import AdminService

        # Ban user
        result = AdminService.ban_user(db_session, test_user.id, admin_user, "Test ban")

        assert result.id == test_user.id
        assert result.is_active is False

    def test_ban_user_already_banned(self, db_session, admin_user, test_user):
        """Test banning an already banned user."""
        from auth.services.admin_service import AdminService

        # Ban user first
        AdminService.ban_user(db_session, test_user.id, admin_user)

        # Try to ban again
        with pytest.raises(ValueError, match="already banned"):
            AdminService.ban_user(db_session, test_user.id, admin_user)

    def test_cannot_ban_yourself(self, db_session, admin_user):
        """Test that admin cannot ban themselves."""
        from auth.services.admin_service import AdminService

        with pytest.raises(ValueError, match="Cannot ban yourself"):
            AdminService.ban_user(db_session, admin_user.id, admin_user)

    def test_unban_user(self, db_session, admin_user, test_user):
        """Test unbanning a user."""
        from auth.services.admin_service import AdminService

        # Ban first
        AdminService.ban_user(db_session, test_user.id, admin_user)

        # Then unban
        result = AdminService.unban_user(db_session, test_user.id, admin_user)

        assert result.id == test_user.id
        assert result.is_active is True

    def test_get_all_users(self, db_session):
        """Test getting all users."""
        from auth.services.admin_service import AdminService

        users, total = AdminService.get_all_users(db_session, limit=10)

        assert len(users) > 0
        assert total > 0

    def test_get_all_users_with_filters(self, db_session, test_user):
        """Test getting users with filters."""
        from auth.services.admin_service import AdminService

        # Filter by active users
        users, total = AdminService.get_all_users(db_session, is_active=True)

        assert all(u.is_active for u in users)

    def test_get_all_users_search(self, db_session, test_user):
        """Test searching users."""
        from auth.services.admin_service import AdminService

        users, total = AdminService.get_all_users(db_session, search=test_user.username[:3])

        assert any(test_user.username in u.username for u in users)

    def test_get_system_stats(self, db_session):
        """Test getting system statistics."""
        from auth.services.admin_service import AdminService

        stats = AdminService.get_system_stats(db_session)

        assert "users" in stats
        assert "content" in stats
        assert "files" in stats
        assert "audit" in stats
        assert "roles" in stats

        assert stats["users"]["total"] > 0
        assert stats["users"]["active"] >= 0

    def test_bulk_assign_role(self, db_session, admin_user, test_user):
        """Test bulk role assignment."""
        from auth.services.admin_service import AdminService

        count = AdminService.bulk_assign_role(
            db_session,
            [test_user.id],
            "editor",
            admin_user
        )

        assert count == 1

    def test_bulk_remove_role(self, db_session, admin_user, test_user):
        """Test bulk role removal."""
        from auth.services.admin_service import AdminService

        # Assign first
        AdminService.bulk_assign_role(db_session, [test_user.id], "editor", admin_user)

        # Then remove
        count = AdminService.bulk_remove_role(db_session, [test_user.id], "editor", admin_user)

        assert count == 1


class TestAdminGraphQL:
    """Test Admin GraphQL API."""

    def test_all_users_query_unauthorized(self, client: TestClient):
        """Test that allUsers requires authentication."""
        query = """
        query {
          allUsers {
            users { id username }
            total
          }
        }
        """

        response = client.post("/graphql", json={"query": query})

        # Should fail without auth
        assert response.status_code == 200
        data = response.json()
        assert "errors" in data

    def test_all_users_query(self, client: TestClient, admin_token):
        """Test allUsers query with admin."""
        query = """
        query {
          allUsers(limit: 10) {
            users {
              id
              username
              email
              isActive
              roles
            }
            total
            hasMore
          }
        }
        """

        response = client.post(
            "/graphql",
            json={"query": query},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "allUsers" in data["data"]
        assert isinstance(data["data"]["allUsers"]["users"], list)
        assert data["data"]["allUsers"]["total"] > 0

    def test_system_stats_query(self, client: TestClient, admin_token):
        """Test systemStats query."""
        query = """
        query {
          systemStats {
            users { total active verified }
            content { concepts dictionaries languages }
            files { total totalSizeMb }
          }
        }
        """

        response = client.post(
            "/graphql",
            json={"query": query},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "systemStats" in data["data"]
        assert "users" in data["data"]["systemStats"]
        assert "content" in data["data"]["systemStats"]

    def test_ban_user_mutation(self, client: TestClient, admin_token, test_user):
        """Test banUser mutation."""
        mutation = f"""
        mutation {{
          banUser(userId: {test_user.id}, reason: "Test ban") {{
            id
            username
            isActive
          }}
        }}
        """

        response = client.post(
            "/graphql",
            json={"query": mutation},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["banUser"]["isActive"] is False

    def test_unban_user_mutation(self, client: TestClient, admin_token, test_user, db_session, admin_user):
        """Test unbanUser mutation."""
        from auth.services.admin_service import AdminService

        # Ban first
        AdminService.ban_user(db_session, test_user.id, admin_user)

        mutation = f"""
        mutation {{
          unbanUser(userId: {test_user.id}) {{
            id
            username
            isActive
          }}
        }}
        """

        response = client.post(
            "/graphql",
            json={"query": mutation},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["unbanUser"]["isActive"] is True

    def test_bulk_assign_role_mutation(self, client: TestClient, admin_token, test_user):
        """Test bulkAssignRole mutation."""
        mutation = f"""
        mutation {{
          bulkAssignRole(userIds: [{test_user.id}], roleName: "editor") {{
            success
            count
            message
          }}
        }}
        """

        response = client.post(
            "/graphql",
            json={"query": mutation},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["bulkAssignRole"]["success"] is True
        assert data["data"]["bulkAssignRole"]["count"] >= 0


@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing."""
    from auth.models.user import UserModel
    from auth.models.role import RoleModel, UserRoleModel
    from auth.utils.password import hash_password

    # Get admin role
    admin_role = db_session.query(RoleModel).filter(RoleModel.name == "admin").first()

    # Create admin user
    user = UserModel(
        username="test_admin",
        email="admin@test.com",
        password_hash=hash_password("Admin123!"),
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.flush()

    # Assign admin role
    user_role = UserRoleModel(user_id=user.id, role_id=admin_role.id)
    db_session.add(user_role)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def admin_token(client: TestClient, admin_user):
    """Get JWT token for admin user."""
    from auth.utils.jwt_handler import jwt_handler

    access_token = jwt_handler.create_access_token(data={"user_id": admin_user.id})
    return access_token
