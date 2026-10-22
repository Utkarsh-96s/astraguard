"""Notification core schema: channels, subscriptions, outbox, escalation, tokens, inbound events.

Revision ID: 002_notification_core
Revises: 001_initial
Create Date: 2026-10-22 14:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "002_notification_core"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # notification_channels
    op.create_table(
        "notification_channels",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), server_default="default_operator", nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), server_default="Default Channel", nullable=False),
        sa.Column("encrypted_address", sa.Text(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="NOT CONFIGURED", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("prefs", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notification_channels_user_id", "notification_channels", ["user_id"])
    op.create_index("ix_notification_channels_type", "notification_channels", ["type"])

    # subscriptions
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("channel_id", sa.String(length=64), sa.ForeignKey("notification_channels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("min_level", sa.String(length=32), server_default="WATCH", nullable=False),
        sa.Column("asset_filter", sa.String(length=64), nullable=True),
        sa.Column("quiet_hours", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_subscriptions_channel_id", "subscriptions", ["channel_id"])

    # notification_outbox
    op.create_table(
        "notification_outbox",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("alert_id", sa.String(length=64), sa.ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel_id", sa.String(length=64), sa.ForeignKey("notification_channels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("escalation_level", sa.Integer(), server_default="1", nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="queued", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("provider_message_id", sa.String(length=128), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("test", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notification_outbox_alert_id", "notification_outbox", ["alert_id"])
    op.create_index("ix_notification_outbox_channel_id", "notification_outbox", ["channel_id"])
    op.create_index("ix_notification_outbox_idempotency_key", "notification_outbox", ["idempotency_key"], unique=True)
    op.create_index("ix_notification_outbox_status", "notification_outbox", ["status"])
    op.create_index("ix_notification_outbox_next_attempt_at", "notification_outbox", ["next_attempt_at"])

    # escalation_policies
    op.create_table(
        "escalation_policies",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("l1_channels", sa.JSON(), nullable=False),
        sa.Column("l2_delay_sec", sa.Integer(), server_default="300", nullable=False),
        sa.Column("l2_channels", sa.JSON(), nullable=False),
        sa.Column("l3_delay_sec", sa.Integer(), server_default="900", nullable=False),
        sa.Column("l3_channels", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # escalation_state
    op.create_table(
        "escalation_state",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("alert_id", sa.String(length=64), sa.ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("policy_id", sa.String(length=64), sa.ForeignKey("escalation_policies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("current_level", sa.Integer(), server_default="1", nullable=False),
        sa.Column("next_escalation_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("halted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("halted_reason", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_escalation_state_alert_id", "escalation_state", ["alert_id"])

    # link_tokens
    op.create_table(
        "link_tokens",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("token_type", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("channel_id", sa.String(length=64), nullable=True),
        sa.Column("alert_id", sa.String(length=64), nullable=True),
        sa.Column("action", sa.String(length=32), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_link_tokens_token_hash", "link_tokens", ["token_hash"], unique=True)

    # inbound_events
    op.create_table(
        "inbound_events",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("channel_type", sa.String(length=32), nullable=False),
        sa.Column("raw_payload_redacted", sa.JSON(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_inbound_events_channel_type", "inbound_events", ["channel_type"])


def downgrade() -> None:
    op.drop_table("inbound_events")
    op.drop_table("link_tokens")
    op.drop_table("escalation_state")
    op.drop_table("escalation_policies")
    op.drop_table("notification_outbox")
    op.drop_table("subscriptions")
    op.drop_table("notification_channels")
