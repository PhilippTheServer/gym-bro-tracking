"""Use case: export a user's completed workout sessions for the daily integration."""

from datetime import datetime

from app.domain.models.workout import WorkoutSession
from app.repositories.workout_repository import WorkoutRepository


class ExportSessionsUseCase:
    """Returns a user's completed workout sessions finished after a cutoff, ascending."""

    def __init__(self, repository: WorkoutRepository) -> None:
        """
        Arg: repository - workout data-access object.
        Operation: stores the repository for use during execution.
        Return: ExportSessionsUseCase instance.
        """
        self._repository = repository

    async def execute(
        self,
        user_id: str,
        completed_after: datetime,
        limit: int = 100,
        offset: int = 0,
    ) -> list[WorkoutSession]:
        """
        Arg: user_id - Keycloak subject of the workout owner; completed_after - exclusive,
             timezone-aware lower bound; limit - max results; offset - pagination offset.
        Operation: retrieves this user's completed sessions finished after the cutoff,
                   ordered oldest first.
        Return: list of WorkoutSession entities.
        """
        return await self._repository.list_completed_since(user_id, completed_after, limit, offset)
