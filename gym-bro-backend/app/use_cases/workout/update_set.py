"""Use case: update an existing set within a workout session."""

import uuid
from datetime import UTC, datetime

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.domain.models.workout import SessionSet, WorkoutSession
from app.domain.schemas.workout import SessionSetUpdate
from app.repositories.workout_repository import WorkoutRepository


class UpdateSetUseCase:
    """Patches a SessionSet and records the completion timestamp when marked done."""

    def __init__(self, repository: WorkoutRepository) -> None:
        """
        Arg: repository - workout data-access object.
        Operation: stores the repository for use during execution.
        Return: UpdateSetUseCase instance.
        """
        self._repository = repository

    async def execute(
        self,
        session_id: uuid.UUID,
        set_id: uuid.UUID,
        data: SessionSetUpdate,
        user_id: str,
    ) -> WorkoutSession:
        """
        Arg: session_id - UUID of the session; set_id - UUID of the set; data - patch;
             user_id - requester.
        Operation: verifies ownership, locates the set across all exercises, applies the patch.
                   When completed is set to True, records completed_at as UTC now.
                   Raises NotFoundError for missing session or set.
                   Raises ForbiddenError if the requester does not own the session.
        Return: updated and fully loaded WorkoutSession entity.
        """
        session = await self._repository.get_full(session_id)
        if session is None:
            raise NotFoundError("WorkoutSession", session_id)
        if session.user_id != user_id:
            raise ForbiddenError("You do not own this session.")

        target_set = self._find_set(session, set_id)
        if target_set is None:
            raise NotFoundError("SessionSet", set_id)

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(target_set, field, value)

        if data.completed:
            target_set.completed_at = datetime.now(UTC)

        await self._repository.commit()
        return await self._repository.get_full(session_id)

    @staticmethod
    def _find_set(session: WorkoutSession, set_id: uuid.UUID) -> SessionSet | None:
        """
        Arg: session - the loaded session entity; set_id - UUID to search for.
        Operation: iterates all exercises and their sets to locate the matching SessionSet.
        Return: the matching SessionSet, or None if not found.
        """
        for exercise in session.exercises:
            for session_set in exercise.sets:
                if session_set.id == set_id:
                    return session_set
        return None
