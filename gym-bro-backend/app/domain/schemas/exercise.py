import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.exercise import Equipment, ExerciseCategory, MuscleGroup, PrimaryMuscle


class ExerciseBase(BaseModel):
    name: str
    muscle_group: MuscleGroup
    primary_muscle: PrimaryMuscle | None = None
    secondary_muscles: str | None = None
    equipment: Equipment = Equipment.BARBELL
    category: ExerciseCategory | None = None
    instructions: str | None = None


class ExerciseCreate(ExerciseBase):
    pass


class ExerciseUpdate(BaseModel):
    name: str | None = None
    muscle_group: MuscleGroup | None = None
    primary_muscle: PrimaryMuscle | None = None
    secondary_muscles: str | None = None
    equipment: Equipment | None = None
    category: ExerciseCategory | None = None
    instructions: str | None = None


class ExerciseOut(ExerciseBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_custom: bool
    created_by: str | None = None
    external_id: str | None = None


class ExerciseSummaryOut(BaseModel):
    """An exercise as the library and picker lists need it.

    Instructions are deliberately absent: the library is 876 entries and sending every
    step of every one of them makes the list several hundred kilobytes for no gain. The
    detail endpoint returns the full record.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    muscle_group: MuscleGroup
    primary_muscle: PrimaryMuscle | None = None
    equipment: Equipment
    category: ExerciseCategory | None = None
    is_custom: bool


class ExerciseFilters(BaseModel):
    """Query parameters narrowing the exercise library."""

    search: str = Field(default="", max_length=100)
    muscle_group: MuscleGroup | None = None
    primary_muscle: PrimaryMuscle | None = None
    equipment: Equipment | None = None
    category: ExerciseCategory | None = None
