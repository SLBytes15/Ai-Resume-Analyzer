"""create_candidate_profiles_and_resumes

Revision ID: f3bd81aedcaf
Revises: 6c2c19751703
Create Date: 2026-11-23 07:43:50.788569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f3bd81aedcaf'
down_revision: Union[str, Sequence[str], None] = '6c2c19751703'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('candidate_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('phone', sa.String(length=32), nullable=True),
        sa.Column('location', sa.String(length=128), nullable=True),
        sa.Column('headline', sa.String(length=255), nullable=True),
        sa.Column('professional_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_candidate_profiles_id'), 'candidate_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_candidate_profiles_user_id'), 'candidate_profiles', ['user_id'], unique=True)

    op.create_table('resumes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('candidate_id', sa.UUID(), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('storage_path', sa.String(length=512), nullable=False),
        sa.Column('mime_type', sa.String(length=64), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('parsed_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('parsing_status', sa.String(length=32), nullable=False),
        sa.Column('parsing_error', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidate_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_resumes_candidate_created', 'resumes', ['candidate_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_resumes_candidate_id'), 'resumes', ['candidate_id'], unique=False)
    op.create_index(op.f('ix_resumes_id'), 'resumes', ['id'], unique=False)
    op.create_index(op.f('ix_resumes_parsing_status'), 'resumes', ['parsing_status'], unique=False)
    op.create_index(op.f('ix_resumes_sha256'), 'resumes', ['sha256'], unique=False)

    # Partial unique index ensuring at most one active resume per candidate
    op.create_index(
        'uq_candidate_active_resume',
        'resumes',
        ['candidate_id'],
        unique=True,
        postgresql_where=sa.text("is_active = TRUE")
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_candidate_active_resume', table_name='resumes')
    op.drop_index(op.f('ix_resumes_sha256'), table_name='resumes')
    op.drop_index(op.f('ix_resumes_parsing_status'), table_name='resumes')
    op.drop_index(op.f('ix_resumes_id'), table_name='resumes')
    op.drop_index(op.f('ix_resumes_candidate_id'), table_name='resumes')
    op.drop_index('idx_resumes_candidate_created', table_name='resumes')
    op.drop_table('resumes')
    op.drop_index(op.f('ix_candidate_profiles_user_id'), table_name='candidate_profiles')
    op.drop_index(op.f('ix_candidate_profiles_id'), table_name='candidate_profiles')
    op.drop_table('candidate_profiles')
