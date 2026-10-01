// ── Enums ─────────────────────────────────────────────────────────────────────

export type MuscleGroup =
  | 'chest' | 'back' | 'shoulders' | 'biceps' | 'triceps' | 'forearms'
  | 'legs' | 'glutes' | 'core' | 'neck' | 'cardio' | 'full_body';

export type PrimaryMuscle =
  | 'abdominals' | 'abductors' | 'adductors' | 'biceps' | 'calves' | 'chest'
  | 'forearms' | 'glutes' | 'hamstrings' | 'lats' | 'lower_back' | 'middle_back'
  | 'neck' | 'quadriceps' | 'shoulders' | 'traps' | 'triceps';

export type ExerciseCategory =
  | 'strength' | 'stretching' | 'plyometrics' | 'powerlifting'
  | 'olympic_weightlifting' | 'strongman' | 'cardio';

export type Equipment =
  | 'barbell' | 'dumbbell' | 'cable' | 'machine'
  | 'bodyweight' | 'kettlebell' | 'band' | 'other';

export type SetType = 'warmup' | 'working_set' | 'drop_set' | 'until_failure';

// ── Exercise ──────────────────────────────────────────────────────────────────

/** What the library and picker lists return — no instructions, so 876 rows stay light. */
export interface Exercise {
  id: string;
  name: string;
  muscle_group: MuscleGroup;
  primary_muscle: PrimaryMuscle | null;
  equipment: Equipment;
  category: ExerciseCategory | null;
  is_custom: boolean;
  secondary_muscles?: string | null;
  instructions?: string | null;
  created_by?: string | null;
  external_id?: string | null;
}

/** The full record, as the detail endpoint returns it. */
export interface ExerciseDetail extends Exercise {
  secondary_muscles: string | null;
  instructions: string | null;
  created_by: string | null;
  external_id: string | null;
}

export interface ExerciseFilters {
  search?: string;
  muscle_group?: MuscleGroup | null;
  primary_muscle?: PrimaryMuscle | null;
  equipment?: Equipment | null;
  category?: ExerciseCategory | null;
}

// ── Templates ─────────────────────────────────────────────────────────────────

export interface TemplateSet {
  id: string;
  set_type: SetType;
  target_reps: number | null;
  /** With target_reps, makes the target a range: 8 to 12 rather than 8. */
  target_reps_max: number | null;
  target_weight: number | null;
  target_duration_seconds: number | null;
  order: number;
}

export interface TemplateExercise {
  id: string;
  exercise_id: string;
  exercise: Exercise;
  order: number;
  notes: string | null;
  sets: TemplateSet[];
}

export interface WorkoutTemplate {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  estimated_duration_minutes: number | null;
  exercises: TemplateExercise[];
}

// ── Workout Sessions ──────────────────────────────────────────────────────────

export interface SessionSet {
  id: string;
  set_type: SetType;
  weight: number | null;
  reps: number | null;
  duration_seconds: number | null;
  rpe: number | null;
  completed: boolean;
  completed_at: string | null;
  order: number;
  notes: string | null;
}

export interface SessionExercise {
  id: string;
  exercise_id: string;
  exercise: Exercise;
  order: number;
  notes: string | null;
  sets: SessionSet[];
}

export interface WorkoutSession {
  id: string;
  user_id: string;
  template_id: string | null;
  name: string;
  notes: string | null;
  started_at: string;
  completed_at: string | null;
  exercises: SessionExercise[];
}

/** What this user last did for an exercise, used to prefill the sets they are about to log. */
export interface LastPerformanceSet {
  set_type: SetType;
  weight: number | null;
  reps: number | null;
  order: number;
}

export interface LastPerformance {
  exercise_id: string;
  performed_at: string;
  sets: LastPerformanceSet[];
}

export interface SessionExerciseUpdate {
  exercise_id?: string;
  notes?: string | null;
}

// ── Progress ──────────────────────────────────────────────────────────────────

export interface PersonalRecord {
  exercise_id: string;
  exercise_name: string;
  weight: number;
  reps: number;
  achieved_at: string;
  estimated_1rm: number;
}

export interface ExerciseProgressPoint {
  date: string;
  max_weight: number;
  total_volume: number;
  max_reps: number;
  estimated_1rm: number;
}

export interface ExerciseProgress {
  exercise_id: string;
  exercise_name: string;
  muscle_group: string;
  points: ExerciseProgressPoint[];
}

export interface VolumePoint {
  date: string;
  total_volume: number;
  total_sets: number;
}

export interface WorkoutFrequency {
  date: string;
  count: number;
}

export interface ProgressOverview {
  total_workouts: number;
  total_volume: number;
  total_sets: number;
  current_streak: number;
  longest_streak: number;
  personal_records: PersonalRecord[];
  weekly_frequency: WorkoutFrequency[];
  recent_volume: VolumePoint[];
}

// ── Request Types ─────────────────────────────────────────────────────────────

export interface SessionSetCreate {
  set_type: SetType;
  weight?: number | null;
  reps?: number | null;
  duration_seconds?: number | null;
  rpe?: number | null;
  order?: number;
  notes?: string | null;
}

export interface SessionSetUpdate extends Partial<SessionSetCreate> {
  completed?: boolean;
}

export interface SessionExerciseCreate {
  exercise_id: string;
  order?: number;
  notes?: string | null;
  sets?: SessionSetCreate[];
}

export interface WorkoutSessionCreate {
  name: string;
  template_id?: string | null;
  exercises?: SessionExerciseCreate[];
  notes?: string | null;
}

export interface TemplateSetCreate {
  set_type: SetType;
  target_reps?: number | null;
  target_reps_max?: number | null;
  target_weight?: number | null;
  target_duration_seconds?: number | null;
  order?: number;
}

export interface TemplateExerciseCreate {
  exercise_id: string;
  order?: number;
  notes?: string | null;
  sets?: TemplateSetCreate[];
}

export interface WorkoutTemplateCreate {
  name: string;
  description?: string | null;
  estimated_duration_minutes?: number | null;
  exercises?: TemplateExerciseCreate[];
}
