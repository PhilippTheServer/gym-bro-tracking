# Vendored exercise catalogue

`exercises.json` is [free-exercise-db](https://github.com/yuhonas/free-exercise-db)'s
`dist/exercises.json`, vendored verbatim so the import needs no network access at
container start.

- **Source:** <https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json>
- **Licence:** Unlicense (public domain)
- **Vendored:** 2026-09-17, 876 entries

Refresh it with:

```bash
curl -sLo data/exercises.json \
  https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json
```

The `images` field is carried along unused — the catalogue is text only. Mapping onto
this application's own taxonomy lives in `app/domain/exercise_catalog.py`; nothing reads
this file directly.
