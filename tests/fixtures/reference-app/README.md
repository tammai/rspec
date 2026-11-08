# Reference task app (rspec test fixture)

A small HTTP API that `/rspec:verify` records against, with its spec in `docs/`.

Start it from this folder: `python3 -m app --port 8765`, then `ACCEPT_BASE_URL` is the address it prints.

## API

- `POST /api/tasks` with `{"title": "..."}` and `Authorization: Bearer member`: 201 with `id`, `key` (`TSK-<n>`) and `title`; 401 without the header; 422 for an empty title.
- `GET /api/tasks`: `count` and `items`. `GET /api/tasks/<id>`: the task, or 404.
- `GET /api/stats`: `count` of tasks.
- `POST /api/reset`: clears every task (for seeding).

## Planted for the acceptance run

- `F-TSK-01.AC2` says 400 for an empty title; the app answers 422. The judge should call it `spec-wrong`.
- `GET /api/stats` answers 503 on every second call. `F-TSK-03.AC1` should be reported `flaky`.
