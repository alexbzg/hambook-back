"""create_qso_table

Revision ID: 1344369e94e5
Revises: 3abd90b73232
Create Date: 2022-12-01 10:43:56.336743

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import JSONB

import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from common import timestamps




# revision identifiers, used by Alembic
revision = '1344369e94e5'
down_revision = '3abd90b73232'
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

    op.execute(sa.text(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS
        $BODY$
        BEGIN
          if exists (select from qso 
                where qso.callsign = new.callsign and 
                    qso.log_id = new.log_id and 
                    qso.id <> new.id and 
                    qso.qso_mode = new.qso_mode and 
                    qso.band = new.band and 
                    qso.qso_datetime > new.qso_datetime - interval '5 minutes' and 
			        qso.qso_datetime < new.qso_datetime + interval '5 minutes')
		  then
			  raise exception using
					errcode='HB001',
					message='The QSO is already in this log.';
		  end if;
		  RETURN NEW;
        END;
        $BODY$ language 'plpgsql';
        """
    ))

    op.execute(
        """
        CREATE TRIGGER check_qso_dupes
            BEFORE INSERT OR UPDATE
            ON qso
            FOR EACH ROW
        EXECUTE FUNCTION check_qso_dupes();
        """
    )
   

def downgrade() -> None:
    op.execute("""DROP SEQUENCE if exists public.qso_id_seq;""")
    op.execute("drop table if exists qso;")


