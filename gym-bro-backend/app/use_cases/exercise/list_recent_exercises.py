"""Use case: list the exercises a user trains most recently."""

from app.domain.models.exercise import Exercise
from app.repositories.exercise_repository import ExerciseRepository


class ListRecentExercisesUseCase:
    """Returns the exercises a user last logged, most recent first."""

    def __init__(self, repository: ExerciseRepository) -> None:
        """
        Arg: repository - exercise data-access object.
        Operation: stores the repository for use during execution.
        Return: ListRecentExercisesUseCase instance.
        """
        self._repository = repository

    async def execute(self, user_id: str, limit: int = 12) -> list[Exercise]:
        """
        Arg: user_id - Keycloak subject of the requesting user; limit - how many to return.
        Operation: retrieves the exercises appearing in the user's most recent sessions, so the
                   picker can offer what they actually train ahead of a library of 876.
        Return: list of Exercise entities, most recently trained first.
        """
        return await self._repository.list_recently_used(user_id, limit)
