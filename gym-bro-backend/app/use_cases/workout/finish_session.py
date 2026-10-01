"""Use case: mark a workout session as completed."""

import uuid
from datetime import UTC, datetime

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.domain.models.workout import WorkoutSession
from app.repositories.workout_repository import WorkoutRepository


class FinishSessionUseCase:
    """Records the completion timestamp on a workout session."""

    def __init__(self, repository: WorkoutRepository) -> None:
        """
        Arg: repository - workout data-access object.
        Operation: stores the repository for use during execution.
        Return: FinishSessionUseCase instance.
        """
        self._repository = repository

    async def execute(self, session_id: uuid.UUID, user_id: str) -> WorkoutSession:
        """
        Arg: session_id - UUID of the session to finish; user_id - requester's subject.
        Operation: loads the session, verifies ownership, sets completed_at to UTC now.
                   Raises NotFoundError if the session does not exist.
                   Raises ForbiddenError if the requester does not own the session.
        Return: updated and fully loaded WorkoutSession entity.
        """
        session = await self._repository.get_full(session_id)
        if session is None:
            raise NotFoundError("WorkoutSession", session_id)
        if session.user_id != user_id:
            raise ForbiddenError("You do not own this session.")

        session.completed_at = datetime.now(UTC)
        await self._repository.commit()
        return await self._repository.get_full(session_id)
