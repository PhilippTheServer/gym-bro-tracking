import {
  ApplicationConfig,
  isDevMode,
  provideAppInitializer,
  provideZonelessChangeDetection,
  inject,
} from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideRouter, withComponentInputBinding, withViewTransitions } from '@angular/router';
import { provideServiceWorker } from '@angular/service-worker';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';

import { environment } from '../environments/environment';
import type { RuntimeConfig } from '../environments/runtime-config';
import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { errorInterceptor } from './core/interceptors/error.interceptor';
import { KeycloakService } from './core/auth/keycloak.service';

/**
 * Loads assets/runtime-config.json (written by the container entrypoint) and applies it
 * to the environment object every other module imports, so a single image can be
 * deployed against any Keycloak or API host without a rebuild.
 */
async function loadRuntimeConfig(): Promise<RuntimeConfig | null> {
  const response = await fetch('assets/runtime-config.json', { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`runtime-config.json returned HTTP ${response.status}`);
  }
  const config = (await response.json()) as RuntimeConfig;

  if (config.apiUrl) {
    environment.apiUrl = config.apiUrl;
  }
  if (config.keycloak?.url) {
    environment.keycloak = config.keycloak;
  }
  return config;
}

function initialiseAuth(): Promise<void> {
  const keycloak = inject(KeycloakService);

  // In dev the values in environment.ts are authoritative — there is no entrypoint
  // to write runtime-config.json.
  if (isDevMode()) {
    return keycloak.init();
  }

  return loadRuntimeConfig()
    .catch((error) => {
      console.error('[gym-bro] runtime config unavailable, falling back to build defaults', error);
      return null;
    })
    .then(() => keycloak.init());
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideZonelessChangeDetection(),
    provideRouter(routes, withComponentInputBinding(), withViewTransitions()),
    provideHttpClient(withInterceptors([authInterceptor, errorInterceptor])),
    provideAnimationsAsync(),
    provideServiceWorker('ngsw-worker.js', {
      enabled: !isDevMode(),
      registrationStrategy: 'registerWhenStable:30000',
    }),
    provideAppInitializer(initialiseAuth),
  ],
};
