"""create_users_table

Revision ID: 731015cbaf5a
Revises: 
Create Date: 2022-10-17 12:45:33.915086

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import Sequence, CreateSequence

# revision identifiers, used by Alembic
revision = '731015cbaf5a'
down_revision = None
branch_labels = None
depends_on = None


def create_users_table() -> None:
    conn = op.get_bind()


    conn.execute(sa.text("""CREATE SEQUENCE IF NOT EXISTS public.user_id_sec
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;"""))

    conn.execute(sa.text("""CREATE OR REPLACE FUNCTION public.generate_user_id(
	OUT result bigint)
    RETURNS bigint
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE
    our_epoch bigint := 1314220021721;
    seq_id bigint;
    now_millis bigint;
BEGIN
    SELECT nextval('user_id_sec') % 1024 INTO seq_id;
    SELECT FLOOR(EXTRACT(EPOCH FROM clock_timestamp()) * 1000) INTO now_millis;
    result := (now_millis - our_epoch) << 23;
    result := result | (seq_id);
END;
    
$BODY$;
    """))

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True, server_default=sa.text("generate_user_id()"),
            autoincrement=False),
        sa.Column("email", sa.VARCHAR(64), nullable=False, unique=True),
        sa.Column("email_verified", sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column("password_hash", sa.VARCHAR(128), nullable=False)
    )

def upgrade() -> None:
    create_users_table()


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute("drop table if exists users;")
    conn.execute("""DROP FUNCTION public.generate_user_id();""")
    conn.execute("""DROP SEQUENCE public.user_id_sec;""")
   


