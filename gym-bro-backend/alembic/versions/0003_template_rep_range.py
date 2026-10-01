"""template sets: an optional top of the rep range

Revision ID: 0003_template_rep_range
Revises: 0002_exercise_taxonomy
Create Date: 2026-09-17 22:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0003_template_rep_range'
down_revision: Union[str, None] = '0002_exercise_taxonomy'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('template_sets', sa.Column('target_reps_max', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('template_sets', 'target_reps_max')
