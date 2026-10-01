/**
 * Loaded at runtime by app.config.ts in production.
 * Allows environment-specific config without rebuilding the image.
 */
export interface RuntimeConfig {
  keycloak: {
    url: string;
    realm: string;
    clientId: string;
  };
  apiUrl?: string;
}
