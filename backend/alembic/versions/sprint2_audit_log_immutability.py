"""sprint2_audit_log_immutability

Revision ID: sprint2_01
Revises: 
Create Date: 2026-05-06

"""
from alembic import op

revision = 'sprint2_01'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("""
        CREATE OR REPLACE FUNCTION block_audit_log_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is immutable. UPDATE and DELETE are not permitted.';
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER audit_log_immutable
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION block_audit_log_mutation();
    """)

def downgrade():
    op.execute("DROP TRIGGER IF EXISTS audit_log_immutable ON audit_log;")
    op.execute("DROP FUNCTION IF EXISTS block_audit_log_mutation();")