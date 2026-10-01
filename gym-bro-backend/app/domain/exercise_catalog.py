"""Reads the vendored exercise catalogue and maps it onto this application's taxonomy.

Pure functions only — no database, no I/O beyond reading the JSON file. The catalogue's
own vocabulary (17 muscles, 7 categories, 13 equipment names) is wider than the one the
application stores, so every value is translated explicitly rather than trusted.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.domain.models.exercise import Equipment, ExerciseCategory, MuscleGroup, PrimaryMuscle

CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "exercises.json"

SECONDARY_MUSCLES_MAX_LENGTH = 255

_PRIMARY_MUSCLES: dict[str, PrimaryMuscle] = {
    "abdominals": PrimaryMuscle.ABDOMINALS,
    "abductors": PrimaryMuscle.ABDUCTORS,
    "adductors": PrimaryMuscle.ADDUCTORS,
    "biceps": PrimaryMuscle.BICEPS,
    "calves": PrimaryMuscle.CALVES,
    "chest": PrimaryMuscle.CHEST,
    "forearms": PrimaryMuscle.FOREARMS,
    "glutes": PrimaryMuscle.GLUTES,
    "hamstrings": PrimaryMuscle.HAMSTRINGS,
    "lats": PrimaryMuscle.LATS,
    "lower back": PrimaryMuscle.LOWER_BACK,
    "middle back": PrimaryMuscle.MIDDLE_BACK,
    "neck": PrimaryMuscle.NECK,
    "quadriceps": PrimaryMuscle.QUADRICEPS,
    "shoulders": PrimaryMuscle.SHOULDERS,
    "traps": PrimaryMuscle.TRAPS,
    "triceps": PrimaryMuscle.TRICEPS,
}

_MUSCLE_GROUPS: dict[PrimaryMuscle, MuscleGroup] = {
    PrimaryMuscle.CHEST: MuscleGroup.CHEST,
    PrimaryMuscle.LATS: MuscleGroup.BACK,
    PrimaryMuscle.MIDDLE_BACK: MuscleGroup.BACK,
    PrimaryMuscle.LOWER_BACK: MuscleGroup.BACK,
    PrimaryMuscle.TRAPS: MuscleGroup.BACK,
    PrimaryMuscle.SHOULDERS: MuscleGroup.SHOULDERS,
    PrimaryMuscle.BICEPS: MuscleGroup.BICEPS,
    PrimaryMuscle.TRICEPS: MuscleGroup.TRICEPS,
    PrimaryMuscle.FOREARMS: MuscleGroup.FOREARMS,
    PrimaryMuscle.QUADRICEPS: MuscleGroup.LEGS,
    PrimaryMuscle.HAMSTRINGS: MuscleGroup.LEGS,
    PrimaryMuscle.CALVES: MuscleGroup.LEGS,
    PrimaryMuscle.ADDUCTORS: MuscleGroup.LEGS,
    PrimaryMuscle.ABDUCTORS: MuscleGroup.LEGS,
    PrimaryMuscle.GLUTES: MuscleGroup.GLUTES,
    PrimaryMuscle.ABDOMINALS: MuscleGroup.CORE,
    PrimaryMuscle.NECK: MuscleGroup.NECK,
}

_EQUIPMENT: dict[str, Equipment] = {
    "barbell": Equipment.BARBELL,
    "dumbbell": Equipment.DUMBBELL,
    "cable": Equipment.CABLE,
    "machine": Equipment.MACHINE,
    "body only": Equipment.BODYWEIGHT,
    "kettlebells": Equipment.KETTLEBELL,
    "bands": Equipment.BAND,
    "e-z curl bar": Equipment.BARBELL,
    "medicine ball": Equipment.OTHER,
    "exercise ball": Equipment.OTHER,
    "foam roll": Equipment.OTHER,
    "other": Equipment.OTHER,
}

_CATEGORIES: dict[str, ExerciseCategory] = {
    "strength": ExerciseCategory.STRENGTH,
    "stretching": ExerciseCategory.STRETCHING,
    "plyometrics": ExerciseCategory.PLYOMETRICS,
    "powerlifting": ExerciseCategory.POWERLIFTING,
    "olympic weightlifting": ExerciseCategory.OLYMPIC_WEIGHTLIFTING,
    "strongman": ExerciseCategory.STRONGMAN,
    "cardio": ExerciseCategory.CARDIO,
}


# The catalogue's own names are inconsistent ("Barbell Bench Press - Medium Grip",
# "Pushups", "Bicycling, Stationary"). These are the names this application used before
# the import, kept as the display name so the library reads cleanly and — because the
# importer matches on the normalised name — so the rows already in a database are
# recognised and enriched instead of being duplicated by their catalogue twin.
PREFERRED_NAMES: dict[str, str] = {
    "Barbell_Bench_Press_-_Medium_Grip": "Barbell Bench Press",
    "Barbell_Incline_Bench_Press_-_Medium_Grip": "Incline Barbell Press",
    "Decline_Barbell_Bench_Press": "Decline Barbell Press",
    "Cable_Crossover": "Cable Fly",
    "Low_Cable_Crossover": "Low-to-High Cable Fly",
    "Pushups": "Push-Up",
    "Dips_-_Chest_Version": "Dips (Chest)",
    "Butterfly": "Pec Deck Machine",
    "Barbell_Deadlift": "Deadlift",
    "Bent_Over_Barbell_Row": "Barbell Row",
    "Pullups": "Pull-Up",
    "Wide-Grip_Lat_Pulldown": "Lat Pulldown",
    "Seated_Cable_Rows": "Seated Cable Row",
    "One-Arm_Dumbbell_Row": "Single-Arm Dumbbell Row",
    "T-Bar_Row_with_Handle": "T-Bar Row",
    "Standing_Military_Press": "Overhead Press (Barbell)",
    "Arnold_Dumbbell_Press": "Arnold Press",
    "Side_Lateral_Raise": "Lateral Raise",
    "Cable_Seated_Lateral_Raise": "Cable Lateral Raise",
    "Front_Dumbbell_Raise": "Front Raise",
    "Reverse_Flyes": "Rear Delt Fly",
    "Dumbbell_Bicep_Curl": "Dumbbell Curl",
    "Hammer_Curls": "Hammer Curl",
    "Standing_Biceps_Cable_Curl": "Cable Curl",
    "Close-Grip_Barbell_Bench_Press": "Close-Grip Bench Press",
    "EZ-Bar_Skullcrusher": "Skull Crusher",
    "Dips_-_Triceps_Version": "Tricep Dips",
    "Triceps_Pushdown": "Cable Pushdown (Bar)",
    "Triceps_Pushdown_-_Rope_Attachment": "Cable Pushdown (Rope)",
    "Seated_Triceps_Press": "Overhead Tricep Extension",
    "Barbell_Squat": "Barbell Back Squat",
    "Front_Barbell_Squat": "Front Squat",
    "Dumbbell_Lunges": "Lunges",
    "Lying_Leg_Curls": "Leg Curl (Lying)",
    "Seated_Leg_Curl": "Leg Curl (Seated)",
    "Leg_Extensions": "Leg Extension",
    "Standing_Calf_Raises": "Standing Calf Raise",
    "Barbell_Hip_Thrust": "Hip Thrust",
    "Butt_Lift_Bridge": "Glute Bridge",
    "One-Legged_Cable_Kickback": "Cable Kickback",
    "Ab_Roller": "Ab Wheel Rollout",
    "Running_Treadmill": "Treadmill Run",
    "Bicycling_Stationary": "Stationary Bike",
    "Rowing_Stationary": "Rowing Machine",
    "Rope_Jumping": "Jump Rope",
    "Battling_Ropes": "Battle Ropes",
}


@dataclass(frozen=True)
class CatalogEntry:
    """One exercise from the vendored catalogue, already in this application's vocabulary."""

    external_id: str
    name: str
    muscle_group: MuscleGroup
    primary_muscle: PrimaryMuscle | None
    secondary_muscles: str | None
    equipment: Equipment
    category: ExerciseCategory
    instructions: str | None


