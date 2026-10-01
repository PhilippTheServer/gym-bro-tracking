"""Use case: delete a workout template."""

import uuid

from app.domain.exceptions import ForbiddenError, NotFoundError
from app.repositories.template_repository import TemplateRepository


class DeleteTemplateUseCase:
    """Deletes a workout template owned by the requesting user."""

    def __init__(self, repository: TemplateRepository) -> None:
        """
        Arg: repository - template data-access object.
        Operation: stores the repository for use during execution.
        Return: DeleteTemplateUseCase instance.
        """
        self._repository = repository

    async def execute(self, template_id: uuid.UUID, user_id: str) -> None:
        """
        Arg: template_id - UUID of the template to delete; user_id - requester's subject.
        Operation: verifies the template exists and is owned by the user, then deletes it.
                   Raises NotFoundError if absent.
                   Raises ForbiddenError if the requester is not the owner.
        Return: None.
        """
        template = await self._repository.get_full(template_id)
        if template is None:
            raise NotFoundError("WorkoutTemplate", template_id)
        if template.user_id != user_id:
            raise ForbiddenError("You do not own this template.")

        await self._repository.delete(template)
        await self._repository.commit()
