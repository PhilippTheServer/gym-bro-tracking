/**
 * The rules the live session screen runs on, kept as pure functions so they can be
 * tested without a browser and reasoned about without reading a component.
 */
import type { LastPerformance, SessionExercise, SessionSet, WorkoutSession } from '../api/models';

/** An exercise is done when it has sets and every one of them is ticked off. */
export function isExerciseComplete(exercise: SessionExercise): boolean {
  return exercise.sets.length > 0 && exercise.sets.every((set) => set.completed);
}

/**
 * The exercise the lifter is on: the first one that still has work left. Returns null
 * once everything is ticked off, which is what turns the screen into "all done".
 */
export function activeExerciseId(session: WorkoutSession | null): string | null {
  if (!session) return null;
  return session.exercises.find((exercise) => !isExerciseComplete(exercise))?.id ?? null;
}

export function completedSetCount(session: WorkoutSession | null): number {
  if (!session) return 0;
  return session.exercises.reduce(
    (total, exercise) => total + exercise.sets.filter((set) => set.completed).length,
    0
  );
}

export function totalSetCount(session: WorkoutSession | null): number {
  if (!session) return 0;
  return session.exercises.reduce((total, exercise) => total + exercise.sets.length, 0);
}

/**
 * Applies a set edit to a copy of the session.
 *
 * The screen used to hand every keystroke to the API and wait for the whole session to
 * come back before showing it, which made typing feel like wading. The edit is applied
 * here first and sent afterwards.
 */
export function applySetUpdate(
  session: WorkoutSession,
  setId: string,
  changes: Partial<SessionSet>
): WorkoutSession {
  return {
    ...session,
    exercises: session.exercises.map((exercise) => ({
      ...exercise,
      sets: exercise.sets.map((set) => (set.id === setId ? { ...set, ...changes } : set)),
    })),
  };
}

/** Drops a set from a copy of the session, for an optimistic delete. */
export function removeSet(session: WorkoutSession, setId: string): WorkoutSession {
  return {
    ...session,
    exercises: session.exercises.map((exercise) => ({
      ...exercise,
      sets: exercise.sets.filter((set) => set.id !== setId),
    })),
  };
}

/** Reorders a copy of the session's exercises, for an optimistic drag-and-drop. */
export function moveExercise(
  session: WorkoutSession,
  fromIndex: number,
  toIndex: number
): WorkoutSession {
  const exercises = [...session.exercises];
  const [moved] = exercises.splice(fromIndex, 1);
  exercises.splice(toIndex, 0, moved);
  return { ...session, exercises: exercises.map((ex, order) => ({ ...ex, order })) };
}

/**
 * What to show greyed out in a set that has not been filled in yet: the matching set from
 * the last time this exercise was trained. Sets beyond what was done last time fall back
 * to the final set, which is what you would repeat anyway.
 */
export function ghostFor(
  performance: LastPerformance | null | undefined,
  setIndex: number
): { weight: number | null; reps: number | null } | null {
  if (!performance || performance.sets.length === 0) return null;
  const reference = performance.sets[Math.min(setIndex, performance.sets.length - 1)];
  if (reference.weight === null && reference.reps === null) return null;
  return { weight: reference.weight, reps: reference.reps };
}

/**
 * The values a newly added set should start from: whatever the previous set holds, or the
 * ghost when the exercise is untouched. Adding a fourth set of the same thing should not
 * mean typing the same numbers a fourth time.
 */
export function nextSetDefaults(
  exercise: SessionExercise,
  performance: LastPerformance | null | undefined
): { set_type: SessionSet['set_type']; weight: number | null; reps: number | null } {
  const previous = exercise.sets[exercise.sets.length - 1];
  if (previous) {
    return {
      set_type: previous.set_type,
      weight: previous.weight,
      reps: previous.reps,
    };
  }
  const ghost = ghostFor(performance, 0);
  return { set_type: 'working_set', weight: ghost?.weight ?? null, reps: ghost?.reps ?? null };
}

/** Weight moves in 2.5 kg steps — the smallest plate pair on most bars. */
export const WEIGHT_STEP = 2.5;

export function stepWeight(current: number | null, direction: 1 | -1): number {
  const next = (current ?? 0) + direction * WEIGHT_STEP;
  return Math.max(0, Math.round(next * 100) / 100);
}

export function stepReps(current: number | null, direction: 1 | -1): number {
  return Math.max(0, (current ?? 0) + direction);
}
