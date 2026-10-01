import { Routes } from '@angular/router';
import { authGuard } from './core/auth/auth.guard';

// AppComponent is the bootstrapped root and already renders the shell (nav + outlet),
// so these routes hang directly off its outlet — routing to AppComponent again would
// nest a second shell inside the first.
export const routes: Routes = [
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full',
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
  },
  {
    path: 'workouts',
    canActivate: [authGuard],
    loadChildren: () =>
      import('./features/workouts/workouts.routes').then((m) => m.workoutsRoutes),
  },
  {
    path: 'templates',
    canActivate: [authGuard],
    loadChildren: () =>
      import('./features/templates/templates.routes').then((m) => m.templatesRoutes),
  },
  {
    path: 'exercises',
    canActivate: [authGuard],
    loadChildren: () =>
      import('./features/exercises/exercises.routes').then((m) => m.exercisesRoutes),
  },
  {
    path: 'progress',
    canActivate: [authGuard],
    loadChildren: () =>
      import('./features/progress/progress.routes').then((m) => m.progressRoutes),
  },
  { path: '**', redirectTo: 'dashboard' },
];
