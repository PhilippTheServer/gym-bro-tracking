import { Routes } from '@angular/router';

export const progressRoutes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./overview/progress-overview.component').then((m) => m.ProgressOverviewComponent),
  },
  {
    path: 'exercise/:id',
    loadComponent: () =>
      import('./exercise-progress/exercise-progress.component').then(
        (m) => m.ExerciseProgressComponent
      ),
  },
];
