"""Use case: remove a set from a workout session."""

import uuid

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.domain.models.workout import WorkoutSession
from app.repositories.workout_repository import WorkoutRepository


class DeleteSetUseCase:
    """Removes a specific SessionSet from a workout session the user owns."""

    def __init__(self, repository: WorkoutRepository) -> None:
        """
        Arg: repository - workout data-access object.
        Operation: stores the repository for use during execution.
        Return: DeleteSetUseCase instance.
        """
        self._repository = repository

    async def execute(
        self, session_id: uuid.UUID, set_id: uuid.UUID, user_id: str
    ) -> WorkoutSession:
        """
        Arg: session_id - UUID of the session; set_id - UUID of the set; user_id - requester.
        Operation: verifies ownership, finds the set across all exercises, deletes it.
                   Raises NotFoundError for missing session or set.
                   Raises ForbiddenError if the requester does not own the session.
        Return: updated and fully loaded WorkoutSession entity.
        """
        session = await self._repository.get_full(session_id)
        if session is None:
            raise NotFoundError("WorkoutSession", session_id)
        if session.user_id != user_id:
            raise ForbiddenError("You do not own this session.")

        for exercise in session.exercises:
            for session_set in exercise.sets:
                if session_set.id == set_id:
                    await self._repository.session.delete(session_set)
                    await self._repository.commit()
                    return await self._repository.get_full(session_id)

        raise NotFoundError("SessionSet", set_id)
