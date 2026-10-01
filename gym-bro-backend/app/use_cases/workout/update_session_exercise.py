"""Use case: swap the movement on a session entry, or note something about it."""

import uuid

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.domain.models.workout import WorkoutSession
from app.domain.schemas.workout import SessionExerciseUpdate
from app.repositories.workout_repository import WorkoutRepository


class UpdateSessionExerciseUseCase:
    """Points a session entry at a different exercise, keeping the sets already logged."""

    def __init__(self, repository: WorkoutRepository) -> None:
        """
        Arg: repository - workout data-access object.
        Operation: stores the repository for use during execution.
        Return: UpdateSessionExerciseUseCase instance.
        """
        self._repository = repository

    async def execute(
        self,
        session_id: uuid.UUID,
        session_exercise_id: uuid.UUID,
        data: SessionExerciseUpdate,
        user_id: str,
    ) -> WorkoutSession:
        """
        Arg: session_id - UUID of the session; session_exercise_id - the entry to change;
             data - the fields to apply; user_id - requester.
        Operation: verifies ownership and applies the supplied fields. The sets stay where they
                   are: swapping a barbell movement for its dumbbell version mid-workout should
                   not throw away the sets already done.
                   Raises NotFoundError for a missing session or entry.
                   Raises ForbiddenError if the requester does not own the session.
        Return: updated and fully loaded WorkoutSession entity.
        """
        session = await self._repository.get_full(session_id)
        if session is None:
            raise NotFoundError("WorkoutSession", session_id)
        if session.user_id != user_id:
            raise ForbiddenError("You do not own this session.")

        entry = next((e for e in session.exercises if e.id == session_exercise_id), None)
        if entry is None:
            raise NotFoundError("SessionExercise", session_exercise_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(entry, field, value)

        await self._repository.commit()
        return await self._repository.get_full(session_id)
