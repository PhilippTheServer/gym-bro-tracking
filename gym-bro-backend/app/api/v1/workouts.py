"""Workout session endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    get_add_exercise_to_session_use_case,
    get_add_set_use_case,
    get_delete_session_use_case,
    get_delete_set_use_case,
    get_finish_session_use_case,
    get_get_active_session_use_case,
    get_get_session_use_case,
    get_list_sessions_use_case,
    get_remove_exercise_from_session_use_case,
    get_reorder_session_exercises_use_case,
    get_start_session_use_case,
    get_update_session_exercise_use_case,
    get_update_session_use_case,
    get_update_set_use_case,
)
from app.core.security import CurrentUser
from app.domain.schemas.workout import (
    SessionExerciseCreate,
    SessionExerciseReorder,
    SessionExerciseUpdate,
    SessionSetCreate,
    SessionSetUpdate,
    WorkoutSessionCreate,
    WorkoutSessionOut,
    WorkoutSessionUpdate,
)
from app.use_cases.workout.add_exercise_to_session import AddExerciseToSessionUseCase
from app.use_cases.workout.add_set import AddSetUseCase
from app.use_cases.workout.delete_session import DeleteSessionUseCase
from app.use_cases.workout.delete_set import DeleteSetUseCase
from app.use_cases.workout.finish_session import FinishSessionUseCase
from app.use_cases.workout.get_active_session import GetActiveSessionUseCase
from app.use_cases.workout.get_session import GetSessionUseCase
from app.use_cases.workout.list_sessions import ListSessionsUseCase
from app.use_cases.workout.remove_exercise_from_session import RemoveExerciseFromSessionUseCase
from app.use_cases.workout.reorder_session_exercises import ReorderSessionExercisesUseCase
from app.use_cases.workout.start_session import StartSessionUseCase
from app.use_cases.workout.update_session import UpdateSessionUseCase
from app.use_cases.workout.update_session_exercise import UpdateSessionExerciseUseCase
from app.use_cases.workout.update_set import UpdateSetUseCase

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("", response_model=list[WorkoutSessionOut])
async def list_sessions(
    user: CurrentUser,
    use_case: Annotated[ListSessionsUseCase, Depends(get_list_sessions_use_case)],
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[WorkoutSessionOut]:
    """
    Arg: user - authenticated user; limit/offset - pagination params; use_case - injected.
    Operation: delegates to ListSessionsUseCase and serialises each result.
    Return: list of WorkoutSessionOut schemas.
    """
    sessions = await use_case.execute(user["sub"], limit, offset)
    return [WorkoutSessionOut.model_validate(s) for s in sessions]


@router.get("/active", response_model=WorkoutSessionOut | None)
async def get_active_session(
    user: CurrentUser,
    use_case: Annotated[GetActiveSessionUseCase, Depends(get_get_active_session_use_case)],
) -> WorkoutSessionOut | None:
    """
    Arg: user - authenticated user; use_case - injected use case.
    Operation: delegates to GetActiveSessionUseCase; returns None when no session is active.
    Return: WorkoutSessionOut schema or None.
    """
    session = await use_case.execute(user["sub"])
    return WorkoutSessionOut.model_validate(session) if session else None


@router.get("/{session_id}", response_model=WorkoutSessionOut)
async def get_session(
    session_id: uuid.UUID,
    user: CurrentUser,
    use_case: Annotated[GetSessionUseCase, Depends(get_get_session_use_case)],
) -> WorkoutSessionOut:
    """
    Arg: session_id - UUID path param; user - authenticated user; use_case - injected.
    Operation: delegates to GetSessionUseCase and serialises the result.
    Return: WorkoutSessionOut schema with full exercise and set detail.
    """
    session = await use_case.execute(session_id, user["sub"])
    return WorkoutSessionOut.model_validate(session)


@router.post("", response_model=WorkoutSessionOut, status_code=201)
async def start_session(
    payload: WorkoutSessionCreate,
    user: CurrentUser,
    use_case: Annotated[StartSessionUseCase, Depends(get_start_session_use_case)],
) -> WorkoutSessionOut:
    """
    Arg: payload - session creation body; user - authenticated user; use_case - injected.
    Operation: delegates to StartSessionUseCase and serialises the result.
    Return: WorkoutSessionOut schema for the newly started session.
    """
    session = await use_case.execute(payload, user["sub"])
    return WorkoutSessionOut.model_validate(session)


@router.patch("/{session_id}", response_model=WorkoutSessionOut)
async def update_session(
    session_id: uuid.UUID,
    payload: WorkoutSessionUpdate,
    user: CurrentUser,
    use_case: Annotated[UpdateSessionUseCase, Depends(get_update_session_use_case)],
) -> WorkoutSessionOut:
    """
    Arg: session_id - UUID path param; payload - update body; user - authenticated user.
    Operation: delegates to UpdateSessionUseCase and serialises the result.
    Return: WorkoutSessionOut schema for the updated session.
    """
    session = await use_case.execute(session_id, payload, user["sub"])
    return WorkoutSessionOut.model_validate(session)


@router.post("/{session_id}/finish", response_model=WorkoutSessionOut)
async def finish_session(
    session_id: uuid.UUID,
    user: CurrentUser,
    use_case: Annotated[FinishSessionUseCase, Depends(get_finish_session_use_case)],
) -> WorkoutSessionOut:
    """
    Arg: session_id - UUID path param; user - authenticated user; use_case - injected.
    Operation: delegates to FinishSessionUseCase; records completion timestamp.
    Return: WorkoutSessionOut schema with completed_at populated.
    """
    session = await use_case.execute(session_id, user["sub"])
    return WorkoutSessionOut.model_validate(session)


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: uuid.UUID,
    user: CurrentUser,
    use_case: Annotated[DeleteSessionUseCase, Depends(get_delete_session_use_case)],
) -> None:
    """
    Arg: session_id - UUID path param; user - authenticated user; use_case - injected.
    Operation: delegates to DeleteSessionUseCase; returns 204 on success.
    Return: None.
    """
    await use_case.execute(session_id, user["sub"])


@router.post("/{session_id}/exercises", response_model=WorkoutSessionOut)
async def add_exercise(
    session_id: uuid.UUID,
    payload: SessionExerciseCreate,
    user: CurrentUser,
    use_case: Annotated[AddExerciseToSessionUseCase, Depends(get_add_exercise_to_session_use_case)],
) -> WorkoutSessionOut:
    """
    Arg: session_id - UUID path param; payload - exercise input; user - authenticated user.
    Operation: delegates to AddExerciseToSessionUseCase and serialises the updated session.
    Return: WorkoutSessionOut schema reflecting the new exercise.
    """
    session = await use_case.execute(session_id, payload, user["sub"])
    return WorkoutSessionOut.model_validate(session)


# Declared before /{session_id}/exercises/{session_exercise_id} so that "reorder" is not
# parsed as a UUID path parameter.
@router.patch("/{session_id}/exercises/reorder", response_model=WorkoutSessionOut)
async def reorder_exercises(
    session_id: uuid.UUID,
    payload: SessionExerciseReorder,
    user: CurrentUser,
    use_case: Annotated[
        ReorderSessionExercisesUseCase, Depends(get_reorder_session_exercises_use_case)
    ],
) -> WorkoutSessionOut:
    """
    Arg: session_id - UUID path param; payload - the exercises in their new order;
         user - authenticated user; use_case - injected.
    Operation: delegates to ReorderSessionExercisesUseCase and serialises the updated session.
    Return: WorkoutSessionOut schema in the new order.
    """
    session = await use_case.execute(session_id, payload.exercise_ids, user["sub"])
    return WorkoutSessionOut.model_validate(session)


@router.patch("/{session_id}/exercises/{session_exercise_id}", response_model=WorkoutSessionOut)
async def update_session_exercise(
    session_id: uuid.UUID,
    session_exercise_id: uuid.UUID,
    payload: SessionExerciseUpdate,
    user: CurrentUser,
    use_case: Annotated[
        UpdateSessionExerciseUseCase, Depends(get_update_session_exercise_use_case)
    ],
) -> WorkoutSessionOut:
    """
    Arg: session_id/session_exercise_id - UUID path params; payload - patch body;
         user - authenticated user; use_case - injected.
    Operation: delegates to UpdateSessionExerciseUseCase and serialises the updated session.
    Return: WorkoutSessionOut schema reflecting the swapped exercise or note.
    """
    session = await use_case.execute(session_id, session_exercise_id, payload, user["sub"])
    return WorkoutSessionOut.model_validate(session)


@router.delete("/{session_id}/exercises/{session_exercise_id}", response_model=WorkoutSessionOut)
async def remove_exercise(
    session_id: uuid.UUID,
    session_exercise_id: uuid.UUID,
    user: CurrentUser,
    use_case: Annotated[
        RemoveExerciseFromSessionUseCase, Depends(get_remove_exercise_from_session_use_case)
    ],
) -> WorkoutSessionOut:
    """
    Arg: session_id/session_exercise_id - UUID path params; user - authenticated user.
    Operation: delegates to RemoveExerciseFromSessionUseCase and serialises the updated session.
    Return: WorkoutSessionOut schema with the exercise removed.
    """
    session = await use_case.execute(session_id, session_exercise_id, user["sub"])
    return WorkoutSessionOut.model_validate(session)


@router.post("/{session_id}/exercises/{exercise_id}/sets", response_model=WorkoutSessionOut)
async def add_set(
    session_id: uuid.UUID,
    exercise_id: uuid.UUID,
    payload: SessionSetCreate,
    user: CurrentUser,
    use_case: Annotated[AddSetUseCase, Depends(get_add_set_use_case)],
) -> WorkoutSessionOut:
    """
    Arg: session_id/exercise_id - UUID path params; payload - set input; user - authenticated.
    Operation: delegates to AddSetUseCase and serialises the updated session.
    Return: WorkoutSessionOut schema reflecting the new set.
    """
    session = await use_case.execute(session_id, exercise_id, payload, user["sub"])
    return WorkoutSessionOut.model_validate(session)


@router.patch("/{session_id}/sets/{set_id}", response_model=WorkoutSessionOut)
async def update_set(
    session_id: uuid.UUID,
    set_id: uuid.UUID,
    payload: SessionSetUpdate,
    user: CurrentUser,
    use_case: Annotated[UpdateSetUseCase, Depends(get_update_set_use_case)],
) -> WorkoutSessionOut:
    """
    Arg: session_id/set_id - UUID path params; payload - patch body; user - authenticated.
    Operation: delegates to UpdateSetUseCase and serialises the updated session.
    Return: WorkoutSessionOut schema reflecting the patched set.
    """
    session = await use_case.execute(session_id, set_id, payload, user["sub"])
    return WorkoutSessionOut.model_validate(session)


@router.delete("/{session_id}/sets/{set_id}", response_model=WorkoutSessionOut)
async def delete_set(
    session_id: uuid.UUID,
    set_id: uuid.UUID,
    user: CurrentUser,
    use_case: Annotated[DeleteSetUseCase, Depends(get_delete_set_use_case)],
) -> WorkoutSessionOut:
    """
    Arg: session_id/set_id - UUID path params; user - authenticated user; use_case - injected.
    Operation: delegates to DeleteSetUseCase and serialises the updated session.
    Return: WorkoutSessionOut schema with the set removed.
    """
    session = await use_case.execute(session_id, set_id, user["sub"])
    return WorkoutSessionOut.model_validate(session)
