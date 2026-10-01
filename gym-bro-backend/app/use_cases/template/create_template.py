"""Use case: create a new workout template."""

from app.domain.models.template import TemplateExercise, TemplateSet, WorkoutTemplate
from app.domain.ordering import resolve_order
from app.domain.schemas.template import TemplateExerciseCreate, WorkoutTemplateCreate
from app.repositories.template_repository import TemplateRepository


class CreateTemplateUseCase:
    """Creates and persists a new workout template for the requesting user."""

    def __init__(self, repository: TemplateRepository) -> None:
        """
        Arg: repository - template data-access object.
        Operation: stores the repository for use during execution.
        Return: CreateTemplateUseCase instance.
        """
        self._repository = repository

    async def execute(self, data: WorkoutTemplateCreate, user_id: str) -> WorkoutTemplate:
        """
        Arg: data - validated template creation input; user_id - owner's Keycloak subject.
        Operation: builds the template entity graph (template → exercises → sets),
                   persists the root entity, and reloads it with full relations.
        Return: fully loaded WorkoutTemplate entity.
        """
        template = WorkoutTemplate(
            user_id=user_id,
            name=data.name,
            description=data.description,
            estimated_duration_minutes=data.estimated_duration_minutes,
        )
        for index, exercise_data in enumerate(data.exercises):
            template_exercise = self._build_template_exercise(exercise_data, index)
            template.exercises.append(template_exercise)

        saved = await self._repository.create(template)
        await self._repository.commit()
        return await self._repository.get_full(saved.id)

    @staticmethod
    def _build_template_exercise(
        exercise_data: TemplateExerciseCreate, index: int
    ) -> TemplateExercise:
        """
        Arg: exercise_data - input for a single exercise entry; index - display order.
        Operation: constructs the TemplateExercise and its child TemplateSet entities.
        Return: TemplateExercise entity (not yet persisted).
        """
        template_exercise = TemplateExercise(
            exercise_id=exercise_data.exercise_id,
            order=resolve_order(exercise_data.order, index),
            notes=exercise_data.notes,
        )
        for set_index, set_data in enumerate(exercise_data.sets):
            template_set = TemplateSet(
                **set_data.model_dump(exclude={"order"}),
                order=resolve_order(set_data.order, set_index),
            )
            template_exercise.sets.append(template_set)
        return template_exercise
