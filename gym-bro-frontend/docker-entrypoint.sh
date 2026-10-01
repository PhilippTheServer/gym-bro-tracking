#!/bin/sh
# Injects environment-specific values into the already-built image so one artifact can
# be deployed anywhere without a rebuild:
#   - assets/runtime-config.json — read by the Angular app during startup
#   - the nginx /api/ proxy target
set -eu

BACKEND_URL="${BACKEND_URL:-http://backend:8000}"

cat > /usr/share/nginx/html/assets/runtime-config.json << EOF
{
  "keycloak": {
    "url": "${KEYCLOAK_URL:-http://localhost:8080}",
    "realm": "${KEYCLOAK_REALM:-gym-bro}",
    "clientId": "${KEYCLOAK_CLIENT_ID:-gym-bro-app}"
  },
  "apiUrl": "${API_URL:-/api/v1}"
}
EOF

sed -i "s|__BACKEND_URL__|${BACKEND_URL}|g" /etc/nginx/conf.d/default.conf

echo "Runtime config written:"
cat /usr/share/nginx/html/assets/runtime-config.json
echo "Backend proxy target: ${BACKEND_URL}"

exec "$@"
