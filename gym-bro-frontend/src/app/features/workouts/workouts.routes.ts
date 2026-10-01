import { Routes } from '@angular/router';

export const workoutsRoutes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./workout-list/workout-list.component').then((m) => m.WorkoutListComponent),
  },
  {
    path: ':id',
    loadComponent: () =>
      import('./workout-session/workout-session.component').then((m) => m.WorkoutSessionComponent),
  },
];
