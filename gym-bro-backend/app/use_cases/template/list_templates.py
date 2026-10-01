"""Use case: list all workout templates for a user."""

from app.domain.models.template import WorkoutTemplate
from app.repositories.template_repository import TemplateRepository


class ListTemplatesUseCase:
    """Returns all workout templates belonging to the requesting user."""

    def __init__(self, repository: TemplateRepository) -> None:
        """
        Arg: repository - template data-access object.
        Operation: stores the repository for use during execution.
        Return: ListTemplatesUseCase instance.
        """
        self._repository = repository

    async def execute(self, user_id: str) -> list[WorkoutTemplate]:
        """
        Arg: user_id - Keycloak subject of the requesting user.
        Operation: retrieves all templates owned by the user, ordered by name.
        Return: list of WorkoutTemplate entities.
        """
        return await self._repository.list_for_user(user_id)
