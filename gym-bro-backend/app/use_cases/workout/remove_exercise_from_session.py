"""Use case: take an exercise out of a workout session."""

import uuid

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.domain.models.workout import WorkoutSession
from app.repositories.workout_repository import WorkoutRepository


class RemoveExerciseFromSessionUseCase:
    """Removes one SessionExercise, and its sets with it, from a session the user owns."""

    def __init__(self, repository: WorkoutRepository) -> None:
        """
        Arg: repository - workout data-access object.
        Operation: stores the repository for use during execution.
        Return: RemoveExerciseFromSessionUseCase instance.
        """
        self._repository = repository

    async def execute(
        self, session_id: uuid.UUID, session_exercise_id: uuid.UUID, user_id: str
    ) -> WorkoutSession:
        """
        Arg: session_id - UUID of the session; session_exercise_id - the entry to remove;
             user_id - requester.
        Operation: verifies ownership, deletes the entry and closes the gap it leaves in the
                   ordering, so the remaining exercises stay numbered 0..n-1.
                   Raises NotFoundError for a missing session or entry.
                   Raises ForbiddenError if the requester does not own the session.
        Return: updated and fully loaded WorkoutSession entity.
        """
        session = await self._repository.get_full(session_id)
        if session is None:
            raise NotFoundError("WorkoutSession", session_id)
        if session.user_id != user_id:
            raise ForbiddenError("You do not own this session.")

        doomed = next((e for e in session.exercises if e.id == session_exercise_id), None)
        if doomed is None:
            raise NotFoundError("SessionExercise", session_exercise_id)

        await self._repository.session.delete(doomed)
        remaining = [e for e in session.exercises if e.id != session_exercise_id]
        for position, exercise in enumerate(remaining):
            exercise.order = position

        await self._repository.commit()
        return await self._repository.get_full(session_id)
