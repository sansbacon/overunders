"""Add content moderation tables

Revision ID: add_content_moderation_tables
Revises: c43685dc2f29_add_is_ai_generated_field_to_contest_
Create Date: 2025-07-13 06:58:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_content_moderation_tables'
down_revision = 'add_league_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create content_moderation_logs table
    op.create_table('content_moderation_logs',
        sa.Column('log_id', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('moderation_result', sa.JSON(), nullable=False),
        sa.Column('action_taken', sa.String(50), nullable=False),
        sa.Column('moderator_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['moderator_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('log_id')
    )
    
    # Create content_reports table
    op.create_table('content_reports',
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('reported_by_user_id', sa.Integer(), nullable=False),
        sa.Column('report_reason', sa.String(100), nullable=False),
        sa.Column('report_description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('reviewed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['reported_by_user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('report_id')
    )
    
    # Create user_warnings table
    op.create_table('user_warnings',
        sa.Column('warning_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('issued_by_user_id', sa.Integer(), nullable=False),
        sa.Column('warning_type', sa.String(50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=True),
        sa.Column('content_id', sa.Integer(), nullable=True),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['issued_by_user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('warning_id')
    )
    
    # Add moderation-related fields to existing tables
    # Add moderation-related fields to existing tables using batch mode for SQLite
    with op.batch_alter_table('contests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('moderation_status', sa.String(20), nullable=False, server_default='approved'))
        batch_op.add_column(sa.Column('moderation_notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('flagged_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('reviewed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('reviewed_by_user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_contests_reviewed_by', 'users', ['reviewed_by_user_id'], ['user_id'])
    
    with op.batch_alter_table('leagues', schema=None) as batch_op:
        batch_op.add_column(sa.Column('moderation_status', sa.String(20), nullable=False, server_default='approved'))
        batch_op.add_column(sa.Column('moderation_notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('flagged_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('reviewed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('reviewed_by_user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_leagues_reviewed_by', 'users', ['reviewed_by_user_id'], ['user_id'])
    
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('moderation_status', sa.String(20), nullable=False, server_default='approved'))
        batch_op.add_column(sa.Column('moderation_notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('flagged_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('reviewed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('reviewed_by_user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_questions_reviewed_by', 'users', ['reviewed_by_user_id'], ['user_id'])
    
    # Add user reputation and trust fields
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('trust_score', sa.Integer(), nullable=False, server_default='100'))
        batch_op.add_column(sa.Column('warning_count', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('is_suspended', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('suspended_until', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('suspension_reason', sa.Text(), nullable=True))


def downgrade():
    # Remove added columns from users table
    op.drop_column('users', 'suspension_reason')
    op.drop_column('users', 'suspended_until')
    op.drop_column('users', 'is_suspended')
    op.drop_column('users', 'warning_count')
    op.drop_column('users', 'trust_score')
    
    # Remove added columns from questions table
    op.drop_constraint('fk_questions_reviewed_by', 'questions', type_='foreignkey')
    op.drop_column('questions', 'reviewed_by_user_id')
    op.drop_column('questions', 'reviewed_at')
    op.drop_column('questions', 'flagged_at')
    op.drop_column('questions', 'moderation_notes')
    op.drop_column('questions', 'moderation_status')
    
    # Remove added columns from leagues table
    op.drop_constraint('fk_leagues_reviewed_by', 'leagues', type_='foreignkey')
    op.drop_column('leagues', 'reviewed_by_user_id')
    op.drop_column('leagues', 'reviewed_at')
    op.drop_column('leagues', 'flagged_at')
    op.drop_column('leagues', 'moderation_notes')
    op.drop_column('leagues', 'moderation_status')
    
    # Remove added columns from contests table
    op.drop_constraint('fk_contests_reviewed_by', 'contests', type_='foreignkey')
    op.drop_column('contests', 'reviewed_by_user_id')
    op.drop_column('contests', 'reviewed_at')
    op.drop_column('contests', 'flagged_at')
    op.drop_column('contests', 'moderation_notes')
    op.drop_column('contests', 'moderation_status')
    
    # Drop new tables
    op.drop_table('user_warnings')
    op.drop_table('content_reports')
    op.drop_table('content_moderation_logs')
