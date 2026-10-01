"""Use case: compute per-exercise progress history for a user."""

import uuid
from collections import defaultdict
from datetime import date, datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.calculations import epley_one_rep_max
from app.domain.exceptions import NotFoundError
from app.domain.models.exercise import Exercise
from app.domain.models.workout import SessionExercise, SessionSet, WorkoutSession
from app.domain.schemas.progress import ExerciseProgress, ExerciseProgressPoint


class GetExerciseProgressUseCase:
    """Builds a per-session progress history for a single exercise."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Arg: db - async SQLAlchemy session for running aggregate queries.
        Operation: stores the session for use during execution.
        Return: GetExerciseProgressUseCase instance.
        """
        self._db = db

    async def execute(self, user_id: str, exercise_id: uuid.UUID) -> ExerciseProgress:
        """
        Arg: user_id - Keycloak subject; exercise_id - UUID of the exercise.
        Operation: loads completed sets for the exercise across all sessions,
                   groups them by calendar date, and builds progress data points.
                   Raises NotFoundError if the exercise does not exist.
        Return: ExerciseProgress schema with a chronological list of progress points.
        """
        exercise = await self._load_exercise(exercise_id)
        set_rows = await self._load_sets_for_exercise(user_id, exercise_id)
        points = self._build_progress_points(set_rows)

        return ExerciseProgress(
            exercise_id=exercise_id,
            exercise_name=exercise.name,
            muscle_group=exercise.muscle_group,
            points=points,
        )

    async def _load_exercise(self, exercise_id: uuid.UUID) -> Exercise:
        """
        Arg: exercise_id - UUID of the exercise to load.
        Operation: fetches the Exercise entity from the database.
                   Raises NotFoundError if absent.
        Return: the Exercise entity.
        """
        result = await self._db.execute(select(Exercise).where(Exercise.id == exercise_id))
        exercise = result.scalar_one_or_none()
        if exercise is None:
            raise NotFoundError("Exercise", exercise_id)
        return exercise

    async def _load_sets_for_exercise(self, user_id: str, exercise_id: uuid.UUID) -> list[tuple]:
        """
        Arg: user_id - Keycloak subject; exercise_id - target exercise UUID.
        Operation: joins sets → session exercises → sessions for the given exercise,
                   filtering to completed sets in completed sessions owned by the user.
        Return: list of tuples (SessionSet, started_at) ordered chronologically.
        """
        query = (
            select(SessionSet, WorkoutSession.started_at)
            .join(SessionExercise, SessionSet.session_exercise_id == SessionExercise.id)
            .join(WorkoutSession, SessionExercise.session_id == WorkoutSession.id)
            .where(
                and_(
                    WorkoutSession.user_id == user_id,
                    SessionExercise.exercise_id == exercise_id,
                    WorkoutSession.completed_at.isnot(None),
                    SessionSet.completed.is_(True),
                )
            )
            .order_by(WorkoutSession.started_at)
        )
        result = await self._db.execute(query)
        return list(result)

    @staticmethod
    def _build_progress_points(set_rows: list[tuple]) -> list[ExerciseProgressPoint]:
        """
        Arg: set_rows - rows from _load_sets_for_exercise.
        Operation: groups sets by calendar date, then computes max weight, total volume,
                   max reps, and estimated 1RM per day.
        Return: chronologically ordered list of ExerciseProgressPoint schemas.
        """
        by_day: dict[date, list[SessionSet]] = defaultdict(list)
        day_timestamp: dict[date, datetime] = {}

        for row in set_rows:
            session_set, started_at = row
            day = started_at.date()
            by_day[day].append(session_set)
            day_timestamp[day] = started_at

        points: list[ExerciseProgressPoint] = []
        for day in sorted(by_day.keys()):
            sets = by_day[day]
            weighted_sets = [s for s in sets if s.weight and s.reps]
            if not weighted_sets:
                continue

            max_weight = max(s.weight for s in weighted_sets)
            best_set = max(weighted_sets, key=lambda s: epley_one_rep_max(s.weight, s.reps))

            points.append(
                ExerciseProgressPoint(
                    date=day_timestamp[day],
                    max_weight=max_weight,
                    total_volume=sum((s.weight or 0.0) * (s.reps or 1) for s in sets),
                    max_reps=max((s.reps or 0) for s in sets),
                    estimated_1rm=epley_one_rep_max(best_set.weight, best_set.reps),
                )
            )
        return points
