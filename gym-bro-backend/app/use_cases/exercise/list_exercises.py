"""Use case: list exercises visible to a user."""

from app.domain.models.exercise import Exercise
from app.domain.schemas.exercise import ExerciseFilters
from app.repositories.exercise_repository import ExerciseRepository


class ListExercisesUseCase:
    """Returns all exercises accessible to the requesting user."""

    def __init__(self, repository: ExerciseRepository) -> None:
        """
        Arg: repository - exercise data-access object.
        Operation: stores the repository for use during execution.
        Return: ListExercisesUseCase instance.
        """
        self._repository = repository

    async def execute(self, user_id: str, filters: ExerciseFilters) -> list[Exercise]:
        """
        Arg: user_id - Keycloak subject of the requesting user; filters - library narrowing.
        Operation: retrieves all global exercises plus the user's own custom exercises, applying
                   whichever of the search term, muscle group, primary muscle, equipment and
                   category filters were supplied.
        Return: list of Exercise entities ordered by name.
        """
        return await self._repository.search(
            query=filters.search,
            user_id=user_id,
            muscle_group=filters.muscle_group,
            primary_muscle=filters.primary_muscle,
            equipment=filters.equipment,
            category=filters.category,
        )
