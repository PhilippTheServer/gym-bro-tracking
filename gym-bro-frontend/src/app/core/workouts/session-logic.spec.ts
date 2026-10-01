import {
  activeExerciseId, applySetUpdate, completedSetCount, ghostFor, isExerciseComplete,
  moveExercise, nextSetDefaults, removeSet, stepReps, stepWeight, totalSetCount,
} from './session-logic';
import type { LastPerformance, SessionExercise, SessionSet, WorkoutSession } from '../api/models';

function set(id: string, overrides: Partial<SessionSet> = {}): SessionSet {
  return {
    id,
    set_type: 'working_set',
    weight: null,
    reps: null,
    duration_seconds: null,
    rpe: null,
    completed: false,
    completed_at: null,
    order: 0,
    notes: null,
    ...overrides,
  };
}

function entry(id: string, sets: SessionSet[], exerciseId = 'ex-' + id): SessionExercise {
  return {
    id,
    exercise_id: exerciseId,
    exercise: {
      id: exerciseId,
      name: 'Barbell Bench Press',
      muscle_group: 'chest',
      primary_muscle: 'chest',
      equipment: 'barbell',
      category: 'strength',
      is_custom: false,
    },
    order: 0,
    notes: null,
    sets,
  };
}

function session(exercises: SessionExercise[]): WorkoutSession {
  return {
    id: 's1',
    user_id: 'u1',
    template_id: null,
    name: 'Push Day',
    notes: null,
    started_at: '2026-09-17T18:00:00Z',
    completed_at: null,
    exercises,
  };
}

describe('session logic', () => {
  describe('completion', () => {
    it('counts an exercise as done only when every set is ticked', () => {
      expect(isExerciseComplete(entry('a', [set('1', { completed: true })]))).toBeTrue();
      expect(
        isExerciseComplete(entry('a', [set('1', { completed: true }), set('2')]))
      ).toBeFalse();
    });

    it('does not call an exercise with no sets done', () => {
      // Otherwise adding an exercise mid-workout would immediately collapse it out of sight.
      expect(isExerciseComplete(entry('a', []))).toBeFalse();
    });

    it('points at the first exercise with work left', () => {
      const current = session([
        entry('a', [set('1', { completed: true })]),
        entry('b', [set('2')]),
      ]);
      expect(activeExerciseId(current)).toBe('b');
    });

    it('points nowhere once everything is done', () => {
      expect(activeExerciseId(session([entry('a', [set('1', { completed: true })])]))).toBeNull();
      expect(activeExerciseId(null)).toBeNull();
    });

    it('counts sets across exercises', () => {
      const current = session([
        entry('a', [set('1', { completed: true }), set('2')]),
        entry('b', [set('3', { completed: true })]),
      ]);
      expect(completedSetCount(current)).toBe(2);
      expect(totalSetCount(current)).toBe(3);
    });
  });

  describe('optimistic edits', () => {
    it('applies a change without mutating the session it was given', () => {
      const before = session([entry('a', [set('1')])]);
      const after = applySetUpdate(before, '1', { weight: 80 });

      expect(after.exercises[0].sets[0].weight).toBe(80);
      expect(before.exercises[0].sets[0].weight).toBeNull();
      expect(after).not.toBe(before);
    });

    it('leaves other sets alone', () => {
      const before = session([entry('a', [set('1'), set('2', { reps: 5 })])]);
      const after = applySetUpdate(before, '1', { reps: 8 });
      expect(after.exercises[0].sets[1].reps).toBe(5);
    });

    it('removes a set', () => {
      const after = removeSet(session([entry('a', [set('1'), set('2')])]), '1');
      expect(after.exercises[0].sets.map((s) => s.id)).toEqual(['2']);
    });

    it('renumbers order when an exercise is dragged', () => {
      // The API rejects a reorder that does not cover every exercise, and the screen sorts
      // by the order it holds — so the moved list has to be renumbered, not just reshuffled.
      const after = moveExercise(session([entry('a', []), entry('b', []), entry('c', [])]), 2, 0);
      expect(after.exercises.map((ex) => ex.id)).toEqual(['c', 'a', 'b']);
      expect(after.exercises.map((ex) => ex.order)).toEqual([0, 1, 2]);
    });
  });

  describe('last time', () => {
    const performance: LastPerformance = {
      exercise_id: 'ex-a',
      performed_at: '2026-09-10T18:00:00Z',
      sets: [
        { set_type: 'working_set', weight: 80, reps: 8, order: 0 },
        { set_type: 'working_set', weight: 80, reps: 7, order: 1 },
      ],
    };

    it('matches the set to the same position last time', () => {
      expect(ghostFor(performance, 0)).toEqual({ weight: 80, reps: 8 });
      expect(ghostFor(performance, 1)).toEqual({ weight: 80, reps: 7 });
    });

    it('falls back to the final set for sets beyond last time', () => {
      expect(ghostFor(performance, 5)).toEqual({ weight: 80, reps: 7 });
    });

    it('offers nothing when there is no history', () => {
      expect(ghostFor(null, 0)).toBeNull();
      expect(ghostFor({ ...performance, sets: [] }, 0)).toBeNull();
    });

    it('starts a new set from the previous one', () => {
      const exercise = entry('a', [set('1', { weight: 100, reps: 5, set_type: 'drop_set' })]);
      expect(nextSetDefaults(exercise, performance)).toEqual({
        set_type: 'drop_set',
        weight: 100,
        reps: 5,
      });
    });

    it('starts the first set from last time', () => {
      expect(nextSetDefaults(entry('a', []), performance)).toEqual({
        set_type: 'working_set',
        weight: 80,
        reps: 8,
      });
    });
  });

  describe('steppers', () => {
    it('moves weight by a plate pair and never below zero', () => {
      expect(stepWeight(80, 1)).toBe(82.5);
      expect(stepWeight(80, -1)).toBe(77.5);
      expect(stepWeight(null, 1)).toBe(2.5);
      expect(stepWeight(1, -1)).toBe(0);
    });

    it('avoids floating-point dust', () => {
      expect(stepWeight(0.1, 1)).toBe(2.6);
    });

    it('moves reps one at a time and never below zero', () => {
      expect(stepReps(8, 1)).toBe(9);
      expect(stepReps(0, -1)).toBe(0);
      expect(stepReps(null, 1)).toBe(1);
    });
  });
});
