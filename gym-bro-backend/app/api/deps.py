"""FastAPI dependency factories for injecting use cases into route handlers."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.template_repository import TemplateRepository
from app.repositories.workout_repository import WorkoutRepository
from app.use_cases.exercise.create_exercise import CreateExerciseUseCase
from app.use_cases.exercise.delete_exercise import DeleteExerciseUseCase
from app.use_cases.exercise.get_exercise import GetExerciseUseCase
from app.use_cases.exercise.list_exercises import ListExercisesUseCase
from app.use_cases.exercise.list_recent_exercises import ListRecentExercisesUseCase
from app.use_cases.exercise.update_exercise import UpdateExerciseUseCase
from app.use_cases.progress.get_exercise_progress import GetExerciseProgressUseCase
from app.use_cases.progress.get_progress_overview import GetProgressOverviewUseCase
from app.use_cases.template.create_template import CreateTemplateUseCase
from app.use_cases.template.delete_template import DeleteTemplateUseCase
from app.use_cases.template.get_template import GetTemplateUseCase
from app.use_cases.template.list_templates import ListTemplatesUseCase
from app.use_cases.template.update_template import UpdateTemplateUseCase
from app.use_cases.workout.add_exercise_to_session import AddExerciseToSessionUseCase
from app.use_cases.workout.add_set import AddSetUseCase
from app.use_cases.workout.delete_session import DeleteSessionUseCase
from app.use_cases.workout.delete_set import DeleteSetUseCase
from app.use_cases.workout.export_sessions import ExportSessionsUseCase
from app.use_cases.workout.finish_session import FinishSessionUseCase
from app.use_cases.workout.get_active_session import GetActiveSessionUseCase
from app.use_cases.workout.get_last_performance import GetLastPerformanceUseCase
from app.use_cases.workout.get_session import GetSessionUseCase
from app.use_cases.workout.list_sessions import ListSessionsUseCase
from app.use_cases.workout.remove_exercise_from_session import RemoveExerciseFromSessionUseCase
from app.use_cases.workout.reorder_session_exercises import ReorderSessionExercisesUseCase
from app.use_cases.workout.start_session import StartSessionUseCase
from app.use_cases.workout.update_session import UpdateSessionUseCase
from app.use_cases.workout.update_session_exercise import UpdateSessionExerciseUseCase
from app.use_cases.workout.update_set import UpdateSetUseCase

DB = Annotated[AsyncSession, Depends(get_db)]


# ── Exercise factories ────────────────────────────────────────────────────────


def get_list_exercises_use_case(db: DB) -> ListExercisesUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs ListExercisesUseCase with an ExerciseRepository.
    Return: ListExercisesUseCase instance.
    """
    return ListExercisesUseCase(ExerciseRepository(db))


def get_list_recent_exercises_use_case(db: DB) -> ListRecentExercisesUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs ListRecentExercisesUseCase with an ExerciseRepository.
    Return: ListRecentExercisesUseCase instance.
    """
    return ListRecentExercisesUseCase(ExerciseRepository(db))


def get_get_exercise_use_case(db: DB) -> GetExerciseUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs GetExerciseUseCase with an ExerciseRepository.
    Return: GetExerciseUseCase instance.
    """
    return GetExerciseUseCase(ExerciseRepository(db))


def get_create_exercise_use_case(db: DB) -> CreateExerciseUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs CreateExerciseUseCase with an ExerciseRepository.
    Return: CreateExerciseUseCase instance.
    """
    return CreateExerciseUseCase(ExerciseRepository(db))


def get_update_exercise_use_case(db: DB) -> UpdateExerciseUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs UpdateExerciseUseCase with an ExerciseRepository.
    Return: UpdateExerciseUseCase instance.
    """
    return UpdateExerciseUseCase(ExerciseRepository(db))


def get_delete_exercise_use_case(db: DB) -> DeleteExerciseUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs DeleteExerciseUseCase with an ExerciseRepository.
    Return: DeleteExerciseUseCase instance.
    """
    return DeleteExerciseUseCase(ExerciseRepository(db))


# ── Template factories ────────────────────────────────────────────────────────


def get_list_templates_use_case(db: DB) -> ListTemplatesUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs ListTemplatesUseCase with a TemplateRepository.
    Return: ListTemplatesUseCase instance.
    """
    return ListTemplatesUseCase(TemplateRepository(db))


def get_get_template_use_case(db: DB) -> GetTemplateUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs GetTemplateUseCase with a TemplateRepository.
    Return: GetTemplateUseCase instance.
    """
    return GetTemplateUseCase(TemplateRepository(db))


def get_create_template_use_case(db: DB) -> CreateTemplateUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs CreateTemplateUseCase with a TemplateRepository.
    Return: CreateTemplateUseCase instance.
    """
    return CreateTemplateUseCase(TemplateRepository(db))


def get_update_template_use_case(db: DB) -> UpdateTemplateUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs UpdateTemplateUseCase with a TemplateRepository.
    Return: UpdateTemplateUseCase instance.
    """
    return UpdateTemplateUseCase(TemplateRepository(db))


def get_delete_template_use_case(db: DB) -> DeleteTemplateUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs DeleteTemplateUseCase with a TemplateRepository.
    Return: DeleteTemplateUseCase instance.
    """
    return DeleteTemplateUseCase(TemplateRepository(db))


