# Gym Bro

Workout tracker: build templates, run a live session, watch the numbers go up.

Angular 21 PWA on a FastAPI backend, Postgres for storage, Keycloak for login.
Runs as two containers behind a reverse proxy — the frontend serves the app and
proxies `/api/` to the backend, so the browser only ever talks to one origin.

---

## What it does

| Area | Behaviour |
|---|---|
| **Exercise library** | 876 exercises imported from [free-exercise-db](https://github.com/yuhonas/free-exercise-db), filtered by muscle group, primary muscle and equipment, plus your own custom ones |
| **Templates** | Reusable workout plans — drag to reorder, per-exercise notes, rep ranges (8–12), duplicate an existing one or save a finished session as a template. Starting one carries its targets into the workout |
| **Live session** | Start from a template or freestyle. Finished exercises fold away, the one you are on is expanded; reorder, swap or drop an exercise mid-workout; each set shows what you lifted last time; rest timer starts on its own when you tick a set off. Survives a page reload |
| **History** | Every finished session with its full set detail |
| **Progress** | Training streaks, volume over time, weekly frequency, and estimated 1RM personal records (Epley) |

Everything is scoped to the logged-in user — the API resolves ownership from the
token subject and returns `403` for anyone else's records.

---

## Architecture

```
Browser
  │  HTTPS
  ▼
frontend container (nginx)
  ├── serves the Angular bundle
  ├── /assets/runtime-config.json   ← written at container start
  └── /api/  ─── proxy ───▶ backend container (FastAPI, 4 uvicorn workers)
                                │
                                ├── Postgres
                                └── Keycloak (JWKS, token verification)
```

**Runtime configuration.** The image is built once and configured at start. The
entrypoint writes `runtime-config.json` (Keycloak URL, realm, client) and
substitutes the backend address into the nginx config, so the same image runs
locally and in the homelab without a rebuild.

**Auth.** The frontend is a public OIDC client using authorization code + PKCE.
The backend verifies the token signature, expiry and issuer against the realm's
JWKS, and checks the token was issued for this client (`azp`/`aud`). Nothing is
trusted from the request body.

**Migrations.** Alembic runs from the container entrypoint, before uvicorn forks
its workers — schema changes and the catalogue import happen exactly once per start.

**Progressive overload.** Finishing a session that came from a template compares what was
logged against what the template asked for and offers the improvements back, one toggle per
exercise. Only improvements: a session where everything moved down is a bad day, not a new
target, which is why this is a prompt and not automatic. Beating the top of a rep range
carries the range's ceiling up with it, since a target above its own maximum is rejected.

**The live session screen.** Edits are applied locally and sent afterwards, batched over
400 ms, so a held stepper is one request and typing never waits for a round trip. Rest
durations are per exercise and live in `localStorage` — a preference of the device rather
than something the schema should carry. `GET /exercises/{id}/last-performance` returns the
completed sets of the last session that logged this exercise, which is what fills the grey
placeholders.

**Bottom sheets.** Every bottom sheet is a `<dialog class="sheet-backdrop" gbModalSheet>`,
which `ModalSheetDirective` opens with `showModal()`, putting it in the browser's top
layer. Rendered in place, a sheet is a fixed overlay inside the scrolling content, and
iOS WebKit (which every iOS browser uses) clips it to that scroller, cutting off the
strip where the sheet's bottom button sits; nothing clips the top layer. A sheet is shown
with `@if` and closed by removing it. When the browser closes one itself (Escape, a back
gesture), `(dismissed)` must do what the sheet's own Cancel does. The tab bar also steps
out while any sheet is open (`styles.scss`).

**Exercise catalogue.** `gym-bro-backend/data/exercises.json` is the vendored
[free-exercise-db](https://github.com/yuhonas/free-exercise-db) (Unlicense), mapped onto
this application's taxonomy in `app/domain/exercise_catalog.py`. Exercises carry two
levels: the coarse `muscle_group` you browse by and the `primary_muscle` underneath it —
Back splits into lats, mid back, lower back and traps, so a 115-entry group narrows to
something you can pick from.

The import is reconciling, never destructive. `template_exercises.exercise_id` cascades
on delete, so clearing the built-ins and reseeding would silently remove exercises from
existing templates. Catalogue entries are matched onto stored rows by catalogue id first
and normalised name second, then enriched in place, keeping their primary keys. Running
it twice reports `0 new, 0 updated`.

### Backend layout

```
app/
├── api/v1/          # thin route handlers, one call into a use case
├── core/            # settings, database, security
├── domain/
│   ├── models/      # SQLAlchemy entities
│   ├── schemas/     # Pydantic request/response contracts
│   ├── calculations.py  # 1RM, streaks — pure functions
│   └── ordering.py
├── repositories/    # data access, no business rules
└── use_cases/       # one class per business action
```

See [GUIDELINES.md](gym-bro-backend/GUIDELINES.md) for the conventions this
follows.

---

## Running it locally

```bash
docker compose up -d --build
```

Then open <http://localhost> and sign in.

| | |
|---|---|
| App | <http://localhost> |
| API docs | <http://localhost:8000/docs> |
| Keycloak | <http://localhost:8080> (admin / admin) |

The local stack brings its own Keycloak with a `gym-bro` realm and two throwaway
accounts — `lifter` / `lifter` and `spotter` / `spotter`. They exist only in
`keycloak/realm-export.json` for development; the deployed instance uses the
homelab realm instead.

### Tests

Domain tests need nothing. API tests need a Postgres — the compose one works:

```bash
cd gym-bro-backend
docker compose -f ../docker-compose.yml up -d postgres
createdb -h localhost -U gymbro gymbro_test          # once

TEST_DATABASE_URL=postgresql+asyncpg://gymbro:gymbro_secret@localhost:5432/gymbro_test \
  uv run pytest

uv run ruff check . && uv run ruff format --check .
```

Without `TEST_DATABASE_URL` the API tests skip and the domain tests still run.

The frontend suite runs headless Chromium, which the test stage of its image brings
along — nothing to install on the host:

```bash
cd gym-bro-frontend
docker build --target test .        # fails the build if a spec fails
```

With Chrome available locally, `npm test` runs the same suite directly.

### Frontend on its own

```bash
cd gym-bro-frontend
npm ci
npm start          # http://localhost:4200, expects the API on :8000
```

---

## Configuration

Backend (`gym-bro-backend/.env.example`):

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Async Postgres URL |
| `KEYCLOAK_URL` | Where the API reaches Keycloak (JWKS) |
| `KEYCLOAK_PUBLIC_URL` | The URL browsers use — must match the token issuer |
| `KEYCLOAK_REALM` / `KEYCLOAK_CLIENT_ID` | Realm and client to validate against |
| `CORS_ORIGINS` | JSON array; unused when the frontend proxies `/api/` |
| `RUN_SEED` | Seed the exercise library on start (idempotent) |
| `EXPORT_CLIENT_ID` | Keycloak client id of daily's service account; the export API is disabled while this is empty |

Frontend container:

| Variable | Purpose |
|---|---|
| `KEYCLOAK_URL` / `KEYCLOAK_REALM` / `KEYCLOAK_CLIENT_ID` | Written into `runtime-config.json` |
| `API_URL` | API base path — defaults to `/api/v1` (same origin) |
| `BACKEND_URL` | Where nginx proxies `/api/` |

---

## Export API

[daily](https://github.com/PhilippTheServer/daily) pulls finished workouts from here on
a schedule instead of gym-bro pushing anything out, so this stays a read-only integration
point with no knowledge of daily's own schema.

**Auth.** The caller authenticates as its own Keycloak client via the client-credentials
grant (a service account, not a user token). The route accepts any validly signed token
from the realm but rejects it with `403` unless the token's `azp` (authorised party)
claim equals `EXPORT_CLIENT_ID` — it does not accept a regular user's token, and a
user-facing route does not accept this client's token either, since each checks for a
different `azp`.

```
GET /api/v1/export/workouts?user_id=<subject>&completed_after=<RFC 3339 datetime>&limit=100&offset=0
Authorization: Bearer <export client's access token>
```

| Param | Required | Notes |
|---|---|---|
| `user_id` | yes | Keycloak subject of the workout owner |
| `completed_after` | yes | timezone-aware; a naive value is rejected with `422` |
| `limit` | no | 1–100, default 100 |
| `offset` | no | default 0 |

Returns the sessions this user finished strictly after `completed_after`, oldest first,
each a full `WorkoutSessionOut` — the same shape `GET /api/v1/workouts` returns, with its
exercises and sets eager-loaded. Sessions still in progress are never included.

---

## Deployment

Deployed from the [homelab](https://github.com/PhilippTheServer/homelab) repo:
Ansible builds both images on the target, pushes them to the self-hosted Harbor
registry, and runs the stack behind Traefik.

```bash
ansible-playbook ansible/site.yml --tags gym-bro
```

See
`ansible/roles/gym-bro/README.md` in that repo for the details.

**Releasing.** The version lives in four places — `gym-bro-backend/pyproject.toml`
(plus `uv.lock`), `version=` in `gym-bro-backend/app/main.py` (what `/openapi.json`
reports), and `gym-bro-frontend/package.json` (plus `package-lock.json`). Bump all of
them together; `tests/test_version.py` fails if they disagree. The image tag is
`gym_bro_version` in the homelab repo and must be set to the same value.
