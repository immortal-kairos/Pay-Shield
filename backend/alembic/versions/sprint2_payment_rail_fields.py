"""Sprint 2 Payment Rail Fields

Revision ID: sprint2_payment_rail
Revises: previous_revision_id
Create Date: 2026-05-07 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Vendor Table Updates
    op.add_column('vendors', sa.Column('bank_account_encrypted', sa.String(), nullable=True))
    
    # Payment Table Updates
    op.add_column('payments', sa.Column('provider_reference_id', sa.String(), nullable=True))
    op.add_column('payments', sa.Column('transfer_status', sa.String(), nullable=True))
    op.add_column('payments', sa.Column('transfer_initiated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('payments', sa.Column('transfer_completed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('payments', sa.Column('transfer_failure_reason', sa.Text(), nullable=True))

    # Add transfer_status constraint
    op.create_check_constraint(
        'check_transfer_status',
        'payments',
        sa.text("transfer_status IN ('INITIATED', 'SUCCESS', 'FAILED', 'PENDING')")
    )

def downgrade():
    op.drop_column('vendors', 'bank_account_encrypted')
    op.drop_column('payments', 'provider_reference_id')
    op.drop_column('payments', 'transfer_status')
    op.drop_column('payments', 'transfer_initiated_at')
    op.drop_column('payments', 'transfer_completed_at')
    op.drop_column('payments', 'transfer_failure_reason')