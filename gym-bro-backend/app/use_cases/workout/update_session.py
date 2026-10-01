"""Use case: update scalar fields on a workout session."""

import uuid

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.domain.models.workout import WorkoutSession
from app.domain.schemas.workout import WorkoutSessionUpdate
from app.repositories.workout_repository import WorkoutRepository


class UpdateSessionUseCase:
    """Updates mutable metadata (name, notes) on a workout session."""

    def __init__(self, repository: WorkoutRepository) -> None:
        """
        Arg: repository - workout data-access object.
        Operation: stores the repository for use during execution.
        Return: UpdateSessionUseCase instance.
        """
        self._repository = repository

    async def execute(
        self, session_id: uuid.UUID, data: WorkoutSessionUpdate, user_id: str
    ) -> WorkoutSession:
        """
        Arg: session_id - UUID of the session; data - fields to patch; user_id - requester.
        Operation: loads the session, verifies ownership, applies the patch, and commits.
                   Raises NotFoundError if the session does not exist.
                   Raises ForbiddenError if the requester does not own the session.
        Return: updated and fully loaded WorkoutSession entity.
        """
        session = await self._repository.get_full(session_id)
        if session is None:
            raise NotFoundError("WorkoutSession", session_id)
        if session.user_id != user_id:
            raise ForbiddenError("You do not own this session.")

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(session, field, value)

        await self._repository.commit()
        return await self._repository.get_full(session_id)
