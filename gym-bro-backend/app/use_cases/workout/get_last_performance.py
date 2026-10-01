"""Use case: what this user last did for a given exercise."""

import uuid

from app.domain.models.workout import SessionExercise
from app.repositories.workout_repository import WorkoutRepository

# How far back to look for a session that actually logged something. A handful is enough:
# an exercise opened and abandoned several sessions running has no useful last performance.
RECENT_SESSIONS_CONSIDERED = 5


class GetLastPerformanceUseCase:
    """Finds the most recent completed sets for one exercise, to prefill the next ones."""

    def __init__(self, repository: WorkoutRepository) -> None:
        """
        Arg: repository - workout data-access object.
        Operation: stores the repository for use during execution.
        Return: GetLastPerformanceUseCase instance.
        """
        self._repository = repository

    async def execute(self, exercise_id: uuid.UUID, user_id: str) -> SessionExercise | None:
        """
        Arg: exercise_id - the exercise to look up; user_id - whose history to search.
        Operation: walks back through the user's finished sessions and returns the first entry
                   for this exercise that has at least one completed set. An entry where every
                   set was left unticked is skipped — it records an intention, not a lift.
        Return: the SessionExercise holding that performance, or None if there is none.
        """
        candidates = await self._repository.list_exercise_history(
            user_id, exercise_id, RECENT_SESSIONS_CONSIDERED
        )
        for entry in candidates:
            if any(session_set.completed for session_set in entry.sets):
                return entry
        return None
