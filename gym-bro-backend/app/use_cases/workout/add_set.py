"""Use case: add a new set to an exercise within a workout session."""

import uuid

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.domain.models.workout import SessionSet, WorkoutSession
from app.domain.ordering import resolve_order
from app.domain.schemas.workout import SessionSetCreate
from app.repositories.workout_repository import WorkoutRepository


class AddSetUseCase:
    """Appends a set to a specific exercise entry inside an active workout session."""

    def __init__(self, repository: WorkoutRepository) -> None:
        """
        Arg: repository - workout data-access object.
        Operation: stores the repository for use during execution.
        Return: AddSetUseCase instance.
        """
        self._repository = repository

    async def execute(
        self,
        session_id: uuid.UUID,
        exercise_id: uuid.UUID,
        data: SessionSetCreate,
        user_id: str,
    ) -> WorkoutSession:
        """
        Arg: session_id - UUID of the session; exercise_id - UUID of the session exercise;
             data - set creation input; user_id - requester's Keycloak subject.
        Operation: verifies ownership and that the exercise belongs to the session,
                   then appends a new SessionSet and reloads.
                   Raises NotFoundError if the session or exercise entry is absent.
                   Raises ForbiddenError if the requester does not own the session.
        Return: updated and fully loaded WorkoutSession entity.
        """
        session = await self._repository.get_full(session_id)
        if session is None:
            raise NotFoundError("WorkoutSession", session_id)
        if session.user_id != user_id:
            raise ForbiddenError("You do not own this session.")

        session_exercise = next((ex for ex in session.exercises if ex.id == exercise_id), None)
        if session_exercise is None:
            raise NotFoundError("SessionExercise", exercise_id)

        new_set = SessionSet(
            **data.model_dump(exclude={"order"}),
            # Without an explicit order the set lands at the end of the exercise.
            order=resolve_order(data.order, len(session_exercise.sets)),
            session_exercise_id=session_exercise.id,
        )
        self._repository.session.add(new_set)
        await self._repository.commit()
        return await self._repository.get_full(session_id)
