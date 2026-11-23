"""add_interviewing_status_to_applications

Revision ID: 27af204e3f76
Revises: b3bdb42a490c
Create Date: 2026-11-23 16:42:53.459246

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27af204e3f76'
down_revision: Union[str, Sequence[str], None] = 'b3bdb42a490c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to include INTERVIEWING status in application check constraints."""
    op.drop_constraint('ck_applications_status_valid', 'applications', type_='check')
    op.drop_constraint('ck_status_history_new_status_valid', 'application_status_history', type_='check')

    op.create_check_constraint(
        'ck_applications_status_valid',
        'applications',
        "status IN ('SUBMITTED', 'UNDER_REVIEW', 'SHORTLISTED', 'INTERVIEWING', 'REJECTED', 'HIRED', 'WITHDRAWN')"
    )
    op.create_check_constraint(
        'ck_status_history_new_status_valid',
        'application_status_history',
        "new_status IN ('SUBMITTED', 'UNDER_REVIEW', 'SHORTLISTED', 'INTERVIEWING', 'REJECTED', 'HIRED', 'WITHDRAWN')"
    )


def downgrade() -> None:
    """Revert check constraints back to original 6 statuses."""
    op.drop_constraint('ck_applications_status_valid', 'applications', type_='check')
    op.drop_constraint('ck_status_history_new_status_valid', 'application_status_history', type_='check')

    op.create_check_constraint(
        'ck_applications_status_valid',
        'applications',
        "status IN ('SUBMITTED', 'UNDER_REVIEW', 'SHORTLISTED', 'REJECTED', 'HIRED', 'WITHDRAWN')"
    )
    op.create_check_constraint(
        'ck_status_history_new_status_valid',
        'application_status_history',
        "new_status IN ('SUBMITTED', 'UNDER_REVIEW', 'SHORTLISTED', 'REJECTED', 'HIRED', 'WITHDRAWN')"
    )
