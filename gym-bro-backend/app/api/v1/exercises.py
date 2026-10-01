"""Exercise endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    get_create_exercise_use_case,
    get_delete_exercise_use_case,
    get_get_exercise_use_case,
    get_last_performance_use_case,
    get_list_exercises_use_case,
    get_list_recent_exercises_use_case,
    get_update_exercise_use_case,
)
from app.core.security import CurrentUser
from app.domain.schemas.exercise import (
    ExerciseCreate,
    ExerciseFilters,
    ExerciseOut,
    ExerciseSummaryOut,
    ExerciseUpdate,
)
from app.domain.schemas.workout import LastPerformanceOut
from app.use_cases.exercise.create_exercise import CreateExerciseUseCase
from app.use_cases.exercise.delete_exercise import DeleteExerciseUseCase
from app.use_cases.exercise.get_exercise import GetExerciseUseCase
from app.use_cases.exercise.list_exercises import ListExercisesUseCase
from app.use_cases.exercise.list_recent_exercises import ListRecentExercisesUseCase
from app.use_cases.exercise.update_exercise import UpdateExerciseUseCase
from app.use_cases.workout.get_last_performance import GetLastPerformanceUseCase

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=list[ExerciseSummaryOut])
async def list_exercises(
    user: CurrentUser,
    use_case: Annotated[ListExercisesUseCase, Depends(get_list_exercises_use_case)],
    filters: Annotated[ExerciseFilters, Query()],
) -> list[ExerciseSummaryOut]:
    """
    Arg: user - authenticated user; use_case - injected use case; filters - library narrowing.
    Operation: delegates to ListExercisesUseCase and serialises the result as summaries.
    Return: list of ExerciseSummaryOut schemas.
    """
    exercises = await use_case.execute(user["sub"], filters)
    return [ExerciseSummaryOut.model_validate(e) for e in exercises]


# Declared before /{exercise_id} so that "recent" is not parsed as a UUID path parameter.
@router.get("/recent", response_model=list[ExerciseSummaryOut])
async def list_recent_exercises(
    user: CurrentUser,
    use_case: Annotated[ListRecentExercisesUseCase, Depends(get_list_recent_exercises_use_case)],
    limit: int = Query(default=12, ge=1, le=50),
) -> list[ExerciseSummaryOut]:
    """
    Arg: user - authenticated user; use_case - injected use case; limit - how many to return.
    Operation: delegates to ListRecentExercisesUseCase and serialises the result as summaries.
    Return: list of ExerciseSummaryOut schemas, most recently trained first.
    """
    exercises = await use_case.execute(user["sub"], limit)
    return [ExerciseSummaryOut.model_validate(e) for e in exercises]


@router.get("/{exercise_id}", response_model=ExerciseOut)
async def get_exercise(
    exercise_id: uuid.UUID,
    user: CurrentUser,
    use_case: Annotated[GetExerciseUseCase, Depends(get_get_exercise_use_case)],
) -> ExerciseOut:
    """
    Arg: exercise_id - UUID path param; user - authenticated user; use_case - injected.
    Operation: delegates to GetExerciseUseCase and serialises the result.
    Return: ExerciseOut schema.
    """
    exercise = await use_case.execute(exercise_id)
    return ExerciseOut.model_validate(exercise)


@router.get("/{exercise_id}/last-performance", response_model=LastPerformanceOut | None)
async def get_last_performance(
    exercise_id: uuid.UUID,
    user: CurrentUser,
    use_case: Annotated[GetLastPerformanceUseCase, Depends(get_last_performance_use_case)],
) -> LastPerformanceOut | None:
    """
    Arg: exercise_id - UUID path param; user - authenticated user; use_case - injected.
    Operation: delegates to GetLastPerformanceUseCase and serialises the result. Returns null
               rather than 404 when there is no history — an exercise you have never trained
               is an ordinary case, not an error.
    Return: LastPerformanceOut schema, or None.
    """
    entry = await use_case.execute(exercise_id, user["sub"])
    return None if entry is None else LastPerformanceOut.from_entry(entry)


@router.post("", response_model=ExerciseOut, status_code=201)
async def create_exercise(
    payload: ExerciseCreate,
    user: CurrentUser,
    use_case: Annotated[CreateExerciseUseCase, Depends(get_create_exercise_use_case)],
) -> ExerciseOut:
    """
    Arg: payload - exercise creation body; user - authenticated user; use_case - injected.
    Operation: delegates to CreateExerciseUseCase and serialises the result.
    Return: ExerciseOut schema for the newly created exercise.
    """
    exercise = await use_case.execute(payload, user["sub"])
    return ExerciseOut.model_validate(exercise)


@router.patch("/{exercise_id}", response_model=ExerciseOut)
async def update_exercise(
    exercise_id: uuid.UUID,
    payload: ExerciseUpdate,
    user: CurrentUser,
    use_case: Annotated[UpdateExerciseUseCase, Depends(get_update_exercise_use_case)],
) -> ExerciseOut:
    """
    Arg: exercise_id - UUID path param; payload - update body; user - authenticated user.
    Operation: delegates to UpdateExerciseUseCase and serialises the result.
    Return: ExerciseOut schema for the updated exercise.
    """
    exercise = await use_case.execute(exercise_id, payload, user["sub"])
    return ExerciseOut.model_validate(exercise)


@router.delete("/{exercise_id}", status_code=204)
async def delete_exercise(
    exercise_id: uuid.UUID,
    user: CurrentUser,
    use_case: Annotated[DeleteExerciseUseCase, Depends(get_delete_exercise_use_case)],
) -> None:
    """
    Arg: exercise_id - UUID path param; user - authenticated user; use_case - injected.
    Operation: delegates to DeleteExerciseUseCase; returns 204 on success.
    Return: None.
    """
    await use_case.execute(exercise_id, user["sub"])
