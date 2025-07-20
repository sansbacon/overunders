"""Add basic reputation tables

Revision ID: add_basic_reputation_tables
Revises: c43685dc2f29
Create Date: 2025-01-13 07:26:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_basic_reputation_tables'
down_revision = 'add_content_moderation_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_reputation table
    op.create_table('user_reputation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False, default=100),
        sa.Column('contests_created', sa.Integer(), nullable=False, default=0),
        sa.Column('contests_participated', sa.Integer(), nullable=False, default=0),
        sa.Column('contests_won', sa.Integer(), nullable=False, default=0),
        sa.Column('leagues_created', sa.Integer(), nullable=False, default=0),
        sa.Column('leagues_joined', sa.Integer(), nullable=False, default=0),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_reputation_user_id'), 'user_reputation', ['user_id'], unique=True)

    # Create user_verification table
    op.create_table('user_verification',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('verification_type', sa.String(length=50), nullable=False),
        sa.Column('verification_level', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, default='pending'),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('verified_by_admin_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['verified_by_admin_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_verification_user_id'), 'user_verification', ['user_id'], unique=False)


def downgrade():
    op.drop_table('user_verification')
    op.drop_table('user_reputation')
