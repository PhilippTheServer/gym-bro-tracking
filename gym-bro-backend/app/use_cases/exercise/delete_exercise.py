"""Use case: delete a custom exercise."""

import uuid

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.repositories.exercise_repository import ExerciseRepository


class DeleteExerciseUseCase:
    """Deletes a custom exercise owned by the requesting user."""

    def __init__(self, repository: ExerciseRepository) -> None:
        """
        Arg: repository - exercise data-access object.
        Operation: stores the repository for use during execution.
        Return: DeleteExerciseUseCase instance.
        """
        self._repository = repository

    async def execute(self, exercise_id: uuid.UUID, user_id: str) -> None:
        """
        Arg: exercise_id - UUID of the exercise to delete; user_id - requester's subject.
        Operation: loads the exercise, verifies it is custom and owned by the user, then deletes.
                   Raises NotFoundError if absent.
                   Raises ForbiddenError if not owned by the requester.
        Return: None.
        """
        exercise = await self._repository.get(exercise_id)
        if exercise is None:
            raise NotFoundError("Exercise", exercise_id)
        if not exercise.is_custom or exercise.created_by != user_id:
            raise ForbiddenError("Only the owner can delete a custom exercise.")

        await self._repository.delete(exercise)
        await self._repository.commit()
