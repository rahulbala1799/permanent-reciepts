"""Add client region mapping tables

Revision ID: f1a2b3c4d5e6
Revises: 8ccecb1a40d0
Create Date: 2026-06-01 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'f1a2b3c4d5e6'
down_revision = '8ccecb1a40d0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'client_region_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(length=50), nullable=False),
        sa.Column('subsidiary_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('match_count', sa.Integer(), nullable=False),
        sa.Column('billing_entity', sa.String(length=500), nullable=True),
        sa.Column('match_types_json', sa.Text(), nullable=True),
        sa.Column('total_stripe_amount', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id', 'subsidiary_id', 'job_id', name='uq_client_region_history'),
    )
    op.create_index('ix_client_region_history_client_id', 'client_region_history', ['client_id'])

    op.create_table(
        'client_region_profiles',
        sa.Column('client_id', sa.String(length=50), nullable=False),
        sa.Column('primary_subsidiary_id', sa.Integer(), nullable=True),
        sa.Column('is_multi_region', sa.Boolean(), nullable=True),
        sa.Column('regions_json', sa.Text(), nullable=True),
        sa.Column('region_counts_json', sa.Text(), nullable=True),
        sa.Column('last_subsidiary_id', sa.Integer(), nullable=True),
        sa.Column('last_job_id', sa.Integer(), nullable=True),
        sa.Column('last_billing_entity', sa.String(length=500), nullable=True),
        sa.Column('total_matches', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('client_id'),
    )


def downgrade():
    op.drop_index('ix_client_region_history_client_id', table_name='client_region_history')
    op.drop_table('client_region_history')
    op.drop_table('client_region_profiles')
