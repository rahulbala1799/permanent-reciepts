"""Add workbook_partner_transfer flag to master cashbook

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-06-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd0e1f2a3b4c5'
down_revision = 'c9d0e1f2a3b4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('master_cashbook_transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('workbook_partner_transfer', sa.Boolean(), nullable=True, server_default=sa.false()))
        batch_op.create_index('ix_master_cashbook_transactions_workbook_partner_transfer', ['workbook_partner_transfer'])


def downgrade():
    with op.batch_alter_table('master_cashbook_transactions', schema=None) as batch_op:
        batch_op.drop_index('ix_master_cashbook_transactions_workbook_partner_transfer')
        batch_op.drop_column('workbook_partner_transfer')
