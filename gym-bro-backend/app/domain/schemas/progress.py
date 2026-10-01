import uuid
from datetime import date, datetime

from pydantic import BaseModel


class PersonalRecord(BaseModel):
    exercise_id: uuid.UUID
    exercise_name: str
    weight: float
    reps: int
    achieved_at: datetime
    estimated_1rm: float


class ExerciseProgressPoint(BaseModel):
    date: datetime
    max_weight: float
    total_volume: float
    max_reps: int
    estimated_1rm: float


class ExerciseProgress(BaseModel):
    exercise_id: uuid.UUID
    exercise_name: str
    muscle_group: str
    points: list[ExerciseProgressPoint]


class VolumePoint(BaseModel):
    date: datetime
    total_volume: float
    total_sets: int


class WorkoutFrequency(BaseModel):
    date: date
    count: int


class ProgressOverview(BaseModel):
    total_workouts: int
    total_volume: float
    total_sets: int
    current_streak: int
    longest_streak: int
    personal_records: list[PersonalRecord]
    weekly_frequency: list[WorkoutFrequency]
    recent_volume: list[VolumePoint]