def normalise_name(name: str) -> str:
    """
    Arg: name - an exercise name from either the catalogue or the database.
    Operation: reduces the name to lowercase alphanumerics so that "Barbell Bench Press",
               "barbell bench-press" and "Barbell  Bench  Press" compare equal.
    Return: the comparison key for that name.
    """
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def to_primary_muscle(raw_muscles: list[str]) -> PrimaryMuscle | None:
    """
    Arg: raw_muscles - the catalogue's primaryMuscles list, which may be empty.
    Operation: takes the first recognised muscle name and translates it.
    Return: the matching PrimaryMuscle, or None when the list is empty or unrecognised.
    """
    for raw in raw_muscles:
        muscle = _PRIMARY_MUSCLES.get(raw.strip().lower())
        if muscle is not None:
            return muscle
    return None


def to_muscle_group(
    primary_muscle: PrimaryMuscle | None, category: ExerciseCategory
) -> MuscleGroup:
    """
    Arg: primary_muscle - the translated primary muscle; category - the translated category.
    Operation: rolls the fine-grained muscle up into a browsable group. Cardio wins over the
               muscle it happens to load, so treadmill work lands under Cardio and not Legs.
    Return: the MuscleGroup the exercise is filed under.
    """
    if category is ExerciseCategory.CARDIO:
        return MuscleGroup.CARDIO
    if primary_muscle is None:
        return MuscleGroup.FULL_BODY
    return _MUSCLE_GROUPS[primary_muscle]


