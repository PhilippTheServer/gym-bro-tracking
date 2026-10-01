"""Use case: create a custom exercise for a user."""

from app.domain.models.exercise import Exercise
from app.domain.schemas.exercise import ExerciseCreate
from app.repositories.exercise_repository import ExerciseRepository


class CreateExerciseUseCase:
    """Creates and persists a new custom exercise owned by the requesting user."""

    def __init__(self, repository: ExerciseRepository) -> None:
        """
        Arg: repository - exercise data-access object.
        Operation: stores the repository for use during execution.
        Return: CreateExerciseUseCase instance.
        """
        self._repository = repository

    async def execute(self, data: ExerciseCreate, user_id: str) -> Exercise:
        """
        Arg: data - validated exercise creation input; user_id - owner's Keycloak subject.
        Operation: constructs an Exercise entity marked as custom, persists it, and commits.
        Return: the newly created Exercise entity.
        """
        exercise = Exercise(
            **data.model_dump(),
            is_custom=True,
            created_by=user_id,
        )
        result = await self._repository.create(exercise)
        await self._repository.commit()
        return result
