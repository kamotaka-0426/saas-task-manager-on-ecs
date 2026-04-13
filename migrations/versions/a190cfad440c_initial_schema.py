"""initial_schema

Revision ID: a190cfad440c
Revises:
Create Date: 2026-04-10

Creates all tables for the SaaS Task Manager MVP:
  users, organizations, organization_members, projects, issues
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a190cfad440c"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    result = op.get_bind().execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = :t"
        ),
        {"t": name},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    # --- PostgreSQL Enum types (idempotent via DO…EXCEPTION) ---
    op.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE roleenum AS ENUM ('owner', 'admin', 'member');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """))
    op.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE statusenum AS ENUM
                ('backlog', 'todo', 'in_progress', 'done', 'cancelled');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """))
    op.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE priorityenum AS ENUM
                ('none', 'low', 'medium', 'high', 'urgent');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """))

    # --- users ---
    if not _table_exists("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("hashed_password", sa.String(), nullable=False),
        )
        op.create_index("ix_users_id", "users", ["id"])
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    # --- organizations ---
    if not _table_exists("organizations"):
        op.create_table(
            "organizations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("slug", sa.String(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
            ),
        )
        op.create_index("ix_organizations_id", "organizations", ["id"])
        op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    # --- organization_members ---
    if not _table_exists("organization_members"):
        op.create_table(
            "organization_members",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "org_id",
                sa.Integer(),
                sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "role",
                sa.Enum("owner", "admin", "member", name="roleenum", create_type=False),
                nullable=False,
                server_default="member",
            ),
            sa.UniqueConstraint("org_id", "user_id", name="uq_org_member"),
        )
        op.create_index("ix_organization_members_id", "organization_members", ["id"])

    # --- projects ---
    if not _table_exists("projects"):
        op.create_table(
            "projects",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "org_id",
                sa.Integer(),
                sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
            ),
        )
        op.create_index("ix_projects_id", "projects", ["id"])

    # --- issues ---
    if not _table_exists("issues"):
        op.create_table(
            "issues",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "project_id",
                sa.Integer(),
                sa.ForeignKey("projects.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column(
                "status",
                sa.Enum(
                    "backlog", "todo", "in_progress", "done", "cancelled",
                    name="statusenum", create_type=False,
                ),
                nullable=False,
                server_default="backlog",
            ),
            sa.Column(
                "priority",
                sa.Enum(
                    "none", "low", "medium", "high", "urgent",
                    name="priorityenum", create_type=False,
                ),
                nullable=False,
                server_default="none",
            ),
            sa.Column(
                "created_by",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
            ),
        )
        op.create_index("ix_issues_id", "issues", ["id"])


def downgrade() -> None:
    op.drop_table("issues")
    op.drop_table("projects")
    op.drop_table("organization_members")
    op.drop_table("organizations")
    op.drop_table("users")

    sa.Enum(name="priorityenum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="statusenum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="roleenum").drop(op.get_bind(), checkfirst=True)
