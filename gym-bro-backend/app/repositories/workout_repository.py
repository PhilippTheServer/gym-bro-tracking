"""Repository for WorkoutSession entities."""

import uuid
from datetime import datetime

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import selectinload

from app.domain.models.workout import SessionExercise, WorkoutSession
from app.repositories.base import BaseRepository


class WorkoutRepository(BaseRepository[WorkoutSession]):
    """Data-access object for the workout_sessions table."""

    model = WorkoutSession

    async def list_for_user(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[WorkoutSession]:
        """
        Arg: user_id - owner's Keycloak subject; limit - page size; offset - start index.
        Operation: selects completed sessions (completed_at is NOT NULL), newest first.
                   Exercises, their exercise entity and their sets are all eager-loaded,
                   because the response schema serialises them and a lazy load outside
                   the async session's greenlet context would fail.
        Return: list of WorkoutSession entities.
        """
        statement = (
            select(WorkoutSession)
            .where(
                and_(
                    WorkoutSession.user_id == user_id,
                    WorkoutSession.completed_at.isnot(None),
                )
            )
            .options(
                selectinload(WorkoutSession.exercises).selectinload(SessionExercise.exercise),
                selectinload(WorkoutSession.exercises).selectinload(SessionExercise.sets),
            )
            .order_by(desc(WorkoutSession.started_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_completed_since(
        self, user_id: str, completed_after: datetime, limit: int = 100, offset: int = 0
    ) -> list[WorkoutSession]:
        """
        Arg: user_id - owner's Keycloak subject; completed_after - exclusive lower bound on
             completion time; limit - page size; offset - start index.
        Operation: selects this user's completed sessions finished strictly after the
                   cutoff, oldest first, with the same eager loads as list_for_user so the
                   caller receives full exercise and set detail in one round trip.
        Return: list of WorkoutSession entities ordered by completed_at then id ascending.
        """
        statement = (
            select(WorkoutSession)
            .where(
                and_(
                    WorkoutSession.user_id == user_id,
                    WorkoutSession.completed_at.isnot(None),
                    WorkoutSession.completed_at > completed_after,
                )
            )
            .options(
                selectinload(WorkoutSession.exercises).selectinload(SessionExercise.exercise),
                selectinload(WorkoutSession.exercises).selectinload(SessionExercise.sets),
            )
            .order_by(WorkoutSession.completed_at.asc(), WorkoutSession.id.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_full(self, id: uuid.UUID) -> WorkoutSession | None:
        """
        Arg: id - UUID of the session to load.
        Operation: loads the session with all exercises, their exercise entity, and all sets
                   via eager loading.
        Return: fully loaded WorkoutSession entity, or None if not found.
        """
        statement = (
            select(WorkoutSession)
            .where(WorkoutSession.id == id)
            .options(
                selectinload(WorkoutSession.exercises).selectinload(SessionExercise.exercise),
                selectinload(WorkoutSession.exercises).selectinload(SessionExercise.sets),
            )
            # populate_existing: these reloads run right after a write, and the
            # instances are still in the session's identity map. Without it their
            # already-loaded collections would be reused and the caller would get
            # back the pre-write state.
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_exercise_history(
        self, user_id: str, exercise_id: uuid.UUID, limit: int
    ) -> list[SessionExercise]:
        """
        Arg: user_id - owner's Keycloak subject; exercise_id - the exercise to look up;
             limit - how many recent entries to return.
        Operation: selects this user's finished sessions containing the exercise, newest first,
                   with their sets eager-loaded.
        Return: list of SessionExercise entities, most recent session first.
        """
        statement = (
            select(SessionExercise)
            .join(WorkoutSession, WorkoutSession.id == SessionExercise.session_id)
            .where(
                and_(
                    WorkoutSession.user_id == user_id,
                    WorkoutSession.completed_at.isnot(None),
                    SessionExercise.exercise_id == exercise_id,
                )
            )
            # The session is eager-loaded too: the response carries when the performance
            # happened, and a lazy load there would leave the async greenlet context.
            .options(
                selectinload(SessionExercise.sets),
                selectinload(SessionExercise.session),
            )
            .order_by(desc(WorkoutSession.completed_at))
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_active(self, user_id: str) -> WorkoutSession | None:
        """
        Arg: user_id - Keycloak subject of the requesting user.
        Operation: finds the most recent session where completed_at is NULL,
                   loaded with full exercise and set relationships.
        Return: the active WorkoutSession entity, or None if no session is in progress.
        """
        statement = (
            select(WorkoutSession)
            .where(
                and_(
                    WorkoutSession.user_id == user_id,
                    WorkoutSession.completed_at.is_(None),
                )
            )
            .options(
                selectinload(WorkoutSession.exercises).selectinload(SessionExercise.exercise),
                selectinload(WorkoutSession.exercises).selectinload(SessionExercise.sets),
            )
            .order_by(desc(WorkoutSession.started_at))
            .limit(1)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
