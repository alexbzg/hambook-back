"""create_qso_logs_tables

Revision ID: 3abd90b73232
Revises: 789b04bb955c
Create Date: 2022-11-25 13:43:25.923966

"""
from alembic import op
import sqlalchemy as sa

import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from common import timestamps




# revision identifiers, used by Alembic
revision = '3abd90b73232'
down_revision = '789b04bb955c'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute(sa.text("""CREATE SEQUENCE IF NOT EXISTS public.qso_log_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;"""))

    op.create_table(
        "qso_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, 
            server_default=sa.text("generate_id('qso_log_id_sec'::text)"),
            autoincrement=False),
        sa.Column("callsign", sa.Text, nullable=False),
        sa.Column("desc", sa.Text),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE")),
        *timestamps()
    )
    op.execute(
        """
        CREATE TRIGGER update_qso_logs_modtime
            BEFORE UPDATE
            ON qso_logs
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def downgrade() -> None:
    op.execute("""DROP SEQUENCE if exists public.qso_log_id_sec;""")
    op.execute("drop table if exists qso_logs;")


