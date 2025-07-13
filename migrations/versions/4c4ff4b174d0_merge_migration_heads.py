"""merge_migration_heads

Revision ID: 4c4ff4b174d0
Revises: add_basic_reputation_tables, add_nfl_schedules
Create Date: 2025-07-13 07:29:20.562336

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c4ff4b174d0'
down_revision = ('add_basic_reputation_tables', 'add_nfl_schedules')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
