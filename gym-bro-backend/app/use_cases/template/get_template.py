"""Use case: retrieve a single workout template with full exercise/set detail."""

import uuid

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.domain.models.template import WorkoutTemplate
from app.repositories.template_repository import TemplateRepository


class GetTemplateUseCase:
    """Fetches a workout template and verifies the requester is the owner."""

    def __init__(self, repository: TemplateRepository) -> None:
        """
        Arg: repository - template data-access object.
        Operation: stores the repository for use during execution.
        Return: GetTemplateUseCase instance.
        """
        self._repository = repository

    async def execute(self, template_id: uuid.UUID, user_id: str) -> WorkoutTemplate:
        """
        Arg: template_id - UUID of the template; user_id - requester's Keycloak subject.
        Operation: loads the template with all related exercises and sets.
                   Raises NotFoundError if the template does not exist.
                   Raises ForbiddenError if the requester is not the owner.
        Return: fully loaded WorkoutTemplate entity.
        """
        template = await self._repository.get_full(template_id)
        if template is None:
            raise NotFoundError("WorkoutTemplate", template_id)
        if template.user_id != user_id:
            raise ForbiddenError("You do not own this template.")
        return template
