"""create_profiles_table

Revision ID: a70122dd5391
Revises: 731015cbaf5a
Create Date: 2022-11-11 14:38:44.999442

"""
from alembic import op
import sqlalchemy as sa

import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from common import timestamps




# revision identifiers, used by Alembic
revision = 'a70122dd5391'
down_revision = '731015cbaf5a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("full_name", sa.VARCHAR(256), nullable=True),
        sa.Column("address", sa.VARCHAR(512), nullable=True),
        sa.Column("bio", sa.VARCHAR(1024), nullable=True, server_default=""),
        sa.Column("default_image", sa.CHAR(32), nullable=True),
	    sa.Column("current_callsign", sa.VARCHAR(32), nullable=True, unique=True),
	    sa.Column("prev_callsigns", sa.VARCHAR(512), nullable=True),
	    sa.Column("birthdate", sa.DATE, nullable=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE")),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_profiles_modtime
            BEFORE UPDATE
            ON profiles
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )

def downgrade() -> None:

 op.execute("drop table if exists profiles;")


