"""drop resumes.file_path

The uploaded PDF is no longer written to disk: nothing read it back, no endpoint
served it, and the deployment targets have ephemeral filesystems, so the column
recorded a path to a file that would not survive a restart. parsed_text holds the
extracted content every feature actually uses.

Revision ID: b7f3c2d91a04
Revises: ca6116dbeba4
Create Date: 2026-09-09
"""
from alembic import op
import sqlalchemy as sa

revision = "b7f3c2d91a04"
down_revision = "ca6116dbeba4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("resumes", "file_path")


def downgrade() -> None:
    # Nullable on the way back: the original paths are gone, and the files they
    # pointed at are too, so there is no honest value to backfill.
    op.add_column("resumes", sa.Column("file_path", sa.String(), nullable=True))
