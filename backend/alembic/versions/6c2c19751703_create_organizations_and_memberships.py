"""create_organizations_and_memberships

Revision ID: 6c2c19751703
Revises: 30ee8f1c6fb3
Create Date: 2026-11-19 08:59:21.857134

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c2c19751703'
down_revision: Union[str, Sequence[str], None] = '30ee8f1c6fb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('organizations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)

    op.create_table('organization_memberships',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_organization_user')
    )
    op.create_index('idx_memberships_org_active', 'organization_memberships', ['organization_id', 'is_active'], unique=False)
    op.create_index('idx_memberships_user_active', 'organization_memberships', ['user_id', 'is_active'], unique=False)
    op.create_index(op.f('ix_organization_memberships_id'), 'organization_memberships', ['id'], unique=False)
    op.create_index(op.f('ix_organization_memberships_organization_id'), 'organization_memberships', ['organization_id'], unique=False)
    op.create_index(op.f('ix_organization_memberships_user_id'), 'organization_memberships', ['user_id'], unique=False)

    # Partial unique index ensuring exactly one OWNER per organization
    op.create_index(
        'uq_org_active_owner',
        'organization_memberships',
        ['organization_id'],
        unique=True,
        postgresql_where=sa.text("role = 'OWNER'")
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_org_active_owner', table_name='organization_memberships')
    op.drop_index(op.f('ix_organization_memberships_user_id'), table_name='organization_memberships')
    op.drop_index(op.f('ix_organization_memberships_organization_id'), table_name='organization_memberships')
    op.drop_index(op.f('ix_organization_memberships_id'), table_name='organization_memberships')
    op.drop_index('idx_memberships_user_active', table_name='organization_memberships')
    op.drop_index('idx_memberships_org_active', table_name='organization_memberships')
    op.drop_table('organization_memberships')
    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    op.drop_table('organizations')