def to_equipment(raw_equipment: str | None) -> Equipment:
    """
    Arg: raw_equipment - the catalogue's equipment name, which may be null.
    Operation: translates it, folding the variants this application does not model
               (medicine ball, foam roll, an unspecified null) into 'other'.
    Return: the matching Equipment.
    """
    if raw_equipment is None:
        return Equipment.OTHER
    return _EQUIPMENT.get(raw_equipment.strip().lower(), Equipment.OTHER)


def to_category(raw_category: str | None) -> ExerciseCategory:
    """
    Arg: raw_category - the catalogue's category name, which may be null.
    Operation: translates it, defaulting to strength when absent or unrecognised.
    Return: the matching ExerciseCategory.
    """
    if raw_category is None:
        return ExerciseCategory.STRENGTH
    return _CATEGORIES.get(raw_category.strip().lower(), ExerciseCategory.STRENGTH)


def _join_secondary_muscles(raw_muscles: list[str]) -> str | None:
    """
    Arg: raw_muscles - the catalogue's secondaryMuscles list.
    Operation: joins the names into the single column the model stores, clipped to the
               column width so a long list cannot fail the insert.
    Return: the joined string, or None when there are no secondary muscles.
    """
    if not raw_muscles:
        return None
    return ", ".join(raw_muscles)[:SECONDARY_MUSCLES_MAX_LENGTH]


def _join_instructions(raw_instructions: list[str]) -> str | None:
    """
    Arg: raw_instructions - the catalogue's ordered instruction steps.
    Operation: joins the steps into one block, one step per line.
    Return: the joined instructions, or None when the entry has none.
    """
    if not raw_instructions:
        return None
    return "\n".join(step.strip() for step in raw_instructions if step.strip()) or None


def to_catalog_entry(raw_entry: dict) -> CatalogEntry:
    """
    Arg: raw_entry - one object from the catalogue JSON.
    Operation: translates every field into this application's vocabulary.
    Return: the corresponding CatalogEntry.
    """
    category = to_category(raw_entry.get("category"))
    primary_muscle = to_primary_muscle(raw_entry.get("primaryMuscles") or [])
    external_id = raw_entry["id"]
    return CatalogEntry(
        external_id=external_id,
        name=PREFERRED_NAMES.get(external_id, raw_entry["name"]),
        muscle_group=to_muscle_group(primary_muscle, category),
        primary_muscle=primary_muscle,
        secondary_muscles=_join_secondary_muscles(raw_entry.get("secondaryMuscles") or []),
        equipment=to_equipment(raw_entry.get("equipment")),
        category=category,
        instructions=_join_instructions(raw_entry.get("instructions") or []),
    )


def load_catalog(path: Path = CATALOG_PATH) -> list[CatalogEntry]:
    """
    Arg: path - location of the vendored catalogue JSON.
    Operation: reads the file and translates every entry.
    Return: the catalogue as CatalogEntry objects, in file order.
    """
    raw_entries = json.loads(path.read_text(encoding="utf-8"))
    return [to_catalog_entry(entry) for entry in raw_entries]
