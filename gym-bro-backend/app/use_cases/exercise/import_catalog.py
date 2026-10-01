"""Use case: bring the vendored exercise catalogue into the database."""

from dataclasses import dataclass

from app.domain.exercise_catalog import CatalogEntry, normalise_name
from app.domain.models.exercise import Exercise
from app.repositories.exercise_repository import ExerciseRepository


@dataclass(frozen=True)
class ImportSummary:
    """What one import run changed."""

    inserted: int
    updated: int
    unchanged: int


class ImportCatalogUseCase:
    """Reconciles the catalogue against the stored exercise library.

    Nothing is ever deleted. template_exercises.exercise_id cascades on delete, so
    removing a built-in exercise would take it out of every template that references it.
    Catalogue entries are matched onto existing rows — by external id first, then by
    normalised name — and enriched in place, which keeps their primary keys and therefore
    every template and finished workout that points at them. Custom exercises are not
    candidates for matching and are never touched.
    """

    def __init__(self, repository: ExerciseRepository) -> None:
        """
        Arg: repository - exercise data-access object.
        Operation: stores the repository for use during execution.
        Return: ImportCatalogUseCase instance.
        """
        self._repository = repository

    async def execute(self, entries: list[CatalogEntry]) -> ImportSummary:
        """
        Arg: entries - the catalogue, already mapped onto this application's taxonomy.
        Operation: updates the built-in exercises that the catalogue already knows about and
                   inserts the ones it does not, then commits once. Running it again over an
                   unchanged catalogue reports no inserts and no updates.
        Return: ImportSummary counting inserted, updated and unchanged rows.
        """
        built_ins = await self._repository.list_built_in()
        by_external_id = {row.external_id: row for row in built_ins if row.external_id}
        unclaimed_by_name = {
            normalise_name(row.name): row for row in built_ins if not row.external_id
        }

        inserted = 0
        updated = 0
        unchanged = 0

        for entry in entries:
            existing = by_external_id.get(entry.external_id)
            if existing is None:
                existing = unclaimed_by_name.pop(normalise_name(entry.name), None)

            if existing is None:
                self._repository.add(_new_exercise(entry))
                inserted += 1
            elif _apply(entry, existing):
                updated += 1
            else:
                unchanged += 1

        await self._repository.commit()
        return ImportSummary(inserted=inserted, updated=updated, unchanged=unchanged)


def _new_exercise(entry: CatalogEntry) -> Exercise:
    """
    Arg: entry - a catalogue entry with no counterpart in the database.
    Operation: builds the built-in Exercise entity the entry describes.
    Return: the unsaved Exercise.
    """
    return Exercise(
        external_id=entry.external_id,
        name=entry.name,
        muscle_group=entry.muscle_group,
        primary_muscle=entry.primary_muscle,
        secondary_muscles=entry.secondary_muscles,
        equipment=entry.equipment,
        category=entry.category,
        instructions=entry.instructions,
        is_custom=False,
    )


def _apply(entry: CatalogEntry, exercise: Exercise) -> bool:
    """
    Arg: entry - the catalogue entry; exercise - the stored row it corresponds to.
    Operation: copies the catalogue's fields onto the row, leaving its primary key alone.
    Return: True when at least one field actually changed, otherwise False.
    """
    fields = {
        "external_id": entry.external_id,
        "name": entry.name,
        "muscle_group": str(entry.muscle_group),
        "primary_muscle": str(entry.primary_muscle) if entry.primary_muscle else None,
        "secondary_muscles": entry.secondary_muscles,
        "equipment": str(entry.equipment),
        "category": str(entry.category),
        "instructions": entry.instructions,
    }
    has_changed = False
    for field, value in fields.items():
        if getattr(exercise, field) != value:
            setattr(exercise, field, value)
            has_changed = True
    return has_changed
