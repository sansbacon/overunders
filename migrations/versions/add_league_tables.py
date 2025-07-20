"""Add league tables

Revision ID: add_league_tables
Revises: c43685dc2f29
Create Date: 2025-01-12 09:08:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_league_tables'
down_revision = 'c43685dc2f29'
branch_labels = None
depends_on = None


def upgrade():
    # Create leagues table
    op.create_table('leagues',
        sa.Column('league_id', sa.Integer(), nullable=False),
        sa.Column('league_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by_user', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=False),
        sa.Column('win_bonus_points', sa.Integer(), nullable=False, default=5),
        sa.ForeignKeyConstraint(['created_by_user'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('league_id')
    )
    
    # Create league_memberships table
    op.create_table('league_memberships',
        sa.Column('membership_id', sa.Integer(), nullable=False),
        sa.Column('league_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('is_admin', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['league_id'], ['leagues.league_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('membership_id'),
        sa.UniqueConstraint('league_id', 'user_id', name='unique_league_user_membership')
    )
    
    # Create league_contests table
    op.create_table('league_contests',
        sa.Column('league_contest_id', sa.Integer(), nullable=False),
        sa.Column('league_id', sa.Integer(), nullable=False),
        sa.Column('contest_id', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('contest_order', sa.Integer(), nullable=False, default=1),
        sa.ForeignKeyConstraint(['league_id'], ['leagues.league_id'], ),
        sa.ForeignKeyConstraint(['contest_id'], ['contests.contest_id'], ),
        sa.PrimaryKeyConstraint('league_contest_id'),
        sa.UniqueConstraint('league_id', 'contest_id', name='unique_league_contest')
    )


def downgrade():
    op.drop_table('league_contests')
    op.drop_table('league_memberships')
    op.drop_table('leagues')
