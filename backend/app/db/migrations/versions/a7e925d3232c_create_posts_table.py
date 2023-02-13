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

    op.execute(sa.text("""CREATE SEQUENCE IF NOT EXISTS public.posts_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;"""))

    op.create_table(
        "posts",
        sa.Column("id", sa.BigInteger, primary_key=True, 
            server_default=sa.text("generate_id('posts_id_seq'::text)"),
            autoincrement=False),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE")),  
        sa.Column("title", sa.Text, nullable=False, index=True),
        sa.Column("contents", sa.Text, nullable=False, index=True),
        sa.Column("post_type", sa.SmallInteger, nullable=False, server_default=sa.text('0')),
        sa.Column("post_visibility", sa.SmallInteger, nullable=False, server_default=sa.text('0')),
        *timestamps()
    )
    op.execute(
        """
        CREATE TRIGGER update_posts_modtime
            BEFORE UPDATE
            ON posts
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )

def downgrade() -> None:
    op.execute("""DROP SEQUENCE if exists public.posts_id_seq;""")
    op.execute("drop table if exists posts;")


