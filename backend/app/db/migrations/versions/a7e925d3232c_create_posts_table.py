"""create posts table

Revision ID: a7e925d3232c
Revises: 1344369e94e5
Create Date: 2023-01-24 12:03:00.857475

"""
from alembic import op
import sqlalchemy as sa

import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from common import timestamps




# revision identifiers, used by Alembic
revision = 'a7e925d3232c'
down_revision = '1344369e94e5'
branch_labels = None
depends_on = None




def upgrade() -> None:

    op.execute(sa.text("""CREATE SEQUENCE IF NOT EXISTS public.qso_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;"""))

    op.create_table(
        "qso",
        sa.Column("id", sa.BigInteger, primary_key=True, 
            server_default=sa.text("generate_id('qso_id_seq'::text)"),
            autoincrement=False),
        sa.Column("log_id", sa.BigInteger, sa.ForeignKey("qso_logs.id", ondelete="CASCADE")),  
        sa.Column("callsign", sa.Text, nullable=False, index=True),
        sa.Column("station_callsign", sa.Text, nullable=False, index=True),
        sa.Column("qso_datetime", sa.TIMESTAMP(timezone=True), index=True, nullable=False),
        sa.Column("band", sa.Text, nullable=False, index=True),
        sa.Column("freq", sa.Numeric(8, 2), nullable=False),
        sa.Column("qso_mode", sa.Text, nullable=False, index=True),
        sa.Column("rst_s", sa.SmallInteger, nullable=False, server_default=sa.text('599')),
        sa.Column("rst_r", sa.SmallInteger, nullable=False, server_default=sa.text('599')),
        sa.Column("name", sa.Text),
        sa.Column("qth", sa.Text),
        sa.Column("gridsquare", sa.Text),
        sa.Column("comment", sa.Text),
        sa.Column("extra", JSONB),
        *timestamps()
    )
    op.execute(
        """
        CREATE TRIGGER update_qso_modtime
            BEFORE UPDATE
            ON qso
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )

def downgrade() -> None:
    op.execute("""DROP SEQUENCE if exists public.qso_id_seq;""")
    op.execute("drop table if exists qso;")


