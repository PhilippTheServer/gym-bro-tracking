"""Domain tests for the vendored catalogue's mapping onto this application's taxonomy."""

from app.domain.exercise_catalog import (
    PREFERRED_NAMES,
    load_catalog,
    normalise_name,
    to_catalog_entry,
    to_equipment,
    to_muscle_group,
    to_primary_muscle,
)
from app.domain.models.exercise import Equipment, ExerciseCategory, MuscleGroup, PrimaryMuscle


def test_normalise_name_ignores_case_punctuation_and_spacing() -> None:
    assert normalise_name("Barbell Bench Press") == normalise_name("barbell  bench-press")
    assert normalise_name("Dips (Chest)") == "dipschest"


def test_normalise_name_separates_genuinely_different_names() -> None:
    assert normalise_name("Front Squat") != normalise_name("Back Squat")


def test_primary_muscle_takes_the_first_recognised_entry() -> None:
    assert to_primary_muscle(["lower back"]) is PrimaryMuscle.LOWER_BACK
    assert to_primary_muscle([]) is None
    assert to_primary_muscle(["left earlobe"]) is None


def test_muscle_group_rolls_a_fine_muscle_up() -> None:
    assert to_muscle_group(PrimaryMuscle.LATS, ExerciseCategory.STRENGTH) is MuscleGroup.BACK
    assert to_muscle_group(PrimaryMuscle.HAMSTRINGS, ExerciseCategory.STRENGTH) is MuscleGroup.LEGS


def test_cardio_outranks_the_muscle_it_happens_to_load() -> None:
    """Treadmill work lists quadriceps as its primary muscle but belongs under Cardio."""
    assert to_muscle_group(PrimaryMuscle.QUADRICEPS, ExerciseCategory.CARDIO) is MuscleGroup.CARDIO


def test_an_entry_without_a_known_muscle_lands_in_full_body() -> None:
    assert to_muscle_group(None, ExerciseCategory.STRENGTH) is MuscleGroup.FULL_BODY


def test_equipment_folds_unmodelled_kit_into_other() -> None:
    assert to_equipment("body only") is Equipment.BODYWEIGHT
    assert to_equipment("e-z curl bar") is Equipment.BARBELL
    assert to_equipment("foam roll") is Equipment.OTHER
    assert to_equipment(None) is Equipment.OTHER


def test_a_preferred_name_replaces_the_catalogue_name() -> None:
    entry = to_catalog_entry(
        {
            "id": "Barbell_Bench_Press_-_Medium_Grip",
            "name": "Barbell Bench Press - Medium Grip",
            "category": "strength",
            "equipment": "barbell",
            "primaryMuscles": ["chest"],
            "secondaryMuscles": ["triceps"],
            "instructions": ["Lie back on a flat bench."],
        }
    )
    assert entry.name == "Barbell Bench Press"
    assert entry.muscle_group is MuscleGroup.CHEST
    assert entry.primary_muscle is PrimaryMuscle.CHEST
    assert entry.secondary_muscles == "triceps"


def test_the_whole_catalogue_maps_without_a_gap() -> None:
    catalog = load_catalog()
    assert len(catalog) == 876
    assert all(entry.muscle_group in set(MuscleGroup) for entry in catalog)
    assert all(entry.equipment in set(Equipment) for entry in catalog)


def test_no_two_catalogue_entries_share_a_name() -> None:
    """A collision would make the importer's name matching ambiguous."""
    names = [normalise_name(entry.name) for entry in load_catalog()]
    assert len(names) == len(set(names))


def test_every_preferred_name_belongs_to_a_real_catalogue_entry() -> None:
    external_ids = {entry.external_id for entry in load_catalog()}
    assert set(PREFERRED_NAMES) <= external_ids
