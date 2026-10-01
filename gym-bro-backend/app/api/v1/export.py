"""Export endpoint used by daily's Keycloak service account to pull completed workouts."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import AwareDatetime

from app.api.deps import get_export_sessions_use_case
from app.core.security import ExportCaller
from app.domain.schemas.workout import WorkoutSessionOut
from app.use_cases.workout.export_sessions import ExportSessionsUseCase

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/workouts", response_model=list[WorkoutSessionOut])
async def export_workouts(
    caller: ExportCaller,
    use_case: Annotated[ExportSessionsUseCase, Depends(get_export_sessions_use_case)],
    user_id: str,
    completed_after: AwareDatetime,
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[WorkoutSessionOut]:
    """
    Arg: caller - validated export-client claims; use_case - injected use case;
         user_id - owner whose sessions to export; completed_after - exclusive,
         timezone-aware lower bound (a naive value fails request validation with 422);
         limit/offset - pagination params.
    Operation: delegates to ExportSessionsUseCase and serialises each result.
    Return: list of WorkoutSessionOut schemas completed after the cutoff, ascending.
    """
    sessions = await use_case.execute(user_id, completed_after, limit, offset)
    return [WorkoutSessionOut.model_validate(s) for s in sessions]
