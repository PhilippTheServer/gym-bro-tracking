"""Workout template endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_create_template_use_case,
    get_delete_template_use_case,
    get_get_template_use_case,
    get_list_templates_use_case,
    get_update_template_use_case,
)
from app.core.security import CurrentUser
from app.domain.schemas.template import (
    WorkoutTemplateCreate,
    WorkoutTemplateOut,
    WorkoutTemplateUpdate,
)
from app.use_cases.template.create_template import CreateTemplateUseCase
from app.use_cases.template.delete_template import DeleteTemplateUseCase
from app.use_cases.template.get_template import GetTemplateUseCase
from app.use_cases.template.list_templates import ListTemplatesUseCase
from app.use_cases.template.update_template import UpdateTemplateUseCase

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[WorkoutTemplateOut])
async def list_templates(
    user: CurrentUser,
    use_case: Annotated[ListTemplatesUseCase, Depends(get_list_templates_use_case)],
) -> list[WorkoutTemplateOut]:
    """
    Arg: user - authenticated user; use_case - injected use case.
    Operation: delegates to ListTemplatesUseCase and serialises each result.
    Return: list of WorkoutTemplateOut schemas.
    """
    templates = await use_case.execute(user["sub"])
    return [WorkoutTemplateOut.model_validate(t) for t in templates]


@router.get("/{template_id}", response_model=WorkoutTemplateOut)
async def get_template(
    template_id: uuid.UUID,
    user: CurrentUser,
    use_case: Annotated[GetTemplateUseCase, Depends(get_get_template_use_case)],
) -> WorkoutTemplateOut:
    """
    Arg: template_id - UUID path param; user - authenticated user; use_case - injected.
    Operation: delegates to GetTemplateUseCase and serialises the result.
    Return: WorkoutTemplateOut schema with full exercise and set detail.
    """
    template = await use_case.execute(template_id, user["sub"])
    return WorkoutTemplateOut.model_validate(template)


@router.post("", response_model=WorkoutTemplateOut, status_code=201)
async def create_template(
    payload: WorkoutTemplateCreate,
    user: CurrentUser,
    use_case: Annotated[CreateTemplateUseCase, Depends(get_create_template_use_case)],
) -> WorkoutTemplateOut:
    """
    Arg: payload - template creation body; user - authenticated user; use_case - injected.
    Operation: delegates to CreateTemplateUseCase and serialises the result.
    Return: WorkoutTemplateOut schema for the newly created template.
    """
    template = await use_case.execute(payload, user["sub"])
    return WorkoutTemplateOut.model_validate(template)


@router.put("/{template_id}", response_model=WorkoutTemplateOut)
async def update_template(
    template_id: uuid.UUID,
    payload: WorkoutTemplateUpdate,
    user: CurrentUser,
    use_case: Annotated[UpdateTemplateUseCase, Depends(get_update_template_use_case)],
) -> WorkoutTemplateOut:
    """
    Arg: template_id - UUID path param; payload - update body; user - authenticated user.
    Operation: delegates to UpdateTemplateUseCase and serialises the result.
    Return: WorkoutTemplateOut schema for the updated template.
    """
    template = await use_case.execute(template_id, payload, user["sub"])
    return WorkoutTemplateOut.model_validate(template)


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: uuid.UUID,
    user: CurrentUser,
    use_case: Annotated[DeleteTemplateUseCase, Depends(get_delete_template_use_case)],
) -> None:
    """
    Arg: template_id - UUID path param; user - authenticated user; use_case - injected.
    Operation: delegates to DeleteTemplateUseCase; returns 204 on success.
    Return: None.
    """
    await use_case.execute(template_id, user["sub"])
