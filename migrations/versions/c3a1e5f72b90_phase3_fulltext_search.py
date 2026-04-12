"""phase3_fulltext_search

Revision ID: c3a1e5f72b90
Revises: 248d20c38f30
Create Date: 2026-04-11

Adds search_vector (tsvector) column + GIN index + auto-update trigger
to the issues table for PostgreSQL full-text search.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c3a1e5f72b90"
down_revision: Union[str, Sequence[str], None] = "248d20c38f30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add tsvector column
    op.execute(sa.text(
        "ALTER TABLE issues ADD COLUMN IF NOT EXISTS search_vector tsvector"
    ))

    # 2. Backfill existing rows
    op.execute(sa.text(
        "UPDATE issues "
        "SET search_vector = to_tsvector('english', title || ' ' || coalesce(description, ''))"
    ))

    # 3. GIN index for fast full-text lookups
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_issues_search_vector "
        "ON issues USING gin(search_vector)"
    ))

    # 4. Trigger function – keeps search_vector in sync on insert / update
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION issues_search_vector_update()
        RETURNS trigger AS $$
        BEGIN
          NEW.search_vector :=
            to_tsvector('english',
              NEW.title || ' ' || coalesce(NEW.description, ''));
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """))

    # 5. Attach trigger
    op.execute(sa.text(
        "DROP TRIGGER IF EXISTS issues_search_vector_trigger ON issues"
    ))
    op.execute(sa.text("""
        CREATE TRIGGER issues_search_vector_trigger
        BEFORE INSERT OR UPDATE ON issues
        FOR EACH ROW EXECUTE FUNCTION issues_search_vector_update()
    """))


def downgrade() -> None:
    op.execute(sa.text(
        "DROP TRIGGER IF EXISTS issues_search_vector_trigger ON issues"
    ))
    op.execute(sa.text(
        "DROP FUNCTION IF EXISTS issues_search_vector_update()"
    ))
    op.execute(sa.text(
        "DROP INDEX IF EXISTS ix_issues_search_vector"
    ))
    op.execute(sa.text(
        "ALTER TABLE issues DROP COLUMN IF EXISTS search_vector"
    ))
