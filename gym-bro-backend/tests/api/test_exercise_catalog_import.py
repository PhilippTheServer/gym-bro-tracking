"""Tests for reconciling the vendored catalogue against a database that is already in use."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exercise_catalog import CatalogEntry, load_catalog
from app.domain.models.exercise import Equipment, Exercise, ExerciseCategory, MuscleGroup
from app.repositories.exercise_repository import ExerciseRepository
from app.use_cases.exercise.import_catalog import ImportCatalogUseCase
from tests.conftest import requires_db

pytestmark = requires_db


def _entries(*names: str) -> list[CatalogEntry]:
    """
    Arg: names - display names to pick out of the vendored catalogue.
    Operation: filters the real catalogue down to a handful of entries, so a test exercises the
               same data the container imports without inserting all 876 rows.
    Return: the matching catalogue entries.
    """
    wanted = set(names)
    return [entry for entry in load_catalog() if entry.name in wanted]


async def _import(session: AsyncSession, entries: list[CatalogEntry]):
    """
    Arg: session - the test database session; entries - the catalogue slice to import.
    Operation: runs the import use case against the test session.
    Return: the ImportSummary for the run.
    """
    return await ImportCatalogUseCase(ExerciseRepository(session)).execute(entries)


async def _add_built_in(session: AsyncSession, name: str) -> Exercise:
    """
    Arg: session - the test database session; name - name of the exercise to insert.
    Operation: inserts a built-in exercise the way the old seed did, with no catalogue id.
    Return: the persisted Exercise.
    """
    exercise = Exercise(
        name=name,
        muscle_group=MuscleGroup.CHEST,
        equipment=Equipment.BARBELL,
        is_custom=False,
    )
    session.add(exercise)
    await session.commit()
    return exercise


async def test_import_enriches_an_existing_exercise_instead_of_replacing_it(
    session: AsyncSession, client: AsyncClient
) -> None:
    """The row a template points at must survive the import with its primary key intact.

    exercise_id cascades on delete, so an importer that cleared the built-ins and reseeded
    would take this exercise out of the template without any error surfacing.
    """
    existing = await _add_built_in(session, "Barbell Bench Press")
    original_id = str(existing.id)

    template = (
        await client.post(
            "/api/v1/templates",
            json={
                "name": "Push Day",
                "exercises": [
                    {
                        "exercise_id": original_id,
                        "order": 0,
                        "sets": [{"set_type": "working_set", "target_reps": 8, "order": 0}],
                    }
                ],
            },
        )
    ).json()

    summary = await _import(session, _entries("Barbell Bench Press"))

    assert summary.inserted == 0
    assert summary.updated == 1

    enriched = (await client.get(f"/api/v1/exercises/{original_id}")).json()
    assert enriched["external_id"] == "Barbell_Bench_Press_-_Medium_Grip"
    assert enriched["primary_muscle"] == "chest"
    assert enriched["category"] == "strength"
    assert enriched["name"] == "Barbell Bench Press"

    reloaded = (await client.get(f"/api/v1/templates/{template['id']}")).json()
    assert [e["exercise_id"] for e in reloaded["exercises"]] == [original_id]


async def test_a_second_import_changes_nothing(session: AsyncSession) -> None:
    entries = _entries("Barbell Bench Press", "Deadlift", "Pull-Up")

    first = await _import(session, entries)
    second = await _import(session, entries)

    assert first.inserted == 3
    assert second == type(second)(inserted=0, updated=0, unchanged=3)


async def test_a_custom_exercise_is_never_claimed_by_the_catalogue(
    session: AsyncSession, client: AsyncClient
) -> None:
    """A user's own 'Deadlift' must not be overwritten by the catalogue's."""
    custom = (
        await client.post(
            "/api/v1/exercises",
            json={"name": "Deadlift", "muscle_group": "back", "equipment": "barbell"},
        )
    ).json()

    summary = await _import(session, _entries("Deadlift"))

    assert summary.inserted == 1
    unchanged = (await client.get(f"/api/v1/exercises/{custom['id']}")).json()
    assert unchanged["is_custom"] is True
    assert unchanged["external_id"] is None
    assert unchanged["muscle_group"] == "back"


async def test_the_full_catalogue_imports(session: AsyncSession, client: AsyncClient) -> None:
    summary = await _import(session, load_catalog())

    assert summary.inserted == 876
    library = (await client.get("/api/v1/exercises")).json()
    assert len(library) == 876


async def test_the_library_filters_by_group_and_primary_muscle(
    session: AsyncSession, client: AsyncClient
) -> None:
    await _import(session, load_catalog())

    back = (await client.get("/api/v1/exercises", params={"muscle_group": "back"})).json()
    lats = (await client.get("/api/v1/exercises", params={"primary_muscle": "lats"})).json()

    assert len(lats) < len(back)
    assert {entry["muscle_group"] for entry in back} == {"back"}
    assert {entry["primary_muscle"] for entry in lats} == {"lats"}
    assert {entry["muscle_group"] for entry in lats} == {"back"}


async def test_the_library_filters_by_equipment_and_category(
    session: AsyncSession, client: AsyncClient
) -> None:
    await _import(session, load_catalog())

    barbell = (await client.get("/api/v1/exercises", params={"equipment": "barbell"})).json()
    stretching = (await client.get("/api/v1/exercises", params={"category": "stretching"})).json()

    assert {entry["equipment"] for entry in barbell} == {"barbell"}
    assert {entry["category"] for entry in stretching} == {str(ExerciseCategory.STRETCHING)}
