"""Use case: delete a workout session."""

import uuid

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.repositories.workout_repository import WorkoutRepository


class DeleteSessionUseCase:
    """Deletes a workout session owned by the requesting user."""

    def __init__(self, repository: WorkoutRepository) -> None:
        """
        Arg: repository - workout data-access object.
        Operation: stores the repository for use during execution.
        Return: DeleteSessionUseCase instance.
        """
        self._repository = repository

    async def execute(self, session_id: uuid.UUID, user_id: str) -> None:
        """
        Arg: session_id - UUID of the session to delete; user_id - requester's subject.
        Operation: verifies existence and ownership, then deletes the session and all children.
                   Raises NotFoundError if the session does not exist.
                   Raises ForbiddenError if the requester does not own the session.
        Return: None.
        """
        session = await self._repository.get_full(session_id)
        if session is None:
            raise NotFoundError("WorkoutSession", session_id)
        if session.user_id != user_id:
            raise ForbiddenError("You do not own this session.")

        await self._repository.delete(session)
        await self._repository.commit()
