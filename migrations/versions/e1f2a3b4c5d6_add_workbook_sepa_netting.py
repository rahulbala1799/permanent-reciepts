"""Add workbook_sepa_netting flag to master cashbook

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-06-02 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e1f2a3b4c5d6'
down_revision = 'd0e1f2a3b4c5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('master_cashbook_transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('workbook_sepa_netting', sa.Boolean(), nullable=True, server_default=sa.false()))
        batch_op.create_index('ix_master_cashbook_transactions_workbook_sepa_netting', ['workbook_sepa_netting'])


def downgrade():
    with op.batch_alter_table('master_cashbook_transactions', schema=None) as batch_op:
        batch_op.drop_index('ix_master_cashbook_transactions_workbook_sepa_netting')
        batch_op.drop_column('workbook_sepa_netting')
