import { Routes } from '@angular/router';

export const templatesRoutes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./template-list/template-list.component').then((m) => m.TemplateListComponent),
  },
  {
    path: 'new',
    loadComponent: () =>
      import('./template-builder/template-builder.component').then((m) => m.TemplateBuilderComponent),
  },
  {
    path: ':id/edit',
    loadComponent: () =>
      import('./template-builder/template-builder.component').then((m) => m.TemplateBuilderComponent),
  },
];
