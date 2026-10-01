"""Use case: compute the overall training progress overview for a user."""

from collections import defaultdict
from datetime import UTC, date, datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.calculations import calculate_streaks, epley_one_rep_max
from app.domain.models.exercise import Exercise
from app.domain.models.workout import SessionExercise, SessionSet, WorkoutSession
from app.domain.schemas.progress import (
    PersonalRecord,
    ProgressOverview,
    VolumePoint,
    WorkoutFrequency,
)


class GetProgressOverviewUseCase:
    """Aggregates workout history into a summary overview with streaks, volume, and PRs."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Arg: db - async SQLAlchemy session for running aggregate queries.
        Operation: stores the session for use during execution.
        Return: GetProgressOverviewUseCase instance.
        """
        self._db = db

    async def execute(self, user_id: str) -> ProgressOverview:
        """
        Arg: user_id - Keycloak subject of the requesting user.
        Operation: queries completed sessions and sets, computes streaks, volume by day,
                   personal records, and weekly training frequency.
        Return: ProgressOverview schema populated with aggregated statistics.
        """
        workout_dates = await self._load_workout_dates(user_id)
        set_rows = await self._load_completed_sets(user_id)

        total_sets, total_volume, volume_by_day, sets_by_day = self._aggregate_sets(set_rows)
        current_streak, longest_streak = calculate_streaks(workout_dates)
        personal_records = self._compute_personal_records(set_rows)
        recent_volume = self._build_volume_points(volume_by_day, sets_by_day)
        weekly_frequency = self._build_weekly_frequency(workout_dates)

        return ProgressOverview(
            # One entry per completed session — de-duplicating here would under-count
            # days on which more than one workout was finished.
            total_workouts=len(workout_dates),
            total_volume=total_volume,
            total_sets=total_sets,
            current_streak=current_streak,
            longest_streak=longest_streak,
            personal_records=personal_records[:10],
            weekly_frequency=weekly_frequency,
            recent_volume=recent_volume,
        )

    async def _load_workout_dates(self, user_id: str) -> list[date]:
        """
        Arg: user_id - Keycloak subject.
        Operation: fetches started_at timestamps for all completed sessions.
        Return: list of dates on which workouts were completed.
        """
        query = select(WorkoutSession.started_at).where(
            and_(
                WorkoutSession.user_id == user_id,
                WorkoutSession.completed_at.isnot(None),
            )
        )
        result = await self._db.execute(query)
        return [row[0].date() for row in result]

    async def _load_completed_sets(self, user_id: str) -> list[tuple]:
        """
        Arg: user_id - Keycloak subject.
        Operation: joins sets → exercises → sessions and returns completed sets with metadata.
        Return: list of tuples (SessionSet, exercise_id, exercise_name, started_at).
        """
        query = (
            select(
                SessionSet,
                SessionExercise.exercise_id,
                Exercise.name,
                WorkoutSession.started_at,
            )
            .join(SessionExercise, SessionSet.session_exercise_id == SessionExercise.id)
            .join(WorkoutSession, SessionExercise.session_id == WorkoutSession.id)
            .join(Exercise, SessionExercise.exercise_id == Exercise.id)
            .where(
                and_(
                    WorkoutSession.user_id == user_id,
                    WorkoutSession.completed_at.isnot(None),
                    SessionSet.completed.is_(True),
                )
            )
        )
        result = await self._db.execute(query)
        return list(result)

    @staticmethod
    def _aggregate_sets(
        set_rows: list[tuple],
    ) -> tuple[int, float, dict[date, float], dict[date, int]]:
        """
        Arg: set_rows - rows from _load_completed_sets.
        Operation: counts sets, sums volume, and groups both by calendar date.
        Return: tuple of (total_sets, total_volume, volume_by_day, sets_by_day).
        """
        total_sets = 0
        total_volume = 0.0
        volume_by_day: dict[date, float] = defaultdict(float)
        sets_by_day: dict[date, int] = defaultdict(int)

        for row in set_rows:
            session_set, _, __, started_at = row
            total_sets += 1
            volume = (session_set.weight or 0.0) * (session_set.reps or 1)
            total_volume += volume
            day = started_at.date()
            volume_by_day[day] += volume
            sets_by_day[day] += 1

        return total_sets, total_volume, dict(volume_by_day), dict(sets_by_day)

    @staticmethod
    def _compute_personal_records(set_rows: list[tuple]) -> list[PersonalRecord]:
        """
        Arg: set_rows - rows from _load_completed_sets.
        Operation: finds the set with the highest estimated 1RM per exercise.
        Return: list of PersonalRecord schemas sorted by estimated 1RM descending.
        """
        import uuid as _uuid

        best: dict[_uuid.UUID, PersonalRecord] = {}
        for row in set_rows:
            session_set, exercise_id, exercise_name, started_at = row
            if session_set.weight is None or session_set.reps is None:
                continue
            estimated = epley_one_rep_max(session_set.weight, session_set.reps)
            if exercise_id not in best or estimated > best[exercise_id].estimated_1rm:
                best[exercise_id] = PersonalRecord(
                    exercise_id=exercise_id,
                    exercise_name=exercise_name,
                    weight=session_set.weight,
                    reps=session_set.reps,
                    achieved_at=started_at,
                    estimated_1rm=estimated,
                )
        return sorted(best.values(), key=lambda r: r.estimated_1rm, reverse=True)

    @staticmethod
    def _build_volume_points(
        volume_by_day: dict[date, float], sets_by_day: dict[date, int]
    ) -> list[VolumePoint]:
        """
        Arg: volume_by_day - total volume per date; sets_by_day - set count per date.
        Operation: takes the 30 most recent days and converts them to VolumePoint schemas.
        Return: list of VolumePoint schemas ordered chronologically.
        """
        recent_days = sorted(volume_by_day.keys())[-30:]
        return [
            VolumePoint(
                date=datetime.combine(day, datetime.min.time(), tzinfo=UTC),
                total_volume=volume_by_day[day],
                total_sets=sets_by_day.get(day, 0),
            )
            for day in recent_days
        ]

    @staticmethod
    def _build_weekly_frequency(workout_dates: list[date]) -> list[WorkoutFrequency]:
        """
        Arg: workout_dates - all dates on which workouts were completed.
        Operation: groups dates by ISO week (Monday as start) and counts sessions per week.
                   Returns the 12 most recent weeks.
        Return: list of WorkoutFrequency schemas ordered chronologically.
        """
        from datetime import timedelta

        weekly: dict[date, int] = defaultdict(int)
        for day in workout_dates:
            monday = day - timedelta(days=day.weekday())
            weekly[monday] += 1

        return [
            WorkoutFrequency(date=monday, count=count)
            for monday, count in sorted(weekly.items())[-12:]
        ]
