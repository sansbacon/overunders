"""Add draft contest tables

Revision ID: 20250719_214525
Revises: c43685dc2f29
Create Date: 2025-01-19 21:45:25.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250719_214525'
down_revision = 'c43685dc2f29'
branch_labels = None
depends_on = None


def upgrade():
    # Create draft_pools table
    op.create_table('draft_pools',
        sa.Column('draft_pool_id', sa.Integer(), nullable=False),
        sa.Column('pool_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sport', sa.String(length=50), nullable=True),
        sa.Column('season', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('draft_pool_id')
    )

    # Create draft_items table
    op.create_table('draft_items',
        sa.Column('draft_item_id', sa.Integer(), nullable=False),
        sa.Column('draft_pool_id', sa.Integer(), nullable=False),
        sa.Column('item_name', sa.String(length=200), nullable=False),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('item_metadata', sa.JSON(), nullable=True),
        sa.Column('item_order', sa.Integer(), nullable=False),
        sa.Column('is_available', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['draft_pool_id'], ['draft_pools.draft_pool_id'], ),
        sa.PrimaryKeyConstraint('draft_item_id')
    )

    # Create draft_contests table
    op.create_table('draft_contests',
        sa.Column('draft_contest_id', sa.Integer(), nullable=False),
        sa.Column('contest_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by_user', sa.Integer(), nullable=False),
        sa.Column('draft_pool_id', sa.Integer(), nullable=False),
        sa.Column('lock_timestamp', sa.DateTime(), nullable=False),
        sa.Column('draft_start_time', sa.DateTime(), nullable=True),
        sa.Column('draft_end_time', sa.DateTime(), nullable=True),
        sa.Column('picks_per_user', sa.Integer(), nullable=False),
        sa.Column('draft_order_type', sa.String(length=20), nullable=False),
        sa.Column('is_snake_draft', sa.Boolean(), nullable=False),
        sa.Column('current_pick_number', sa.Integer(), nullable=False),
        sa.Column('current_round', sa.Integer(), nullable=False),
        sa.Column('draft_status', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['draft_pool_id'], ['draft_pools.draft_pool_id'], ),
        sa.PrimaryKeyConstraint('draft_contest_id')
    )

    # Create draft_entries table
    op.create_table('draft_entries',
        sa.Column('draft_entry_id', sa.Integer(), nullable=False),
        sa.Column('draft_contest_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('draft_position', sa.Integer(), nullable=True),
        sa.Column('total_score', sa.Float(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['draft_contest_id'], ['draft_contests.draft_contest_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('draft_entry_id'),
        sa.UniqueConstraint('draft_contest_id', 'user_id', name='unique_user_draft_contest_entry')
    )

    # Create draft_scoring_rules table
    op.create_table('draft_scoring_rules',
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('draft_contest_id', sa.Integer(), nullable=False),
        sa.Column('rule_name', sa.String(length=100), nullable=False),
        sa.Column('rule_description', sa.Text(), nullable=True),
        sa.Column('points_per_unit', sa.Float(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['draft_contest_id'], ['draft_contests.draft_contest_id'], ),
        sa.PrimaryKeyConstraint('rule_id')
    )

    # Create draft_item_scores table
    op.create_table('draft_item_scores',
        sa.Column('score_id', sa.Integer(), nullable=False),
        sa.Column('draft_item_id', sa.Integer(), nullable=False),
        sa.Column('score_value', sa.Float(), nullable=False),
        sa.Column('score_category', sa.String(length=50), nullable=False),
        sa.Column('scoring_period', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('scored_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['draft_item_id'], ['draft_items.draft_item_id'], ),
        sa.PrimaryKeyConstraint('score_id')
    )

    # Create draft_picks table
    op.create_table('draft_picks',
        sa.Column('draft_pick_id', sa.Integer(), nullable=False),
        sa.Column('draft_entry_id', sa.Integer(), nullable=False),
        sa.Column('draft_item_id', sa.Integer(), nullable=False),
        sa.Column('pick_number', sa.Integer(), nullable=False),
        sa.Column('pick_round', sa.Integer(), nullable=False),
        sa.Column('picked_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['draft_entry_id'], ['draft_entries.draft_entry_id'], ),
        sa.ForeignKeyConstraint(['draft_item_id'], ['draft_items.draft_item_id'], ),
        sa.PrimaryKeyConstraint('draft_pick_id'),
        sa.UniqueConstraint('draft_entry_id', 'pick_number', name='unique_entry_pick_number'),
        sa.UniqueConstraint('draft_item_id', name='unique_draft_item')
    )

    # Create league_draft_contests table
    op.create_table('league_draft_contests',
        sa.Column('league_draft_contest_id', sa.Integer(), nullable=False),
        sa.Column('league_id', sa.Integer(), nullable=False),
        sa.Column('draft_contest_id', sa.Integer(), nullable=False),
        sa.Column('contest_order', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['draft_contest_id'], ['draft_contests.draft_contest_id'], ),
        sa.ForeignKeyConstraint(['league_id'], ['leagues.league_id'], ),
        sa.PrimaryKeyConstraint('league_draft_contest_id'),
        sa.UniqueConstraint('league_id', 'draft_contest_id', name='unique_league_draft_contest')
    )


def downgrade():
    # Drop tables in reverse order due to foreign key constraints
    op.drop_table('league_draft_contests')
    op.drop_table('draft_picks')
    op.drop_table('draft_item_scores')
    op.drop_table('draft_scoring_rules')
    op.drop_table('draft_entries')
    op.drop_table('draft_contests')
    op.drop_table('draft_items')
    op.drop_table('draft_pools')
