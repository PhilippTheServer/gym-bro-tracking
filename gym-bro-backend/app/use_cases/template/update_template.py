"""Use case: replace a workout template's content."""

import uuid

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.domain.models.template import TemplateExercise, TemplateSet, WorkoutTemplate
from app.domain.ordering import resolve_order
from app.domain.schemas.template import WorkoutTemplateUpdate
from app.repositories.template_repository import TemplateRepository


class UpdateTemplateUseCase:
    """Replaces scalar fields and optionally all exercises on a workout template."""

    def __init__(self, repository: TemplateRepository) -> None:
        """
        Arg: repository - template data-access object.
        Operation: stores the repository for use during execution.
        Return: UpdateTemplateUseCase instance.
        """
        self._repository = repository

    async def execute(
        self, template_id: uuid.UUID, data: WorkoutTemplateUpdate, user_id: str
    ) -> WorkoutTemplate:
        """
        Arg: template_id - UUID of the template; data - update payload; user_id - requester.
        Operation: verifies ownership, patches scalar fields, and when exercises are provided
                   replaces the entire exercise/set graph. Commits and reloads full relations.
                   Raises NotFoundError if the template does not exist.
                   Raises ForbiddenError if the requester is not the owner.
        Return: updated and fully loaded WorkoutTemplate entity.
        """
        template = await self._repository.get_full(template_id)
        if template is None:
            raise NotFoundError("WorkoutTemplate", template_id)
        if template.user_id != user_id:
            raise ForbiddenError("You do not own this template.")

        self._apply_scalar_updates(template, data)

        if data.exercises is not None:
            self._replace_exercises(template, data.exercises)

        await self._repository.commit()
        return await self._repository.get_full(template_id)

    @staticmethod
    def _apply_scalar_updates(template: WorkoutTemplate, data: WorkoutTemplateUpdate) -> None:
        """
        Arg: template - entity to mutate; data - patch payload.
        Operation: sets each non-None scalar field from data onto the template entity.
        Return: None (mutates template in place).
        """
        for field, value in data.model_dump(exclude_none=True, exclude={"exercises"}).items():
            setattr(template, field, value)

    @staticmethod
    def _replace_exercises(template: WorkoutTemplate, exercises_data: list) -> None:
        """
        Arg: template - entity to mutate; exercises_data - new exercise list from input.
        Operation: clears all existing TemplateExercise children and rebuilds them from input.
        Return: None (mutates template in place).
        """
        template.exercises.clear()
        for index, exercise_data in enumerate(exercises_data):
            template_exercise = TemplateExercise(
                exercise_id=exercise_data.exercise_id,
                order=resolve_order(exercise_data.order, index),
                notes=exercise_data.notes,
            )
            for set_index, set_data in enumerate(exercise_data.sets):
                template_set = TemplateSet(
                    **set_data.model_dump(exclude={"order"}),
                    order=resolve_order(set_data.order, set_index),
                )
                template_exercise.sets.append(template_set)
            template.exercises.append(template_exercise)
