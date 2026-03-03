"""Add model_version to audit_events table

Revision ID: 002_add_model_version
Revises: 001_initial
Create Date: 2024-03-03 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op  # type: ignore[attr-defined]
import sqlalchemy as sa  # type: ignore[import-not-found]


# revision identifiers, used by Alembic.
revision: str = "002_add_model_version"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "audit_events",
        sa.Column("model_version", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("audit_events", "model_version")
