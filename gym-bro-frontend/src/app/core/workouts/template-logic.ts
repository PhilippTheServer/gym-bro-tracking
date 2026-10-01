/**
 * Turning templates into sessions and sessions into templates.
 *
 * Pure functions, and deliberately not inlined into the components that need them: the
 * template-to-session mapping used to live in the dashboard, where it quietly sent
 * `target_reps` to an endpoint whose field is `reps` — the API ignored the unknown keys
 * and every templated workout started empty.
 */
import type {
  SessionSetCreate, TemplateSet, TemplateSetCreate, WorkoutSession, WorkoutSessionCreate,
  WorkoutTemplate, WorkoutTemplateCreate,
} from '../api/models';

/** A new exercise lands with a full working set count, not one set to duplicate twice. */
export const DEFAULT_SET_COUNT = 3;

/** Starts a workout from a template, carrying the targets over as the opening numbers. */
export function sessionFromTemplate(template: WorkoutTemplate): WorkoutSessionCreate {
  return {
    name: template.name,
    template_id: template.id,
    exercises: template.exercises.map((entry) => ({
      exercise_id: entry.exercise_id,
      order: entry.order,
      notes: entry.notes,
      sets: entry.sets.map(
        (set, index): SessionSetCreate => ({
          set_type: set.set_type,
          weight: set.target_weight,
          reps: set.target_reps,
          duration_seconds: set.target_duration_seconds,
          order: index,
        })
      ),
    })),
  };
}

/** Keeps a good session as a template. Sets that were ticked off are the ones worth keeping. */
export function templateFromSession(
  session: WorkoutSession,
  name: string
): WorkoutTemplateCreate {
  return {
    name,
    description: null,
    estimated_duration_minutes: durationMinutes(session),
    exercises: session.exercises.map((entry) => {
      const completed = entry.sets.filter((set) => set.completed);
      const sets = completed.length ? completed : entry.sets;
      return {
        exercise_id: entry.exercise_id,
        order: entry.order,
        notes: entry.notes,
        sets: sets.map(
          (set, index): TemplateSetCreate => ({
            set_type: set.set_type,
            target_reps: set.reps,
            target_weight: set.weight,
            target_duration_seconds: set.duration_seconds,
            order: index,
          })
        ),
      };
    }),
  };
}

/** A copy to edit, so a variation does not mean rebuilding the whole thing. */
export function duplicateOf(template: WorkoutTemplate): WorkoutTemplateCreate {
  return {
    name: `${template.name} copy`,
    description: template.description,
    estimated_duration_minutes: template.estimated_duration_minutes,
    exercises: template.exercises.map((entry) => ({
      exercise_id: entry.exercise_id,
      order: entry.order,
      notes: entry.notes,
      sets: entry.sets.map((set, index) => ({
        set_type: set.set_type,
        target_reps: set.target_reps,
        target_reps_max: set.target_reps_max,
        target_weight: set.target_weight,
        target_duration_seconds: set.target_duration_seconds,
        order: index,
      })),
    })),
  };
}

/** The sets a freshly added exercise starts with, copying whatever the last one held. */
export function startingSets(previous?: TemplateSetCreate | TemplateSet): TemplateSetCreate[] {
  return Array.from({ length: DEFAULT_SET_COUNT }, (_, order) => ({
    set_type: previous?.set_type ?? 'working_set',
    target_reps: previous?.target_reps ?? 8,
    target_reps_max: previous?.target_reps_max ?? null,
    target_weight: previous?.target_weight ?? null,
    order,
  }));
}

export function repRangeLabel(
  targetReps: number | null | undefined,
  targetRepsMax: number | null | undefined
): string {
  if (targetReps === null || targetReps === undefined) return '—';
  if (targetRepsMax === null || targetRepsMax === undefined || targetRepsMax === targetReps) {
    return String(targetReps);
  }
  return `${targetReps}–${targetRepsMax}`;
}

function durationMinutes(session: WorkoutSession): number | null {
  if (!session.completed_at) return null;
  const ms = new Date(session.completed_at).getTime() - new Date(session.started_at).getTime();
  const minutes = Math.round(ms / 60000);
  return minutes > 0 ? minutes : null;
}
