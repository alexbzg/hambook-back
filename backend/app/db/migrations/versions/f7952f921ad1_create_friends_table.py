"""create_friends_table

Revision ID: f7952f921ad1
Revises: a7e925d3232c
Create Date: 2023-04-06 08:11:12.799457

"""
from alembic import op
import sqlalchemy as sa

import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from common import timestamps




# revision identifiers, used by Alembic
revision = 'f7952f921ad1'
down_revision = 'a7e925d3232c'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute(sa.text("""CREATE SEQUENCE IF NOT EXISTS public.friends_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;"""))

    op.create_table(
        "friends",
        sa.Column("id", sa.BigInteger, primary_key=True, 
            server_default=sa.text("generate_id('friends_id_seq'::text)"),
            autoincrement=False),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("friend_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE")),
        timestamps()[0],
        sa.UniqueConstraint('user_id', 'friend_id', name='unique_constraint_friends')
    )

def downgrade() -> None:
    op.execute("""DROP SEQUENCE if exists public.friends_id_sec;""")
    op.execute("drop table if exists friends;")


