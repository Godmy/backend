"""Convert user_roles_association and concept_tags from bare link tables to
full entities (surrogate id, created_at/updated_at, soft-delete for history)

Two many-to-many "join" tables previously had no identity of their own:
- user_roles_association: composite PK (user_id, role_id), no timestamps
- concept_tags: composite PK (concept_id, tag_id), no timestamps

Both now carry BaseModel + SoftDeleteMixin columns so that granting/revoking
a role or tag preserves history (created_at = when granted, deleted_at = when
revoked) instead of the row simply vanishing. Uniqueness of the natural key
is preserved via a partial unique index that only applies to active
(deleted_at IS NULL) rows, so the same pair can be re-granted after a revoke
without colliding with its own history.

Revision ID: 003
Revises: 002
Create Date: 2026-07-23 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # user_roles_association -> user_roles
    # ------------------------------------------------------------------
    op.rename_table("user_roles_association", "user_roles")

    # Drop the old composite PK, replace with a surrogate id.
    # SERIAL backfills existing rows via the sequence (Postgres evaluates
    # a volatile default like nextval() per-row on ADD COLUMN).
    op.execute("ALTER TABLE user_roles DROP CONSTRAINT user_roles_association_pkey")
    op.execute("ALTER TABLE user_roles ADD COLUMN id SERIAL")
    op.execute("ALTER TABLE user_roles ADD PRIMARY KEY (id)")

    op.add_column(
        "user_roles",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column(
        "user_roles",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column("user_roles", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_roles", sa.Column("deleted_by_id", sa.Integer(), nullable=True))

    op.create_index("ix_user_roles_created_at", "user_roles", ["created_at"])
    op.create_index("ix_user_roles_deleted_at", "user_roles", ["deleted_at"])
    op.create_foreign_key(
        "fk_user_roles_deleted_by_id_users", "user_roles", "users", ["deleted_by_id"], ["id"], ondelete="SET NULL"
    )

    # Original FKs had no ondelete; bring them in line with the rest of the codebase.
    op.execute("ALTER TABLE user_roles DROP CONSTRAINT user_roles_association_user_id_fkey")
    op.create_foreign_key("fk_user_roles_user_id_users", "user_roles", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.execute("ALTER TABLE user_roles DROP CONSTRAINT user_roles_association_role_id_fkey")
    op.create_foreign_key("fk_user_roles_role_id_roles", "user_roles", "roles", ["role_id"], ["id"], ondelete="CASCADE")

    # Replaces the old composite PK's uniqueness guarantee, scoped to active rows only.
    op.create_index(
        "uq_user_roles_active_user_role",
        "user_roles",
        ["user_id", "role_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ------------------------------------------------------------------
    # concept_tags: same shape change, name stays the same
    # ------------------------------------------------------------------
    op.execute("ALTER TABLE concept_tags DROP CONSTRAINT concept_tags_pkey")
    op.execute("ALTER TABLE concept_tags ADD COLUMN id SERIAL")
    op.execute("ALTER TABLE concept_tags ADD PRIMARY KEY (id)")

    op.add_column(
        "concept_tags",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column(
        "concept_tags",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column("concept_tags", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("concept_tags", sa.Column("deleted_by_id", sa.Integer(), nullable=True))

    op.create_index("ix_concept_tags_created_at", "concept_tags", ["created_at"])
    op.create_index("ix_concept_tags_deleted_at", "concept_tags", ["deleted_at"])
    op.create_foreign_key(
        "fk_concept_tags_deleted_by_id_users", "concept_tags", "users", ["deleted_by_id"], ["id"], ondelete="SET NULL"
    )

    op.create_index(
        "uq_concept_tags_active_concept_tag",
        "concept_tags",
        ["concept_id", "tag_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    # LOSSY: the old schema has no concept of history and enforces one row per
    # pair via a composite PK, so any revoked (soft-deleted) assignments are
    # discarded here rather than migrated back.
    op.execute("DELETE FROM concept_tags WHERE deleted_at IS NOT NULL")
    op.drop_index("uq_concept_tags_active_concept_tag", table_name="concept_tags")
    op.drop_constraint("fk_concept_tags_deleted_by_id_users", "concept_tags", type_="foreignkey")
    op.drop_index("ix_concept_tags_deleted_at", table_name="concept_tags")
    op.drop_index("ix_concept_tags_created_at", table_name="concept_tags")
    op.drop_column("concept_tags", "deleted_by_id")
    op.drop_column("concept_tags", "deleted_at")
    op.drop_column("concept_tags", "updated_at")
    op.drop_column("concept_tags", "created_at")
    op.execute("ALTER TABLE concept_tags DROP CONSTRAINT concept_tags_pkey")
    op.drop_column("concept_tags", "id")
    op.execute("ALTER TABLE concept_tags ADD PRIMARY KEY (concept_id, tag_id)")

    op.execute("DELETE FROM user_roles WHERE deleted_at IS NOT NULL")
    op.drop_index("uq_user_roles_active_user_role", table_name="user_roles")
    op.execute("ALTER TABLE user_roles DROP CONSTRAINT fk_user_roles_role_id_roles")
    op.create_foreign_key(None, "user_roles", "roles", ["role_id"], ["id"])
    op.execute("ALTER TABLE user_roles DROP CONSTRAINT fk_user_roles_user_id_users")
    op.create_foreign_key(None, "user_roles", "users", ["user_id"], ["id"])
    op.drop_constraint("fk_user_roles_deleted_by_id_users", "user_roles", type_="foreignkey")
    op.drop_index("ix_user_roles_deleted_at", table_name="user_roles")
    op.drop_index("ix_user_roles_created_at", table_name="user_roles")
    op.drop_column("user_roles", "deleted_by_id")
    op.drop_column("user_roles", "deleted_at")
    op.drop_column("user_roles", "updated_at")
    op.drop_column("user_roles", "created_at")
    op.execute("ALTER TABLE user_roles DROP CONSTRAINT user_roles_pkey")
    op.drop_column("user_roles", "id")
    op.execute("ALTER TABLE user_roles ADD PRIMARY KEY (user_id, role_id)")

    op.rename_table("user_roles", "user_roles_association")
