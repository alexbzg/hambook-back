"""create media table

Revision ID: 789b04bb955c
Revises: a70122dd5391
Create Date: 2022-11-17 12:13:11.557595

"""
from alembic import op
import sqlalchemy as sa

import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from common import timestamps




# revision identifiers, used by Alembic
revision = '789b04bb955c'
down_revision = 'a70122dd5391'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""CREATE SEQUENCE IF NOT EXISTS public.media_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;"""))

    op.create_table(
        "media",
        sa.Column("id", sa.BigInteger, primary_key=True, 
            server_default=sa.text("generate_id('media_id_sec'::text)"),
            autoincrement=False),
        sa.Column("media_type", sa.SmallInteger),
        sa.Column("file_path", sa.VARCHAR(512), nullable=False),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE")),
        timestamps()[0],
    )

def downgrade() -> None:
    op.execute("""DROP SEQUENCE if exists public.user_id_sec;""")
    op.execute("drop table if exists media;")
