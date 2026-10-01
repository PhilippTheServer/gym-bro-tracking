import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.domain.models.template import TemplateExercise
    from app.domain.models.workout import SessionExercise


class MuscleGroup(StrEnum):
    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    FOREARMS = "forearms"
    LEGS = "legs"
    GLUTES = "glutes"
    CORE = "core"
    NECK = "neck"
    CARDIO = "cardio"
    FULL_BODY = "full_body"


class PrimaryMuscle(StrEnum):
    """The muscle a movement actually loads, one level below MuscleGroup."""

    ABDOMINALS = "abdominals"
    ABDUCTORS = "abductors"
    ADDUCTORS = "adductors"
    BICEPS = "biceps"
    CALVES = "calves"
    CHEST = "chest"
    FOREARMS = "forearms"
    GLUTES = "glutes"
    HAMSTRINGS = "hamstrings"
    LATS = "lats"
    LOWER_BACK = "lower_back"
    MIDDLE_BACK = "middle_back"
    NECK = "neck"
    QUADRICEPS = "quadriceps"
    SHOULDERS = "shoulders"
    TRAPS = "traps"
    TRICEPS = "triceps"


class ExerciseCategory(StrEnum):
    STRENGTH = "strength"
    STRETCHING = "stretching"
    PLYOMETRICS = "plyometrics"
    POWERLIFTING = "powerlifting"
    OLYMPIC_WEIGHTLIFTING = "olympic_weightlifting"
    STRONGMAN = "strongman"
    CARDIO = "cardio"


class Equipment(StrEnum):
    BARBELL = "barbell"
    DUMBBELL = "dumbbell"
    CABLE = "cable"
    MACHINE = "machine"
    BODYWEIGHT = "bodyweight"
    KETTLEBELL = "kettlebell"
    BAND = "band"
    OTHER = "other"


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    muscle_group: Mapped[str] = mapped_column(String(30), nullable=False)
    primary_muscle: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    secondary_muscles: Mapped[str | None] = mapped_column(String(255), nullable=True)
    equipment: Mapped[str] = mapped_column(String(30), nullable=False, default=Equipment.BARBELL)
    category: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Identifier from the vendored catalogue. Present only on imported rows, and the
    # handle the importer uses to recognise an exercise it has already seen.
    external_id: Mapped[str | None] = mapped_column(
        String(120), nullable=True, unique=True, index=True
    )

    template_exercises: Mapped[list[TemplateExercise]] = relationship(
        "TemplateExercise", back_populates="exercise"
    )
    session_exercises: Mapped[list[SessionExercise]] = relationship(
        "SessionExercise", back_populates="exercise"
    )
