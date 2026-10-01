"""Repository for WorkoutTemplate entities."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domain.models.template import TemplateExercise, WorkoutTemplate
from app.repositories.base import BaseRepository


class TemplateRepository(BaseRepository[WorkoutTemplate]):
    """Data-access object for the workout_templates table."""

    model = WorkoutTemplate

    async def list_for_user(self, user_id: str) -> list[WorkoutTemplate]:
        """
        Arg: user_id - Keycloak subject of the template owner.
        Operation: selects all templates for the user, ordered alphabetically by name.
                   Exercises, their exercise entity and their sets are all eager-loaded,
                   because the response schema serialises them and a lazy load outside
                   the async session's greenlet context would fail.
        Return: list of WorkoutTemplate entities.
        """
        statement = (
            select(WorkoutTemplate)
            .where(WorkoutTemplate.user_id == user_id)
            .options(
                selectinload(WorkoutTemplate.exercises).selectinload(TemplateExercise.exercise),
                selectinload(WorkoutTemplate.exercises).selectinload(TemplateExercise.sets),
            )
            .order_by(WorkoutTemplate.name)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_full(self, id: uuid.UUID) -> WorkoutTemplate | None:
        """
        Arg: id - UUID of the template to load.
        Operation: loads the template with all exercises, their exercise entity, and all sets
                   via eager loading to avoid N+1 queries.
        Return: fully loaded WorkoutTemplate entity, or None if not found.
        """
        statement = (
            select(WorkoutTemplate)
            .where(WorkoutTemplate.id == id)
            .options(
                selectinload(WorkoutTemplate.exercises).selectinload(TemplateExercise.exercise),
                selectinload(WorkoutTemplate.exercises).selectinload(TemplateExercise.sets),
            )
            # populate_existing: these reloads run right after a write, and the
            # instances are still in the session's identity map. Without it their
            # already-loaded collections would be reused and the caller would get
            # back the pre-write state.
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
