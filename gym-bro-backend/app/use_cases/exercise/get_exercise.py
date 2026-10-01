"""Use case: retrieve a single exercise by ID."""

import uuid

from app.domain.exceptions import NotFoundError
from app.domain.models.exercise import Exercise
from app.repositories.exercise_repository import ExerciseRepository


class GetExerciseUseCase:
    """Retrieves a single exercise or raises NotFoundError."""

    def __init__(self, repository: ExerciseRepository) -> None:
        """
        Arg: repository - exercise data-access object.
        Operation: stores the repository for use during execution.
        Return: GetExerciseUseCase instance.
        """
        self._repository = repository

    async def execute(self, exercise_id: uuid.UUID) -> Exercise:
        """
        Arg: exercise_id - UUID of the exercise to retrieve.
        Operation: fetches the exercise from the repository; raises NotFoundError if absent.
        Return: the matching Exercise entity.
        """
        exercise = await self._repository.get(exercise_id)
        if exercise is None:
            raise NotFoundError("Exercise", exercise_id)
        return exercise
