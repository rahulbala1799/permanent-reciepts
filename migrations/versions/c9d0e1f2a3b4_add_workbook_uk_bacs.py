"""Add workbook_uk_bacs flag to master cashbook

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-06-01 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c9d0e1f2a3b4'
down_revision = 'b8c9d0e1f2a3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('master_cashbook_transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('workbook_uk_bacs', sa.Boolean(), nullable=True, server_default=sa.false()))
        batch_op.create_index('ix_master_cashbook_transactions_workbook_uk_bacs', ['workbook_uk_bacs'])


def downgrade():
    with op.batch_alter_table('master_cashbook_transactions', schema=None) as batch_op:
        batch_op.drop_index('ix_master_cashbook_transactions_workbook_uk_bacs')
        batch_op.drop_column('workbook_uk_bacs')
