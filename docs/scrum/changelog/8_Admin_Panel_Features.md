### #8 - Admin Panel Features ✅

**User Story:**
Как администратор, я хочу управлять пользователями, ролями и контентом через GraphQL API.

**Acceptance Criteria:**
- [✅] Admin mutations: banUser, unbanUser, deleteUserPermanently
- [✅] Admin queries: allUsers (с фильтрами), systemStats
- [✅] Bulk operations: bulkAssignRole, bulkRemoveRole
- [✅] Audit log для всех admin действий
- [✅] Permission проверки для всех admin operations
- [✅] Pagination для больших списков (limit/offset, max 100)

**Estimated Effort:** 8 story points

**Status:** ✅ Done (2025-10-20)

**Implementation Details:**
- `auth/services/admin_service.py` - AdminService with 7 methods:
  - `ban_user()` / `unban_user()` - User ban management
  - `get_all_users()` - List users with filters (is_active, is_verified, role_name, search)
  - `get_system_stats()` - System statistics (users, content, files, audit, roles)
  - `delete_user_permanently()` - Hard delete (irreversible)
  - `bulk_assign_role()` / `bulk_remove_role()` - Bulk role operations
- `auth/schemas/admin.py` - GraphQL API:
  - Queries: `allUsers`, `systemStats`
  - Mutations: `banUser`, `unbanUser`, `deleteUserPermanently`, `bulkAssignRole`, `bulkRemoveRole`
- `core/schemas/schema.py` - Integrated AdminQuery and AdminMutation
- `tests/test_admin.py` - Full test coverage (service + GraphQL)
- All admin actions logged to audit trail
- Permission checks: admin:read, admin:update, admin:delete
- Safety: Cannot ban/delete yourself
- Pagination: limit/offset with max 100 results
- Filters: is_active, is_verified, role_name, search (username/email)
- System stats: users (total, active, verified, new 30d, banned), content, files, audit logs, role distribution

**Files Modified:**
- auth/services/admin_service.py (NEW, 334 lines)
- auth/schemas/admin.py (NEW, 589 lines)
- core/schemas/schema.py (UPDATED)
- tests/test_admin.py (NEW, 263 lines)
- CLAUDE.md (UPDATED)