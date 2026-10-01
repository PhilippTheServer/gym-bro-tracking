/**
 * The exercise taxonomy, mirroring the backend's two levels: a coarse muscle group you
 * browse by, and the primary muscle underneath it that narrows a 262-entry "legs" list
 * into something you can pick from.
 *
 * Kept free of Angular so it can be tested directly.
 */
import type { Equipment, ExerciseCategory, ExerciseFilters, MuscleGroup, PrimaryMuscle } from './models';

export const MUSCLE_GROUP_LABELS: Record<MuscleGroup, string> = {
  chest: 'Chest',
  back: 'Back',
  shoulders: 'Shoulders',
  biceps: 'Biceps',
  triceps: 'Triceps',
  forearms: 'Forearms',
  legs: 'Legs',
  glutes: 'Glutes',
  core: 'Core',
  neck: 'Neck',
  cardio: 'Cardio',
  full_body: 'Full Body',
};

export const PRIMARY_MUSCLE_LABELS: Record<PrimaryMuscle, string> = {
  abdominals: 'Abs',
  abductors: 'Abductors',
  adductors: 'Adductors',
  biceps: 'Biceps',
  calves: 'Calves',
  chest: 'Chest',
  forearms: 'Forearms',
  glutes: 'Glutes',
  hamstrings: 'Hamstrings',
  lats: 'Lats',
  lower_back: 'Lower Back',
  middle_back: 'Mid Back',
  neck: 'Neck',
  quadriceps: 'Quads',
  shoulders: 'Shoulders',
  traps: 'Traps',
  triceps: 'Triceps',
};

export const EQUIPMENT_LABELS: Record<Equipment, string> = {
  barbell: 'Barbell',
  dumbbell: 'Dumbbell',
  cable: 'Cable',
  machine: 'Machine',
  bodyweight: 'Bodyweight',
  kettlebell: 'Kettlebell',
  band: 'Band',
  other: 'Other',
};

export const CATEGORY_LABELS: Record<ExerciseCategory, string> = {
  strength: 'Strength',
  stretching: 'Stretching',
  plyometrics: 'Plyometrics',
  powerlifting: 'Powerlifting',
  olympic_weightlifting: 'Olympic',
  strongman: 'Strongman',
  cardio: 'Cardio',
};

/** Which primary muscles sit under each group. Must match the backend's roll-up. */
const PRIMARY_MUSCLES_BY_GROUP: Record<MuscleGroup, readonly PrimaryMuscle[]> = {
  chest: ['chest'],
  back: ['lats', 'middle_back', 'lower_back', 'traps'],
  shoulders: ['shoulders'],
  biceps: ['biceps'],
  triceps: ['triceps'],
  forearms: ['forearms'],
  legs: ['quadriceps', 'hamstrings', 'calves', 'adductors', 'abductors'],
  glutes: ['glutes'],
  core: ['abdominals'],
  neck: ['neck'],
  cardio: [],
  full_body: [],
};

export const MUSCLE_GROUPS = Object.keys(MUSCLE_GROUP_LABELS) as MuscleGroup[];
export const EQUIPMENT_TYPES = Object.keys(EQUIPMENT_LABELS) as Equipment[];

/**
 * The primary-muscle chips worth offering for a group. A group with a single muscle
 * underneath it (chest, glutes) gets none — the chips would filter nothing.
 */
export function primaryMusclesFor(group: MuscleGroup | null): readonly PrimaryMuscle[] {
  if (group === null) return [];
  const muscles = PRIMARY_MUSCLES_BY_GROUP[group];
  return muscles.length > 1 ? muscles : [];
}

/** Drops empty filters so the request carries only what actually narrows the library. */
export function toQueryParams(filters: ExerciseFilters): Record<string, string> {
  const params: Record<string, string> = {};
  if (filters.search?.trim()) params['search'] = filters.search.trim();
  if (filters.muscle_group) params['muscle_group'] = filters.muscle_group;
  if (filters.primary_muscle) params['primary_muscle'] = filters.primary_muscle;
  if (filters.equipment) params['equipment'] = filters.equipment;
  if (filters.category) params['category'] = filters.category;
  return params;
}
