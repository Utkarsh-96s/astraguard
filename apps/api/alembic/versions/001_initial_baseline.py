"""Initial baseline schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-10-19 05:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '001_initial'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # assets
    op.create_table(
        'assets',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('norad_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(length=64), server_default='satellite', nullable=False),
        sa.Column('tle_epoch', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # objects
    op.create_table(
        'objects',
        sa.Column('norad_id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('type', sa.String(length=32), server_default='debris', nullable=False),
        sa.Column('tle_line1', sa.String(length=80), nullable=False),
        sa.Column('tle_line2', sa.String(length=80), nullable=False),
        sa.Column('epoch', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # telemetry
    op.create_table(
        'telemetry',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('asset_id', sa.String(length=64), sa.ForeignKey('assets.id'), nullable=False),
        sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('channel', sa.String(length=64), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('quality', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('synthetic', sa.Boolean(), server_default='0', nullable=False),
    )
    op.create_index('ix_telemetry_asset_id', 'telemetry', ['asset_id'])
    op.create_index('ix_telemetry_ts', 'telemetry', ['ts'])
    op.create_index('ix_telemetry_channel', 'telemetry', ['channel'])
    op.create_index('ix_telemetry_asset_ts', 'telemetry', ['asset_id', 'ts'])

    # telemetry_windows
    op.create_table(
        'telemetry_windows',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('asset_id', sa.String(length=64), sa.ForeignKey('assets.id'), nullable=False),
        sa.Column('t_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('t_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('model_ver', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_telemetry_windows_asset_id', 'telemetry_windows', ['asset_id'])

    # conjunctions
    op.create_table(
        'conjunctions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('primary_id', sa.String(length=64), sa.ForeignKey('assets.id'), nullable=False),
        sa.Column('secondary_id', sa.Integer(), sa.ForeignKey('objects.norad_id'), nullable=False),
        sa.Column('tca', sa.DateTime(timezone=True), nullable=False),
        sa.Column('miss_km', sa.Float(), nullable=False),
        sa.Column('rel_vel_kms', sa.Float(), nullable=False),
        sa.Column('pc', sa.Float(), nullable=False),
        sa.Column('pc_method', sa.String(length=32), server_default='foster_2d_screening', nullable=False),
        sa.Column('risk_class', sa.String(length=32), server_default='LOW', nullable=False),
        sa.Column('synthetic', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_conjunctions_tca', 'conjunctions', ['tca'])

    # imagery_products
    op.create_table(
        'imagery_products',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('source', sa.String(length=64), server_default='Sentinel-2', nullable=False),
        sa.Column('bbox', sa.JSON(), nullable=False),
        sa.Column('acquired_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cloud_pct', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('uri', sa.String(length=512), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # disaster_events
    op.create_table(
        'disaster_events',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('product_id', sa.String(length=64), sa.ForeignKey('imagery_products.id'), nullable=True),
        sa.Column('type', sa.String(length=64), nullable=False),
        sa.Column('area_km2', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('mask_uri', sa.String(length=512), nullable=True),
        sa.Column('priority', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('confidence', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('synthetic', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # risk_snapshots
    op.create_table(
        'risk_snapshots',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('asset_id', sa.String(length=64), sa.ForeignKey('assets.id'), nullable=False),
        sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('r_h', sa.Float(), nullable=False),
        sa.Column('r_d', sa.Float(), nullable=False),
        sa.Column('r_e', sa.Float(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('level', sa.String(length=32), nullable=False),
        sa.Column('drivers', sa.JSON(), nullable=False),
        sa.Column('synthetic', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_risk_snapshots_asset_id', 'risk_snapshots', ['asset_id'])
    op.create_index('ix_risk_snapshots_ts', 'risk_snapshots', ['ts'])

    # alerts
    op.create_table(
        'alerts',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('snapshot_id', sa.String(length=64), sa.ForeignKey('risk_snapshots.id'), nullable=False),
        sa.Column('level', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('recommendation', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('dedup_key', sa.String(length=128), nullable=False),
        sa.Column('synthetic', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_alerts_dedup_key', 'alerts', ['dedup_key'])

    # operator_actions
    op.create_table(
        'operator_actions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('alert_id', sa.String(length=64), sa.ForeignKey('alerts.id'), nullable=False),
        sa.Column('user', sa.String(length=128), server_default='Operator', nullable=False),
        sa.Column('action', sa.String(length=32), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    )

    # model_registry
    op.create_table(
        'model_registry',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('version', sa.String(length=64), nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=False),
        sa.Column('trained_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('data_hash', sa.String(length=128), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('model_registry')
    op.drop_table('operator_actions')
    op.drop_table('alerts')
    op.drop_table('risk_snapshots')
    op.drop_table('disaster_events')
    op.drop_table('imagery_products')
    op.drop_table('conjunctions')
    op.drop_table('telemetry_windows')
    op.drop_table('telemetry')
    op.drop_table('objects')
    op.drop_table('assets')
