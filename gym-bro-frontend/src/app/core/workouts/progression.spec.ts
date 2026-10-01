import { applyImprovements, proposeTemplateUpdate } from './progression';
import type {
  SessionExercise, SessionSet, TemplateExercise, TemplateSet, WorkoutSession, WorkoutTemplate,
} from '../api/models';

const bench = {
  id: 'ex-bench',
  name: 'Barbell Bench Press',
  muscle_group: 'chest' as const,
  primary_muscle: 'chest' as const,
  equipment: 'barbell' as const,
  category: 'strength' as const,
  is_custom: false,
};

function targetSet(order: number, overrides: Partial<TemplateSet> = {}): TemplateSet {
  return {
    id: `ts-${order}`,
    set_type: 'working_set',
    target_reps: 8,
    target_reps_max: null,
    target_weight: 80,
    target_duration_seconds: null,
    order,
    ...overrides,
  };
}

function loggedSet(order: number, overrides: Partial<SessionSet> = {}): SessionSet {
  return {
    id: `ss-${order}`,
    set_type: 'working_set',
    weight: 80,
    reps: 8,
    duration_seconds: null,
    rpe: null,
    completed: true,
    completed_at: '2026-09-17T19:00:00Z',
    order,
    notes: null,
    ...overrides,
  };
}

function template(sets: TemplateSet[], entryOverrides: Partial<TemplateExercise> = {}): WorkoutTemplate {
  return {
    id: 'tpl-1',
    user_id: 'u1',
    name: 'Push Day',
    description: null,
    estimated_duration_minutes: 60,
    exercises: [
      {
        id: 'te-1',
        exercise_id: 'ex-bench',
        exercise: bench,
        order: 0,
        notes: 'Pause on the chest.',
        sets,
        ...entryOverrides,
      },
    ],
  };
}

function session(sets: SessionSet[], entryOverrides: Partial<SessionExercise> = {}): WorkoutSession {
  return {
    id: 's-1',
    user_id: 'u1',
    template_id: 'tpl-1',
    name: 'Push Day',
    notes: null,
    started_at: '2026-09-17T18:00:00Z',
    completed_at: '2026-09-17T19:05:00Z',
    exercises: [
      {
        id: 'se-1',
        exercise_id: 'ex-bench',
        exercise: bench,
        order: 0,
        notes: null,
        sets,
        ...entryOverrides,
      },
    ],
  };
}

describe('progressive overload', () => {
  describe('what counts as an improvement', () => {
    it('offers more weight', () => {
      const proposals = proposeTemplateUpdate(
        template([targetSet(0)]),
        session([loggedSet(0, { weight: 82.5 })])
      );
      expect(proposals.length).toBe(1);
      expect(proposals[0].label).toBe('80 kg → 82.5 kg');
      expect(proposals[0].sets[0].toWeight).toBe(82.5);
    });

    it('offers more reps at the same weight', () => {
      const proposals = proposeTemplateUpdate(
        template([targetSet(0)]),
        session([loggedSet(0, { reps: 10 })])
      );
      expect(proposals[0].label).toBe('80 kg × 8 → × 10');
    });

    it('offers loading a movement the template holds at bodyweight', () => {
      const proposals = proposeTemplateUpdate(
        template([targetSet(0, { target_weight: null, target_reps: 10 })]),
        session([loggedSet(0, { weight: 10, reps: 10 })])
      );
      expect(proposals[0].label).toBe('bodyweight → 10 kg');
    });

    it('says nothing when the session matched the targets', () => {
      expect(proposeTemplateUpdate(template([targetSet(0)]), session([loggedSet(0)]))).toEqual([]);
    });

    it('says nothing about a lighter session', () => {
      // A bad day is not a new target.
      const proposals = proposeTemplateUpdate(
        template([targetSet(0)]),
        session([loggedSet(0, { weight: 70, reps: 5 })])
      );
      expect(proposals).toEqual([]);
    });

    it('ignores more reps at a lighter weight', () => {
      const proposals = proposeTemplateUpdate(
        template([targetSet(0)]),
        session([loggedSet(0, { weight: 70, reps: 15 })])
      );
      expect(proposals).toEqual([]);
    });

    it('ignores sets that were never ticked off', () => {
      const proposals = proposeTemplateUpdate(
        template([targetSet(0)]),
        session([loggedSet(0, { weight: 100, completed: false })])
      );
      expect(proposals).toEqual([]);
    });

    it('ignores an exercise swapped in mid-workout', () => {
      const swapped = session([loggedSet(0, { weight: 90 })], { exercise_id: 'ex-dumbbell' });
      expect(proposeTemplateUpdate(template([targetSet(0)]), swapped)).toEqual([]);
    });

    it('reports only the sets that improved', () => {
      const proposals = proposeTemplateUpdate(
        template([targetSet(0), targetSet(1), targetSet(2)]),
        session([loggedSet(0), loggedSet(1, { weight: 85 }), loggedSet(2)])
      );
      expect(proposals[0].sets.map((s) => s.order)).toEqual([1]);
    });
  });

  describe('writing the accepted improvements back', () => {
    it('updates the improved set and leaves the others alone', () => {
      const original = template([targetSet(0), targetSet(1)]);
      const proposals = proposeTemplateUpdate(
        original,
        session([loggedSet(0, { weight: 85 }), loggedSet(1)])
      );

      const payload = applyImprovements(original, proposals);
      const sets = payload.exercises![0].sets!;

      expect(sets[0].target_weight).toBe(85);
      expect(sets[1].target_weight).toBe(80);
    });

    it('leaves the template untouched when nothing is accepted', () => {
      const original = template([targetSet(0)]);
      proposeTemplateUpdate(original, session([loggedSet(0, { weight: 85 })]));

      const payload = applyImprovements(original, []);
      expect(payload.exercises![0].sets![0].target_weight).toBe(80);
    });

    it('keeps the name, description, notes and ordering', () => {
      const original = template([targetSet(0)]);
      const payload = applyImprovements(original, []);

      expect(payload.name).toBe('Push Day');
      expect(payload.estimated_duration_minutes).toBe(60);
      expect(payload.exercises![0].notes).toBe('Pause on the chest.');
      expect(payload.exercises![0].sets![0].order).toBe(0);
    });

    it('carries the top of a rep range along when the reps overtake it', () => {
      // The API rejects target_reps_max below target_reps, so a 8-12 range that gets
      // beaten with 14 reps has to move its ceiling too.
      const original = template([targetSet(0, { target_reps: 8, target_reps_max: 12 })]);
      const proposals = proposeTemplateUpdate(original, session([loggedSet(0, { reps: 14 })]));

      const set = applyImprovements(original, proposals).exercises![0].sets![0];
      expect(set.target_reps).toBe(14);
      expect(set.target_reps_max).toBe(14);
    });

    it('leaves a rep range that still contains the new target', () => {
      const original = template([targetSet(0, { target_reps: 8, target_reps_max: 12 })]);
      const proposals = proposeTemplateUpdate(original, session([loggedSet(0, { reps: 10 })]));

      const set = applyImprovements(original, proposals).exercises![0].sets![0];
      expect(set.target_reps).toBe(10);
      expect(set.target_reps_max).toBe(12);
    });
  });
});
