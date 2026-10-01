export const environment = {
  production: true,
  // Same-origin: nginx proxies /api/ to the backend container, so no CORS and no
  // hard-coded host. Overridable at runtime via assets/runtime-config.json.
  apiUrl: '/api/v1',
  keycloak: {
    url: '', // injected at runtime via runtime-config.json
    realm: '',
    clientId: '',
  },
};
