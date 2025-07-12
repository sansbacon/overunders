"""Add NFL schedules table

Revision ID: add_nfl_schedules
Revises: 99b5f12b5c77
Create Date: 2025-01-11 16:54:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_nfl_schedules'
down_revision = '99b5f12b5c77'
branch_labels = None
depends_on = None


def upgrade():
    # Create NFL schedules table
    op.create_table('nfl_schedules',
        sa.Column('schedule_id', sa.Integer(), nullable=False),
        sa.Column('season_year', sa.Integer(), nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('home_team', sa.String(50), nullable=False),
        sa.Column('away_team', sa.String(50), nullable=False),
        sa.Column('game_date', sa.DateTime(), nullable=True),
        sa.Column('game_time', sa.String(20), nullable=True),
        sa.Column('is_playoff', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.PrimaryKeyConstraint('schedule_id')
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_nfl_schedules_season_week', 'nfl_schedules', ['season_year', 'week_number'])
    op.create_index('idx_nfl_schedules_teams', 'nfl_schedules', ['home_team', 'away_team'])


def downgrade():
    op.drop_index('idx_nfl_schedules_teams', table_name='nfl_schedules')
    op.drop_index('idx_nfl_schedules_season_week', table_name='nfl_schedules')
    op.drop_table('nfl_schedules')