# ── Workout factories ─────────────────────────────────────────────────────────


def get_list_sessions_use_case(db: DB) -> ListSessionsUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs ListSessionsUseCase with a WorkoutRepository.
    Return: ListSessionsUseCase instance.
    """
    return ListSessionsUseCase(WorkoutRepository(db))


def get_get_session_use_case(db: DB) -> GetSessionUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs GetSessionUseCase with a WorkoutRepository.
    Return: GetSessionUseCase instance.
    """
    return GetSessionUseCase(WorkoutRepository(db))


def get_get_active_session_use_case(db: DB) -> GetActiveSessionUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs GetActiveSessionUseCase with a WorkoutRepository.
    Return: GetActiveSessionUseCase instance.
    """
    return GetActiveSessionUseCase(WorkoutRepository(db))


def get_start_session_use_case(db: DB) -> StartSessionUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs StartSessionUseCase with a WorkoutRepository.
    Return: StartSessionUseCase instance.
    """
    return StartSessionUseCase(WorkoutRepository(db))


def get_update_session_use_case(db: DB) -> UpdateSessionUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs UpdateSessionUseCase with a WorkoutRepository.
    Return: UpdateSessionUseCase instance.
    """
    return UpdateSessionUseCase(WorkoutRepository(db))


def get_finish_session_use_case(db: DB) -> FinishSessionUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs FinishSessionUseCase with a WorkoutRepository.
    Return: FinishSessionUseCase instance.
    """
    return FinishSessionUseCase(WorkoutRepository(db))


def get_delete_session_use_case(db: DB) -> DeleteSessionUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs DeleteSessionUseCase with a WorkoutRepository.
    Return: DeleteSessionUseCase instance.
    """
    return DeleteSessionUseCase(WorkoutRepository(db))


def get_add_exercise_to_session_use_case(db: DB) -> AddExerciseToSessionUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs AddExerciseToSessionUseCase with a WorkoutRepository.
    Return: AddExerciseToSessionUseCase instance.
    """
    return AddExerciseToSessionUseCase(WorkoutRepository(db))


def get_remove_exercise_from_session_use_case(db: DB) -> RemoveExerciseFromSessionUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs RemoveExerciseFromSessionUseCase with a WorkoutRepository.
    Return: RemoveExerciseFromSessionUseCase instance.
    """
    return RemoveExerciseFromSessionUseCase(WorkoutRepository(db))


def get_reorder_session_exercises_use_case(db: DB) -> ReorderSessionExercisesUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs ReorderSessionExercisesUseCase with a WorkoutRepository.
    Return: ReorderSessionExercisesUseCase instance.
    """
    return ReorderSessionExercisesUseCase(WorkoutRepository(db))


def get_update_session_exercise_use_case(db: DB) -> UpdateSessionExerciseUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs UpdateSessionExerciseUseCase with a WorkoutRepository.
    Return: UpdateSessionExerciseUseCase instance.
    """
    return UpdateSessionExerciseUseCase(WorkoutRepository(db))


def get_last_performance_use_case(db: DB) -> GetLastPerformanceUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs GetLastPerformanceUseCase with a WorkoutRepository.
    Return: GetLastPerformanceUseCase instance.
    """
    return GetLastPerformanceUseCase(WorkoutRepository(db))


def get_add_set_use_case(db: DB) -> AddSetUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs AddSetUseCase with a WorkoutRepository.
    Return: AddSetUseCase instance.
    """
    return AddSetUseCase(WorkoutRepository(db))


def get_update_set_use_case(db: DB) -> UpdateSetUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs UpdateSetUseCase with a WorkoutRepository.
    Return: UpdateSetUseCase instance.
    """
    return UpdateSetUseCase(WorkoutRepository(db))


def get_delete_set_use_case(db: DB) -> DeleteSetUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs DeleteSetUseCase with a WorkoutRepository.
    Return: DeleteSetUseCase instance.
    """
    return DeleteSetUseCase(WorkoutRepository(db))


def get_export_sessions_use_case(db: DB) -> ExportSessionsUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs ExportSessionsUseCase with a WorkoutRepository.
    Return: ExportSessionsUseCase instance.
    """
    return ExportSessionsUseCase(WorkoutRepository(db))


# ── Progress factories ────────────────────────────────────────────────────────


def get_progress_overview_use_case(db: DB) -> GetProgressOverviewUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs GetProgressOverviewUseCase with the raw session for aggregate queries.
    Return: GetProgressOverviewUseCase instance.
    """
    return GetProgressOverviewUseCase(db)


def get_exercise_progress_use_case(db: DB) -> GetExerciseProgressUseCase:
    """
    Arg: db - request-scoped async database session.
    Operation: constructs GetExerciseProgressUseCase with the raw session for aggregate queries.
    Return: GetExerciseProgressUseCase instance.
    """
    return GetExerciseProgressUseCase(db)
