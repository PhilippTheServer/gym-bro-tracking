import { Routes } from '@angular/router';

export const exercisesRoutes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./exercise-library/exercise-library.component').then((m) => m.ExerciseLibraryComponent),
  },
  {
    path: ':id',
    loadComponent: () =>
      import('./exercise-detail/exercise-detail.component').then((m) => m.ExerciseDetailComponent),
  },
];
