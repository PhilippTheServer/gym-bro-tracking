import { Injectable, signal } from '@angular/core';
import Keycloak from 'keycloak-js';
import { environment } from '../../../environments/environment';

export interface UserProfile {
  sub: string;
  name: string;
  email: string;
  preferred_username: string;
  given_name: string;
  family_name: string;
}

@Injectable({ providedIn: 'root' })
export class KeycloakService {
  private _kc!: Keycloak;

  readonly isAuthenticated = signal(false);
  readonly profile = signal<UserProfile | null>(null);
  readonly token = signal<string | null>(null);

  async init(config?: { url: string; realm: string; clientId: string }): Promise<void> {
    const cfg = config ?? environment.keycloak;
    this._kc = new Keycloak({
      url: cfg.url,
      realm: cfg.realm,
      clientId: cfg.clientId,
    });

    const authenticated = await this._kc.init({
      onLoad: 'login-required',
      pkceMethod: 'S256',
      checkLoginIframe: false,
      silentCheckSsoRedirectUri: window.location.origin + '/assets/silent-check-sso.html',
    });

    this.isAuthenticated.set(authenticated);

    if (authenticated) {
      this.token.set(this._kc.token ?? null);
      const p = this._kc.tokenParsed as UserProfile;
      this.profile.set(p);

      this._kc.onTokenExpired = () => this._refreshToken();
    }
  }

  private async _refreshToken(): Promise<void> {
    try {
      const refreshed = await this._kc.updateToken(30);
      if (refreshed) this.token.set(this._kc.token ?? null);
    } catch {
      await this.logout();
    }
  }

  async getToken(): Promise<string> {
    await this._kc.updateToken(30);
    this.token.set(this._kc.token ?? null);
    return this._kc.token ?? '';
  }

  async logout(): Promise<void> {
    await this._kc.logout({ redirectUri: window.location.origin });
  }

  get username(): string {
    return this.profile()?.preferred_username ?? '';
  }

  get displayName(): string {
    return this.profile()?.name ?? this.username;
  }
}
