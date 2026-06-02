"""Add master cashbook workbook link fields

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-06-01 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b8c9d0e1f2a3'
down_revision = 'a7b8c9d0e1f2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('cashbook_transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('master_cashbook_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_cashbook_transactions_master_cashbook_id', ['master_cashbook_id'])

    with op.batch_alter_table('master_cashbook_transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('workbook_region_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('workbook_updated_at', sa.DateTime(), nullable=True))
        batch_op.create_index('ix_master_cashbook_transactions_workbook_region_id', ['workbook_region_id'])


def downgrade():
    with op.batch_alter_table('master_cashbook_transactions', schema=None) as batch_op:
        batch_op.drop_index('ix_master_cashbook_transactions_workbook_region_id')
        batch_op.drop_column('workbook_updated_at')
        batch_op.drop_column('workbook_region_id')

    with op.batch_alter_table('cashbook_transactions', schema=None) as batch_op:
        batch_op.drop_index('ix_cashbook_transactions_master_cashbook_id')
        batch_op.drop_column('master_cashbook_id')
