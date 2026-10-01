"""exercise taxonomy: primary muscle, category and catalogue id

Revision ID: 0002_exercise_taxonomy
Revises: 0001_initial_schema
Create Date: 2026-09-17 21:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0002_exercise_taxonomy'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('exercises', sa.Column('primary_muscle', sa.String(length=30), nullable=True))
    op.add_column('exercises', sa.Column('category', sa.String(length=30), nullable=True))
    op.add_column('exercises', sa.Column('external_id', sa.String(length=120), nullable=True))
    op.create_index(op.f('ix_exercises_primary_muscle'), 'exercises', ['primary_muscle'], unique=False)
    op.create_index(op.f('ix_exercises_category'), 'exercises', ['category'], unique=False)
    op.create_index(op.f('ix_exercises_external_id'), 'exercises', ['external_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_exercises_external_id'), table_name='exercises')
    op.drop_index(op.f('ix_exercises_category'), table_name='exercises')
    op.drop_index(op.f('ix_exercises_primary_muscle'), table_name='exercises')
    op.drop_column('exercises', 'external_id')
    op.drop_column('exercises', 'category')
    op.drop_column('exercises', 'primary_muscle')
