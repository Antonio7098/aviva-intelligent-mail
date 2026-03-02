"""Initial migration - create audit_events and read models tables

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create audit_events table (append-only)
    op.create_table(
        "audit_events",
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("correlation_id", sa.UUID(), nullable=False),
        sa.Column("email_hash", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("stage", sa.Text(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("actor", sa.Text(), nullable=True),
        sa.Column("model_name", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.Text(), nullable=True),
        sa.Column("ruleset_version", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "payload_json", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column("payload_hash", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("event_id"),
    )

    # Create indexes for audit_events
    op.create_index("ix_audit_events_email_hash", "audit_events", ["email_hash"])
    op.create_index(
        "ix_audit_events_correlation_id", "audit_events", ["correlation_id"]
    )
    op.create_index("ix_audit_events_timestamp", "audit_events", ["timestamp"])
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_status", "audit_events", ["status"])

    # GIN index on JSONB payload for efficient querying
    op.execute(
        "CREATE INDEX ix_audit_events_payload_json ON audit_events USING GIN (payload_json)"
    )

    # Create email_decisions table
    op.create_table(
        "email_decisions",
        sa.Column("email_hash", sa.Text(), nullable=False),
        sa.Column("classification", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("priority", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("model_name", sa.Text(), nullable=False),
        sa.Column("model_version", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("email_hash"),
    )

    op.create_index(
        "ix_email_decisions_classification", "email_decisions", ["classification"]
    )
    op.create_index("ix_email_decisions_priority", "email_decisions", ["priority"])
    op.create_index(
        "ix_email_decisions_processed_at", "email_decisions", ["processed_at"]
    )

    # Create required_actions table
    op.create_table(
        "required_actions",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("email_hash", sa.Text(), nullable=False),
        sa.Column("action_type", sa.Text(), nullable=False),
        sa.Column(
            "entity_refs", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column("risk_tags", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_required_actions_email_hash", "required_actions", ["email_hash"]
    )
    op.create_index(
        "ix_required_actions_action_type", "required_actions", ["action_type"]
    )
    op.create_index("ix_required_actions_deadline", "required_actions", ["deadline"])

    # Create digest_runs table
    op.create_table(
        "digest_runs",
        sa.Column("correlation_id", sa.UUID(), nullable=False),
        sa.Column("handler_id", sa.Text(), nullable=False),
        sa.Column("digest_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "summary_counts", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column(
            "priority_breakdown",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "top_priorities", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
        sa.Column(
            "actionable_emails", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
        sa.Column("model_version", sa.Text(), nullable=False),
        sa.Column("total_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("correlation_id"),
    )

    op.create_index("ix_digest_runs_handler_id", "digest_runs", ["handler_id"])
    op.create_index("ix_digest_runs_digest_date", "digest_runs", ["digest_date"])


def downgrade() -> None:
    op.drop_table("digest_runs")
    op.drop_table("required_actions")
    op.drop_table("email_decisions")
    op.drop_table("audit_events")
