import uuid

from pydantic import BaseModel, ConfigDict, model_validator

from app.domain.models.template import SetType
from app.domain.schemas.exercise import ExerciseOut


class TemplateSetBase(BaseModel):
    set_type: SetType = SetType.WORKING_SET
    target_reps: int | None = None
    # With target_reps, makes the target a range: 8 to 12 rather than 8.
    target_reps_max: int | None = None
    target_weight: float | None = None
    target_duration_seconds: int | None = None
    order: int = 0

    @model_validator(mode="after")
    def _check_rep_range(self) -> TemplateSetBase:
        """
        Arg: none - runs over the populated model.
        Operation: rejects a range whose top is below its bottom, which would otherwise be
                   stored and rendered as "12-8".
        Return: the validated model.
        """
        if (
            self.target_reps is not None
            and self.target_reps_max is not None
            and self.target_reps_max < self.target_reps
        ):
            raise ValueError("target_reps_max must not be below target_reps")
        return self


class TemplateSetCreate(TemplateSetBase):
    # None lets the server order sets by their position in the request.
    order: int | None = None


class TemplateSetOut(TemplateSetBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class TemplateExerciseBase(BaseModel):
    exercise_id: uuid.UUID
    order: int = 0
    notes: str | None = None


class TemplateExerciseCreate(TemplateExerciseBase):
    order: int | None = None
    sets: list[TemplateSetCreate] = []


class TemplateExerciseOut(TemplateExerciseBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    exercise: ExerciseOut
    sets: list[TemplateSetOut] = []


class WorkoutTemplateBase(BaseModel):
    name: str
    description: str | None = None
    estimated_duration_minutes: int | None = None


class WorkoutTemplateCreate(WorkoutTemplateBase):
    exercises: list[TemplateExerciseCreate] = []


class WorkoutTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    estimated_duration_minutes: int | None = None
    exercises: list[TemplateExerciseCreate] | None = None


class WorkoutTemplateOut(WorkoutTemplateBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: str
    exercises: list[TemplateExerciseOut] = []


class WorkoutTemplateSummary(WorkoutTemplateBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    exercise_count: int = 0
