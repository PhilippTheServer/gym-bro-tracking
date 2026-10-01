/**
 * Carrying a good session back into the template it came from.
 *
 * Only improvements are proposed. A session where everything moved down is a bad day
 * rather than a new target, and quietly dragging the template with it is the reason this
 * is a prompt at all instead of something automatic.
 */
import type {
  SessionSet, TemplateExercise, TemplateSet, WorkoutSession, WorkoutTemplate,
  WorkoutTemplateCreate,
} from '../api/models';

export interface SetImprovement {
  /** Position within the exercise, matching the template's set order. */
  order: number;
  fromWeight: number | null;
  fromReps: number | null;
  toWeight: number | null;
  toReps: number | null;
}

export interface ExerciseImprovement {
  templateExerciseId: string;
  name: string;
  /** One line a person can check at a glance, e.g. "80 → 82.5 kg". */
  label: string;
  sets: SetImprovement[];
}

/** True when the set carries more weight, or the same weight for more reps. */
function isImprovement(target: TemplateSet, achieved: SessionSet): boolean {
  if (!achieved.completed) return false;

  const targetWeight = target.target_weight;
  const achievedWeight = achieved.weight;

  if (achievedWeight !== null && targetWeight !== null && achievedWeight > targetWeight) {
    return true;
  }
  // Loading a movement the template holds at bodyweight is progress too.
  if (targetWeight === null && achievedWeight !== null && achievedWeight > 0) return true;

  const sameWeight = achievedWeight === targetWeight;
  if (!sameWeight || achieved.reps === null) return false;
  return target.target_reps === null || achieved.reps > target.target_reps;
}

function weightLabel(weight: number | null): string {
  return weight === null ? 'bodyweight' : `${weight} kg`;
}

function improvementLabel(first: SetImprovement): string {
  if (first.toWeight !== first.fromWeight) {
    return `${weightLabel(first.fromWeight)} → ${weightLabel(first.toWeight)}`;
  }
  return `${weightLabel(first.toWeight)} × ${first.fromReps ?? '—'} → × ${first.toReps ?? '—'}`;
}

/**
 * Compares what was logged against what the template asked for.
 *
 * Exercises are matched by the exercise they point at, each session entry claimed once, so
 * an exercise swapped in mid-workout has nothing in the template to improve on and is
 * left out rather than overwriting an unrelated entry.
 */
export function proposeTemplateUpdate(
  template: WorkoutTemplate,
  session: WorkoutSession
): ExerciseImprovement[] {
  const claimed = new Set<string>();
  const proposals: ExerciseImprovement[] = [];

  for (const templateEntry of template.exercises) {
    const sessionEntry = session.exercises.find(
      (entry) => entry.exercise_id === templateEntry.exercise_id && !claimed.has(entry.id)
    );
    if (!sessionEntry) continue;
    claimed.add(sessionEntry.id);

    const completed = sessionEntry.sets.filter((set) => set.completed);
    const sets = improvedSets(templateEntry, completed);
    if (!sets.length) continue;

    proposals.push({
      templateExerciseId: templateEntry.id,
      name: templateEntry.exercise.name,
      label: improvementLabel(sets[0]),
      sets,
    });
  }

  return proposals;
}

function improvedSets(
  templateEntry: TemplateExercise,
  completed: SessionSet[]
): SetImprovement[] {
  const improvements: SetImprovement[] = [];
  templateEntry.sets.forEach((target, index) => {
    const achieved = completed[index];
    if (!achieved || !isImprovement(target, achieved)) return;
    improvements.push({
      order: target.order,
      fromWeight: target.target_weight,
      fromReps: target.target_reps,
      toWeight: achieved.weight,
      toReps: achieved.reps,
    });
  });
  return improvements;
}

/**
 * Builds the template payload with the accepted improvements folded in. Everything not
 * accepted is sent back exactly as it was.
 */
export function applyImprovements(
  template: WorkoutTemplate,
  accepted: ExerciseImprovement[]
): WorkoutTemplateCreate {
  const byExercise = new Map(accepted.map((entry) => [entry.templateExerciseId, entry]));

  return {
    name: template.name,
    description: template.description,
    estimated_duration_minutes: template.estimated_duration_minutes,
    exercises: template.exercises.map((entry) => {
      const improvement = byExercise.get(entry.id);
      return {
        exercise_id: entry.exercise_id,
        order: entry.order,
        notes: entry.notes,
        sets: entry.sets.map((set, index) => {
          const change = improvement?.sets.find((s) => s.order === set.order);
          if (!change) {
            return {
              set_type: set.set_type,
              target_reps: set.target_reps,
              target_reps_max: set.target_reps_max,
              target_weight: set.target_weight,
              target_duration_seconds: set.target_duration_seconds,
              order: index,
            };
          }
          const targetReps = change.toReps ?? set.target_reps;
          return {
            set_type: set.set_type,
            target_reps: targetReps,
            // A range whose top ends up below its bottom is rejected by the API, so a rep
            // count that overtakes the range carries the top along with it.
            target_reps_max: raisedCeiling(set.target_reps_max, targetReps),
            target_weight: change.toWeight ?? set.target_weight,
            target_duration_seconds: set.target_duration_seconds,
            order: index,
          };
        }),
      };
    }),
  };
}

function raisedCeiling(ceiling: number | null, targetReps: number | null): number | null {
  if (ceiling === null || targetReps === null) return ceiling;
  return Math.max(ceiling, targetReps);
}
