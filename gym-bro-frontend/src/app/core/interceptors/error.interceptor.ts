import { HttpHandlerFn, HttpInterceptorFn, HttpRequest } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { KeycloakService } from '../auth/keycloak.service';

export const errorInterceptor: HttpInterceptorFn = (
  req: HttpRequest<unknown>,
  next: HttpHandlerFn
) => {
  const kc = inject(KeycloakService);

  return next(req).pipe(
    catchError((error) => {
      if (error.status === 401) kc.logout();
      return throwError(() => error);
    })
  );
};
