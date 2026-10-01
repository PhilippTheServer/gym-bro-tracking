from app.domain.schemas.exercise import ExerciseCreate, ExerciseOut, ExerciseUpdate
from app.domain.schemas.progress import (
    ExerciseProgress,
    PersonalRecord,
    ProgressOverview,
)
from app.domain.schemas.template import (
    TemplateExerciseCreate,
    TemplateExerciseOut,
    TemplateSetCreate,
    TemplateSetOut,
    WorkoutTemplateCreate,
    WorkoutTemplateOut,
    WorkoutTemplateSummary,
    WorkoutTemplateUpdate,
)
from app.domain.schemas.workout import (
    SessionExerciseCreate,
    SessionExerciseOut,
    SessionSetCreate,
    SessionSetOut,
    SessionSetUpdate,
    WorkoutSessionCreate,
    WorkoutSessionOut,
    WorkoutSessionSummary,
    WorkoutSessionUpdate,
)

__all__ = [
    "ExerciseCreate",
    "ExerciseOut",
    "ExerciseUpdate",
    "WorkoutTemplateCreate",
    "WorkoutTemplateOut",
    "WorkoutTemplateSummary",
    "WorkoutTemplateUpdate",
    "TemplateExerciseCreate",
    "TemplateExerciseOut",
    "TemplateSetCreate",
    "TemplateSetOut",
    "WorkoutSessionCreate",
    "WorkoutSessionOut",
    "WorkoutSessionSummary",
    "WorkoutSessionUpdate",
    "SessionExerciseCreate",
    "SessionExerciseOut",
    "SessionSetCreate",
    "SessionSetOut",
    "SessionSetUpdate",
    "ExerciseProgress",
    "PersonalRecord",
    "ProgressOverview",
]
