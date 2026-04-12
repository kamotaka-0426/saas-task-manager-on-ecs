"""phase2_comments_labels_assignees

Revision ID: 248d20c38f30
Revises: a190cfad440c
Create Date: 2026-04-10

Adds: comments, activity_logs, labels, issue_labels, issue_assignees
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "248d20c38f30"
down_revision: Union[str, Sequence[str], None] = "a190cfad440c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- comments ---
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "issue_id",
            sa.Integer(),
            sa.ForeignKey("issues.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("content", sa.Text(), nullable=False),
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
    op.create_index("ix_comments_id", "comments", ["id"])
    op.create_index("ix_comments_issue_id", "comments", ["issue_id"])

    # --- activity_logs ---
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "issue_id",
            sa.Integer(),
            sa.ForeignKey("issues.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("field", sa.String(), nullable=True),
        sa.Column("old_value", sa.String(), nullable=True),
        sa.Column("new_value", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_activity_logs_id", "activity_logs", ["id"])
    op.create_index("ix_activity_logs_issue_id", "activity_logs", ["issue_id"])

    # --- labels ---
    op.create_table(
        "labels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("color", sa.String(), nullable=False, server_default="#6366f1"),
        sa.UniqueConstraint("org_id", "name", name="uq_label_org_name"),
    )
    op.create_index("ix_labels_id", "labels", ["id"])

    # --- issue_labels (association) ---
    op.create_table(
        "issue_labels",
        sa.Column(
            "issue_id",
            sa.Integer(),
            sa.ForeignKey("issues.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "label_id",
            sa.Integer(),
            sa.ForeignKey("labels.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # --- issue_assignees (association) ---
    op.create_table(
        "issue_assignees",
        sa.Column(
            "issue_id",
            sa.Integer(),
            sa.ForeignKey("issues.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("issue_assignees")
    op.drop_table("issue_labels")
    op.drop_table("labels")
    op.drop_table("activity_logs")
    op.drop_table("comments")
