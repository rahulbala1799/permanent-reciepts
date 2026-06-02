"""Add master_cashbook_transactions table

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
Create Date: 2026-06-01 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a7b8c9d0e1f2'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'master_cashbook_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('payment_date', sa.String(length=20), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=True),
        sa.Column('invoice_number', sa.String(length=255), nullable=True),
        sa.Column('billing_entity', sa.String(length=500), nullable=True),
        sa.Column('ar_account', sa.String(length=500), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('exchange_rate', sa.Float(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('account', sa.String(length=500), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('transtype', sa.String(length=100), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('card_reference', sa.Float(), nullable=True),
        sa.Column('reasoncode', sa.Float(), nullable=True),
        sa.Column('sepaprovider', sa.String(length=255), nullable=True),
        sa.Column('invoice_hash', sa.String(length=255), nullable=True),
        sa.Column('payment_hash', sa.String(length=255), nullable=True),
        sa.Column('memo', sa.Float(), nullable=True),
        sa.Column('assigned_subsidiary_id', sa.Integer(), nullable=True),
        sa.Column('assignment_source', sa.String(length=50), nullable=True),
        sa.Column('assignment_detail', sa.String(length=500), nullable=True),
        sa.Column('original_account', sa.String(length=500), nullable=True),
        sa.Column('original_billing_entity', sa.String(length=500), nullable=True),
        sa.Column('fields_corrected', sa.Boolean(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_master_cashbook_transactions_job_id', 'master_cashbook_transactions', ['job_id'])


def downgrade():
    op.drop_index('ix_master_cashbook_transactions_job_id', table_name='master_cashbook_transactions')
    op.drop_table('master_cashbook_transactions')
