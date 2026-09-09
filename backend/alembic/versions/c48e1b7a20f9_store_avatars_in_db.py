"""store avatar bytes in the database

Avatars were written to uploads/avatars and served by a StaticFiles mount. The
free hosting tiers restart containers on idle and deploy, which wipes that
directory while users.avatar_url still points into it — every restart produced
broken images. The bytes now live beside the row that references them.

Revision ID: c48e1b7a20f9
Revises: b7f3c2d91a04
Create Date: 2026-09-09
"""
from alembic import op
import sqlalchemy as sa

revision = "c48e1b7a20f9"
down_revision = "b7f3c2d91a04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_data", sa.LargeBinary(), nullable=True))
    op.add_column("users", sa.Column("avatar_mime", sa.String(), nullable=True))
    # Existing avatar_url values point at files this deployment can no longer
    # serve. Clearing them shows the initials placeholder instead of a broken
    # image; the user can re-upload.
    op.execute("UPDATE users SET avatar_url = NULL WHERE avatar_url IS NOT NULL")


def downgrade() -> None:
    op.drop_column("users", "avatar_mime")
    op.drop_column("users", "avatar_data")
