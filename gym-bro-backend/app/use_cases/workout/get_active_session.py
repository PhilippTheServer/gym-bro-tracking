"""Use case: retrieve the currently active (unfinished) workout session."""

from app.domain.models.workout import WorkoutSession
from app.repositories.workout_repository import WorkoutRepository


class GetActiveSessionUseCase:
    """Returns the most recent unfinished session for the requesting user, or None."""

    def __init__(self, repository: WorkoutRepository) -> None:
        """
        Arg: repository - workout data-access object.
        Operation: stores the repository for use during execution.
        Return: GetActiveSessionUseCase instance.
        """
        self._repository = repository

    async def execute(self, user_id: str) -> WorkoutSession | None:
        """
        Arg: user_id - Keycloak subject of the requesting user.
        Operation: queries for the most recent session where completed_at is NULL.
        Return: the active WorkoutSession entity, or None if no active session exists.
        """
        return await self._repository.get_active(user_id)
