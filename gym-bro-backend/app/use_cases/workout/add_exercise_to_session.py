"""Use case: add an exercise entry to an active workout session."""

import uuid

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.domain.models.workout import SessionExercise, SessionSet, WorkoutSession
from app.domain.ordering import resolve_order
from app.domain.schemas.workout import SessionExerciseCreate
from app.repositories.workout_repository import WorkoutRepository


class AddExerciseToSessionUseCase:
    """Appends a new exercise (with optional pre-defined sets) to an existing session."""

    def __init__(self, repository: WorkoutRepository) -> None:
        """
        Arg: repository - workout data-access object.
        Operation: stores the repository for use during execution.
        Return: AddExerciseToSessionUseCase instance.
        """
        self._repository = repository

    async def execute(
        self, session_id: uuid.UUID, data: SessionExerciseCreate, user_id: str
    ) -> WorkoutSession:
        """
        Arg: session_id - UUID of the target session; data - exercise input; user_id - requester.
        Operation: verifies ownership, builds the exercise and its sets, persists, and reloads.
                   Raises NotFoundError if the session does not exist.
                   Raises ForbiddenError if the requester does not own the session.
        Return: updated and fully loaded WorkoutSession entity.
        """
        session = await self._repository.get_full(session_id)
        if session is None:
            raise NotFoundError("WorkoutSession", session_id)
        if session.user_id != user_id:
            raise ForbiddenError("You do not own this session.")

        session_exercise = SessionExercise(
            session_id=session_id,
            exercise_id=data.exercise_id,
            order=resolve_order(data.order, len(session.exercises)),
            notes=data.notes,
        )
        for set_index, set_data in enumerate(data.sets):
            session_set = SessionSet(
                **set_data.model_dump(exclude={"order"}),
                order=resolve_order(set_data.order, set_index),
            )
            session_exercise.sets.append(session_set)

        self._repository.session.add(session_exercise)
        await self._repository.commit()
        return await self._repository.get_full(session_id)
