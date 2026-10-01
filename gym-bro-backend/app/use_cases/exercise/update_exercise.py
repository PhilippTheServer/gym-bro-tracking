"""Use case: update a custom exercise."""

import uuid

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.domain.models.exercise import Exercise
from app.domain.schemas.exercise import ExerciseUpdate
from app.repositories.exercise_repository import ExerciseRepository


class UpdateExerciseUseCase:
    """Updates fields on a custom exercise the requesting user owns."""

    def __init__(self, repository: ExerciseRepository) -> None:
        """
        Arg: repository - exercise data-access object.
        Operation: stores the repository for use during execution.
        Return: UpdateExerciseUseCase instance.
        """
        self._repository = repository

    async def execute(self, exercise_id: uuid.UUID, data: ExerciseUpdate, user_id: str) -> Exercise:
        """
        Arg: exercise_id - UUID of the exercise; data - fields to update; user_id - requester.
        Operation: loads the exercise, verifies ownership, applies the patch, and commits.
                   Raises NotFoundError if the exercise does not exist.
                   Raises ForbiddenError if the requester does not own the custom exercise.
        Return: the updated Exercise entity.
        """
        exercise = await self._repository.get(exercise_id)
        if exercise is None:
            raise NotFoundError("Exercise", exercise_id)
        if exercise.is_custom and exercise.created_by != user_id:
            raise ForbiddenError("You do not own this exercise.")

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(exercise, field, value)

        await self._repository.commit()
        return exercise
