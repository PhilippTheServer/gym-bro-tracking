"""Use case: retrieve a single workout session with full detail."""

import uuid

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.domain.models.workout import WorkoutSession
from app.repositories.workout_repository import WorkoutRepository


class GetSessionUseCase:
    """Fetches a workout session and verifies the requester is the owner."""

    def __init__(self, repository: WorkoutRepository) -> None:
        """
        Arg: repository - workout data-access object.
        Operation: stores the repository for use during execution.
        Return: GetSessionUseCase instance.
        """
        self._repository = repository

    async def execute(self, session_id: uuid.UUID, user_id: str) -> WorkoutSession:
        """
        Arg: session_id - UUID of the session; user_id - requester's Keycloak subject.
        Operation: loads the session with all exercises and sets.
                   Raises NotFoundError if the session does not exist.
                   Raises ForbiddenError if the requester does not own the session.
        Return: fully loaded WorkoutSession entity.
        """
        session = await self._repository.get_full(session_id)
        if session is None:
            raise NotFoundError("WorkoutSession", session_id)
        if session.user_id != user_id:
            raise ForbiddenError("You do not own this session.")
        return session
