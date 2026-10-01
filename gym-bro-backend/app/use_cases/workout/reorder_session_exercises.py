"""Use case: put a session's exercises into a new order."""

import uuid

from app.domain.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.domain.models.workout import WorkoutSession
from app.repositories.workout_repository import WorkoutRepository


class ReorderSessionExercisesUseCase:
    """Renumbers a session's exercises to match a client-supplied order."""

    def __init__(self, repository: WorkoutRepository) -> None:
        """
        Arg: repository - workout data-access object.
        Operation: stores the repository for use during execution.
        Return: ReorderSessionExercisesUseCase instance.
        """
        self._repository = repository

    async def execute(
        self, session_id: uuid.UUID, exercise_ids: list[uuid.UUID], user_id: str
    ) -> WorkoutSession:
        """
        Arg: session_id - UUID of the session; exercise_ids - every SessionExercise id in the
             order they should appear; user_id - requester.
        Operation: verifies ownership, then renumbers. The list must name each of the session's
                   exercises exactly once — a partial list would leave duplicate order values
                   and an ordering that depends on which row the database returns first.
                   Raises NotFoundError for a missing session.
                   Raises ForbiddenError if the requester does not own the session.
                   Raises ValidationError if the list does not match the session's exercises.
        Return: updated and fully loaded WorkoutSession entity.
        """
        session = await self._repository.get_full(session_id)
        if session is None:
            raise NotFoundError("WorkoutSession", session_id)
        if session.user_id != user_id:
            raise ForbiddenError("You do not own this session.")

        by_id = {exercise.id: exercise for exercise in session.exercises}
        if sorted(exercise_ids, key=str) != sorted(by_id, key=str):
            raise ValidationError(
                "The order must list each of the session's exercises exactly once."
            )

        for position, exercise_id in enumerate(exercise_ids):
            by_id[exercise_id].order = position

        await self._repository.commit()
        return await self._repository.get_full(session_id)
