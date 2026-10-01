"""Progress and analytics endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_exercise_progress_use_case, get_progress_overview_use_case
from app.core.security import CurrentUser
from app.domain.schemas.progress import ExerciseProgress, ProgressOverview
from app.use_cases.progress.get_exercise_progress import GetExerciseProgressUseCase
from app.use_cases.progress.get_progress_overview import GetProgressOverviewUseCase

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/overview", response_model=ProgressOverview)
async def get_overview(
    user: CurrentUser,
    use_case: Annotated[GetProgressOverviewUseCase, Depends(get_progress_overview_use_case)],
) -> ProgressOverview:
    """
    Arg: user - authenticated user; use_case - injected use case.
    Operation: delegates to GetProgressOverviewUseCase and returns the aggregated result.
    Return: ProgressOverview schema with streaks, volume, PRs, and frequency data.
    """
    return await use_case.execute(user["sub"])


@router.get("/exercises/{exercise_id}", response_model=ExerciseProgress)
async def get_exercise_progress(
    exercise_id: uuid.UUID,
    user: CurrentUser,
    use_case: Annotated[GetExerciseProgressUseCase, Depends(get_exercise_progress_use_case)],
) -> ExerciseProgress:
    """
    Arg: exercise_id - UUID path param; user - authenticated user; use_case - injected.
    Operation: delegates to GetExerciseProgressUseCase and returns the per-exercise history.
    Return: ExerciseProgress schema with chronological progress data points.
    """
    return await use_case.execute(user["sub"], exercise_id)
