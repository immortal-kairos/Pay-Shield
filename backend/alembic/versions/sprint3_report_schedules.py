"""Sprint 3 Report Schedules

Revision ID: sprint3_report_schedules
Revises: 
Create Date: 2026-05-10 11:40:43.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'sprint3_report_schedules'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'report_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('export_type', sa.String(), nullable=False),
        sa.Column('frequency', sa.String(), nullable=False),
        sa.Column('recipient_emails', sa.JSON(), nullable=False),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'))
    )

def downgrade():
    op.drop_table('report_schedules')
