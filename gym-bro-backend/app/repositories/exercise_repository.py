"""Repository for Exercise entities."""

from sqlalchemy import func, or_, select

from app.domain.models.exercise import Exercise
from app.domain.models.workout import SessionExercise, WorkoutSession
from app.repositories.base import BaseRepository


class ExerciseRepository(BaseRepository[Exercise]):
    """Data-access object for the exercises table."""

    model = Exercise

    async def search(
        self,
        query: str,
        user_id: str | None = None,
        muscle_group: str | None = None,
        primary_muscle: str | None = None,
        equipment: str | None = None,
        category: str | None = None,
    ) -> list[Exercise]:
        """
        Arg: query - partial name to filter by (empty string returns all); user_id - owner filter;
             muscle_group, primary_muscle, equipment, category - optional exact-match filters.
        Operation: selects exercises that are either global (is_custom=False) or owned by the user,
                   narrowing by each filter that was supplied.
        Return: list of Exercise entities ordered by name.
        """
        statement = select(Exercise).where(
            or_(
                Exercise.is_custom.is_(False),
                Exercise.created_by == user_id,
            )
        )
        if query:
            statement = statement.where(Exercise.name.ilike(f"%{query}%"))
        if muscle_group:
            statement = statement.where(Exercise.muscle_group == muscle_group)
        if primary_muscle:
            statement = statement.where(Exercise.primary_muscle == primary_muscle)
        if equipment:
            statement = statement.where(Exercise.equipment == equipment)
        if category:
            statement = statement.where(Exercise.category == category)
        statement = statement.order_by(Exercise.name)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_built_in(self) -> list[Exercise]:
        """
        Arg: none.
        Operation: selects every exercise that came from the catalogue rather than from a user.
        Return: list of built-in Exercise entities.
        """
        statement = select(Exercise).where(Exercise.is_custom.is_(False))
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_for_user(self, user_id: str) -> list[Exercise]:
        """
        Arg: user_id - Keycloak subject of the requesting user.
        Operation: selects all global and user-owned exercises, ordered by muscle group then name.
        Return: list of Exercise entities.
        """
        statement = (
            select(Exercise)
            .where(
                or_(
                    Exercise.is_custom.is_(False),
                    Exercise.created_by == user_id,
                )
            )
            .order_by(Exercise.muscle_group, Exercise.name)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_recently_used(self, user_id: str, limit: int) -> list[Exercise]:
        """
        Arg: user_id - Keycloak subject of the requesting user; limit - maximum rows to return.
        Operation: joins the exercises onto the user's own sessions and orders them by the most
                   recent session they appear in.
        Return: list of Exercise entities, most recently trained first.
        """
        statement = (
            select(Exercise)
            .join(SessionExercise, SessionExercise.exercise_id == Exercise.id)
            .join(WorkoutSession, WorkoutSession.id == SessionExercise.session_id)
            .where(WorkoutSession.user_id == user_id)
            .group_by(Exercise.id)
            .order_by(func.max(WorkoutSession.started_at).desc())
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Exercise | None:
        """
        Arg: name - exact exercise name to look up.
        Operation: queries for a single exercise with a matching name.
        Return: the Exercise entity if found, otherwise None.
        """
        statement = select(Exercise).where(Exercise.name == name)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
