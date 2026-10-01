"""Use case: start a new workout session."""

from datetime import UTC, datetime

from app.domain.models.workout import SessionExercise, SessionSet, WorkoutSession
from app.domain.ordering import resolve_order
from app.domain.schemas.workout import SessionExerciseCreate, WorkoutSessionCreate
from app.repositories.workout_repository import WorkoutRepository


class StartSessionUseCase:
    """Creates and persists a new workout session, optionally pre-populated from a template."""

    def __init__(self, repository: WorkoutRepository) -> None:
        """
        Arg: repository - workout data-access object.
        Operation: stores the repository for use during execution.
        Return: StartSessionUseCase instance.
        """
        self._repository = repository

    async def execute(self, data: WorkoutSessionCreate, user_id: str) -> WorkoutSession:
        """
        Arg: data - validated session creation input; user_id - owner's Keycloak subject.
        Operation: builds the session entity graph (session → exercises → sets),
                   records the start timestamp, persists, and reloads with full relations.
        Return: fully loaded WorkoutSession entity.
        """
        session = WorkoutSession(
            user_id=user_id,
            name=data.name,
            template_id=data.template_id,
            notes=data.notes,
            started_at=datetime.now(UTC),
        )
        for index, exercise_data in enumerate(data.exercises):
            session_exercise = self._build_session_exercise(exercise_data, index)
            session.exercises.append(session_exercise)

        saved = await self._repository.create(session)
        await self._repository.commit()
        return await self._repository.get_full(saved.id)

    @staticmethod
    def _build_session_exercise(
        exercise_data: SessionExerciseCreate, index: int
    ) -> SessionExercise:
        """
        Arg: exercise_data - input for a single exercise entry; index - display order.
        Operation: constructs SessionExercise and its child SessionSet entities.
        Return: SessionExercise entity (not yet persisted).
        """
        session_exercise = SessionExercise(
            exercise_id=exercise_data.exercise_id,
            order=resolve_order(exercise_data.order, index),
            notes=exercise_data.notes,
        )
        for set_index, set_data in enumerate(exercise_data.sets):
            session_set = SessionSet(
                **set_data.model_dump(exclude={"order"}),
                order=resolve_order(set_data.order, set_index),
            )
            session_exercise.sets.append(session_set)
        return session_exercise
