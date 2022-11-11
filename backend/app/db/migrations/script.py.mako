"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa

import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from common import timestamps


${imports if imports else ""}

# revision identifiers, used by Alembic
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:

    ${upgrades if upgrades else "pass"}


def downgrade() -> None:

    ${downgrades if downgrades else "pass"}


