# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --prefer-offline

COPY . .
RUN npm run build:prod

# ── Stage 2: Test ─────────────────────────────────────────────────────────────
# Not part of the production build — reached with `docker build --target test .`, which
# fails if a spec fails. Keeps the suite runnable without Chrome installed on the host.
FROM node:22-alpine AS test

WORKDIR /app

RUN apk add --no-cache chromium
ENV CHROME_BIN=/usr/bin/chromium-browser

COPY package*.json ./
RUN npm ci --prefer-offline

COPY . .
RUN npm test

# ── Stage 3: Serve ────────────────────────────────────────────────────────────
FROM nginx:1.27-alpine AS production

# Runtime config generator script
COPY --from=builder /app/dist/gym-bro-frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh && \
    mkdir -p /usr/share/nginx/html/assets

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
