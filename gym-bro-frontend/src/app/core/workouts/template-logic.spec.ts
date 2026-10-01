import {
  DEFAULT_SET_COUNT, duplicateOf, repRangeLabel, sessionFromTemplate, startingSets,
  templateFromSession,
} from './template-logic';
import type { SessionSet, TemplateSet, WorkoutSession, WorkoutTemplate } from '../api/models';

const exercise = {
  id: 'ex-1',
  name: 'Barbell Bench Press',
  muscle_group: 'chest' as const,
  primary_muscle: 'chest' as const,
  equipment: 'barbell' as const,
  category: 'strength' as const,
  is_custom: false,
};

function templateSet(overrides: Partial<TemplateSet> = {}): TemplateSet {
  return {
    id: 'ts-1',
    set_type: 'working_set',
    target_reps: 8,
    target_reps_max: null,
    target_weight: 80,
    target_duration_seconds: null,
    order: 0,
    ...overrides,
  };
}

const template: WorkoutTemplate = {
  id: 'tpl-1',
  user_id: 'u1',
  name: 'Push Day',
  description: 'Chest and triceps',
  estimated_duration_minutes: 60,
  exercises: [
    {
      id: 'te-1',
      exercise_id: 'ex-1',
      exercise,
      order: 0,
      notes: 'Pause on the chest.',
      sets: [templateSet(), templateSet({ id: 'ts-2', order: 1, target_weight: 82.5 })],
    },
  ],
};

function sessionSet(overrides: Partial<SessionSet> = {}): SessionSet {
  return {
    id: 'ss-1',
    set_type: 'working_set',
    weight: 80,
    reps: 8,
    duration_seconds: null,
    rpe: null,
    completed: true,
    completed_at: '2026-09-17T18:30:00Z',
    order: 0,
    notes: null,
    ...overrides,
  };
}

const session: WorkoutSession = {
  id: 's-1',
  user_id: 'u1',
  template_id: null,
  name: 'Freestyle',
  notes: null,
  started_at: '2026-09-17T18:00:00Z',
  completed_at: '2026-09-17T19:05:00Z',
  exercises: [
    {
      id: 'se-1',
      exercise_id: 'ex-1',
      exercise,
      order: 0,
      notes: null,
      sets: [sessionSet(), sessionSet({ id: 'ss-2', order: 1, weight: 85, reps: 6 })],
    },
  ],
};

describe('template logic', () => {
  describe('starting a workout from a template', () => {
    it('carries the targets over as weight and reps', () => {
      // The old mapping sent target_weight/target_reps, which the API has no fields for —
      // it dropped them and every templated workout started with empty sets.
      const started = sessionFromTemplate(template);
      const sets = started.exercises![0].sets!;

      expect(sets[0].weight).toBe(80);
      expect(sets[0].reps).toBe(8);
      expect(sets[1].weight).toBe(82.5);
      expect(Object.keys(sets[0])).not.toContain('target_weight');
    });

    it('links the session back to its template and keeps the notes', () => {
      const started = sessionFromTemplate(template);
      expect(started.template_id).toBe('tpl-1');
      expect(started.name).toBe('Push Day');
      expect(started.exercises![0].notes).toBe('Pause on the chest.');
    });

    it('numbers the sets from zero', () => {
      expect(sessionFromTemplate(template).exercises![0].sets!.map((s) => s.order)).toEqual([0, 1]);
    });
  });

  describe('saving a session as a template', () => {
    it('turns the logged numbers into targets', () => {
      const saved = templateFromSession(session, 'Chest Day');
      const sets = saved.exercises![0].sets!;

      expect(saved.name).toBe('Chest Day');
      expect(sets.map((s) => [s.target_weight, s.target_reps])).toEqual([[80, 8], [85, 6]]);
    });

    it('keeps only the sets that were ticked off', () => {
      const partial: WorkoutSession = {
        ...session,
        exercises: [
          {
            ...session.exercises[0],
            sets: [sessionSet(), sessionSet({ id: 'ss-3', completed: false, weight: 200 })],
          },
        ],
      };
      expect(templateFromSession(partial, 'X').exercises![0].sets!.length).toBe(1);
    });

    it('falls back to every set when nothing was ticked off', () => {
      const untouched: WorkoutSession = {
        ...session,
        exercises: [
          {
            ...session.exercises[0],
            sets: [sessionSet({ completed: false }), sessionSet({ id: 'ss-4', completed: false })],
          },
        ],
      };
      expect(templateFromSession(untouched, 'X').exercises![0].sets!.length).toBe(2);
    });

    it('records how long the session took', () => {
      expect(templateFromSession(session, 'X').estimated_duration_minutes).toBe(65);
    });
  });

  describe('duplicating', () => {
    it('copies the exercises and marks the name as a copy', () => {
      const copy = duplicateOf(template);
      expect(copy.name).toBe('Push Day copy');
      expect(copy.exercises!.length).toBe(1);
      expect(copy.exercises![0].sets!.length).toBe(2);
    });

    it('carries the rep range across', () => {
      const ranged: WorkoutTemplate = {
        ...template,
        exercises: [
          { ...template.exercises[0], sets: [templateSet({ target_reps_max: 12 })] },
        ],
      };
      expect(duplicateOf(ranged).exercises![0].sets![0].target_reps_max).toBe(12);
    });
  });

  describe('starting sets', () => {
    it('gives a new exercise three working sets', () => {
      const sets = startingSets();
      expect(sets.length).toBe(DEFAULT_SET_COUNT);
      expect(sets.map((s) => s.order)).toEqual([0, 1, 2]);
      expect(sets[0].target_reps).toBe(8);
    });

    it('copies the previous set rather than starting blank', () => {
      const sets = startingSets(templateSet({ target_weight: 100, target_reps: 5 }));
      expect(sets.every((s) => s.target_weight === 100 && s.target_reps === 5)).toBeTrue();
    });
  });

  describe('rep range label', () => {
    it('shows a single number, a range, or nothing', () => {
      expect(repRangeLabel(8, null)).toBe('8');
      expect(repRangeLabel(8, 12)).toBe('8–12');
      expect(repRangeLabel(8, 8)).toBe('8');
      expect(repRangeLabel(null, null)).toBe('—');
    });
  });
});
