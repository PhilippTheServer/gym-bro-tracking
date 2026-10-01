import {
  MUSCLE_GROUPS, MUSCLE_GROUP_LABELS, PRIMARY_MUSCLE_LABELS, primaryMusclesFor, toQueryParams,
} from './exercise-taxonomy';

describe('exercise taxonomy', () => {
  it('offers primary-muscle chips for a group that has several', () => {
    expect(primaryMusclesFor('back')).toEqual(['lats', 'middle_back', 'lower_back', 'traps']);
    expect(primaryMusclesFor('legs').length).toBe(5);
  });

  it('offers no chips where they would filter nothing', () => {
    // Chest holds exactly one primary muscle — a "Chest" chip under "Chest" is noise.
    expect(primaryMusclesFor('chest')).toEqual([]);
    expect(primaryMusclesFor('glutes')).toEqual([]);
    expect(primaryMusclesFor(null)).toEqual([]);
  });

  it('labels every muscle group and primary muscle', () => {
    for (const group of MUSCLE_GROUPS) {
      expect(MUSCLE_GROUP_LABELS[group]).toBeTruthy();
    }
    for (const group of MUSCLE_GROUPS) {
      for (const muscle of primaryMusclesFor(group)) {
        expect(PRIMARY_MUSCLE_LABELS[muscle]).toBeTruthy();
      }
    }
  });

  it('drops empty filters instead of sending blank query parameters', () => {
    // The API rejects muscle_group= with a 422, so an unset filter must not be sent at all.
    expect(toQueryParams({ search: '', muscle_group: null, equipment: null })).toEqual({});
  });

  it('trims the search term and keeps the filters that narrow', () => {
    expect(
      toQueryParams({ search: '  bench  ', muscle_group: 'back', primary_muscle: 'lats' })
    ).toEqual({ search: 'bench', muscle_group: 'back', primary_muscle: 'lats' });
  });
});
