import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.domain.models.exercise import Exercise


class SetType(StrEnum):
    WARMUP = "warmup"
    WORKING_SET = "working_set"
    DROP_SET = "drop_set"
    UNTIL_FAILURE = "until_failure"


class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    exercises: Mapped[list[TemplateExercise]] = relationship(
        "TemplateExercise",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TemplateExercise.order",
    )


class TemplateExercise(Base):
    __tablename__ = "template_exercises"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workout_templates.id", ondelete="CASCADE"), nullable=False
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    template: Mapped[WorkoutTemplate] = relationship("WorkoutTemplate", back_populates="exercises")
    exercise: Mapped[Exercise] = relationship("Exercise", back_populates="template_exercises")
    sets: Mapped[list[TemplateSet]] = relationship(
        "TemplateSet",
        back_populates="template_exercise",
        cascade="all, delete-orphan",
        order_by="TemplateSet.order",
    )


class TemplateSet(Base):
    __tablename__ = "template_sets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("template_exercises.id", ondelete="CASCADE"),
        nullable=False,
    )
    set_type: Mapped[str] = mapped_column(String(20), nullable=False, default=SetType.WORKING_SET)
    target_reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Set together with target_reps this makes the target a range: 8 to 12 rather than 8.
    target_reps_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    template_exercise: Mapped[TemplateExercise] = relationship(
        "TemplateExercise", back_populates="sets"
    )
