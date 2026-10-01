import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.models.template import SetType
from app.domain.models.workout import SessionExercise as SessionExerciseEntity
from app.domain.schemas.exercise import ExerciseOut


class SessionSetBase(BaseModel):
    set_type: SetType = SetType.WORKING_SET
    weight: float | None = None
    reps: int | None = None
    duration_seconds: int | None = None
    rpe: float | None = None
    order: int = 0
    notes: str | None = None


class SessionSetCreate(SessionSetBase):
    # None lets the server order sets by their position in the request.
    order: int | None = None


class SessionSetUpdate(BaseModel):
    set_type: SetType | None = None
    weight: float | None = None
    reps: int | None = None
    duration_seconds: int | None = None
    rpe: float | None = None
    completed: bool | None = None
    notes: str | None = None


class SessionSetOut(SessionSetBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    completed: bool
    completed_at: datetime | None = None


class SessionExerciseBase(BaseModel):
    exercise_id: uuid.UUID
    order: int = 0
    notes: str | None = None


class SessionExerciseCreate(SessionExerciseBase):
    order: int | None = None
    sets: list[SessionSetCreate] = []


class SessionExerciseUpdate(BaseModel):
    """Swapping the movement, or leaving a note, without disturbing the logged sets."""

    exercise_id: uuid.UUID | None = None
    notes: str | None = None


class SessionExerciseReorder(BaseModel):
    """The session's exercises, in the order they should now appear."""

    exercise_ids: list[uuid.UUID]


class LastPerformanceSet(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    set_type: SetType
    weight: float | None = None
    reps: int | None = None
    order: int


class LastPerformanceOut(BaseModel):
    """What this user last did for one exercise, to prefill the sets they are about to log."""

    exercise_id: uuid.UUID
    performed_at: datetime
    sets: list[LastPerformanceSet] = []

    @classmethod
    def from_entry(cls, entry: SessionExerciseEntity) -> LastPerformanceOut:
        """
        Arg: entry - the SessionExercise holding the performance.
        Operation: keeps only the sets that were actually completed, in order.
        Return: the LastPerformanceOut for that entry.
        """
        completed = sorted(
            (s for s in entry.sets if s.completed), key=lambda session_set: session_set.order
        )
        return cls(
            exercise_id=entry.exercise_id,
            performed_at=entry.session.completed_at,
            sets=[LastPerformanceSet.model_validate(s) for s in completed],
        )


class SessionExerciseOut(SessionExerciseBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    exercise: ExerciseOut
    sets: list[SessionSetOut] = []


class WorkoutSessionCreate(BaseModel):
    name: str
    template_id: uuid.UUID | None = None
    exercises: list[SessionExerciseCreate] = []
    notes: str | None = None


class WorkoutSessionUpdate(BaseModel):
    name: str | None = None
    notes: str | None = None
    completed_at: datetime | None = None


class WorkoutSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: str
    template_id: uuid.UUID | None
    name: str
    notes: str | None
    started_at: datetime
    completed_at: datetime | None
    exercises: list[SessionExerciseOut] = []


class WorkoutSessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    started_at: datetime
    completed_at: datetime | None
    exercise_count: int = 0
    total_sets: int = 0
    total_volume: float = 0.0
