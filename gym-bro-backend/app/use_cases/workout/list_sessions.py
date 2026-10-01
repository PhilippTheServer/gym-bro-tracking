"""Use case: list completed workout sessions for a user."""

from app.domain.models.workout import WorkoutSession
from app.repositories.workout_repository import WorkoutRepository


class ListSessionsUseCase:
    """Returns a paginated list of completed workout sessions for the requesting user."""

    def __init__(self, repository: WorkoutRepository) -> None:
        """
        Arg: repository - workout data-access object.
        Operation: stores the repository for use during execution.
        Return: ListSessionsUseCase instance.
        """
        self._repository = repository

    async def execute(self, user_id: str, limit: int = 50, offset: int = 0) -> list[WorkoutSession]:
        """
        Arg: user_id - Keycloak subject; limit - max results; offset - pagination offset.
        Operation: retrieves completed sessions ordered by start time descending.
        Return: list of WorkoutSession entities.
        """
        return await self._repository.list_for_user(user_id, limit, offset)
