---
name: api-devloper
description: Implement or change FastAPI endpoints in this project's app/ backend, including pytest coverage that verifies the behavior.
metadata:
  short-description: Build project-shaped FastAPI APIs with pytest coverage
---

# API Developer

Use this skill for backend API implementation in `app/`. Start by reading the relevant application code and tests so changes follow the current project structure and behavior.

## Project shape

- FastAPI application setup and router registration live in `app/main.py`.
- Put endpoint modules under `app/api/routers/`; database dependencies are exposed through `app/api/deps.py` and `app/db/database.py`.
- Put SQLAlchemy models under `app/models/` and Pydantic request/response schemas under `app/schemas/`. Update package exports when existing imports rely on them.
- The default database is SQLite at `app.db`. Follow existing SQLAlchemy 2.x model and session patterns, and do not create or modify the real database as part of tests.
- Backend tests live in the repository's `tests/` directory and use pytest.

## Implement and verify

1. Inspect the app factory, neighboring routers, models, schemas, dependency wiring, configuration, and related tests. Use the existing API contract and conventions unless the request specifies a different contract. Current endpoints use `/user` routes, Pydantic response models, and `{code, result}` response bodies; HTTP and validation errors are formatted by handlers in `app/main.py`.
2. Implement the requested behavior in the appropriate layers. Register new routers in the app factory, import new models where needed for metadata registration, and handle expected conflicts or missing records with suitable HTTP status codes. Keep secrets and internal fields out of public responses.
3. Add pytest coverage for the requested behavior, including relevant success paths, validation failures, and error cases. Exercise endpoints through FastAPI's `TestClient`; use an isolated in-memory SQLite engine/session (such as `StaticPool`) or the project's existing test fixture, and ensure test data is cleaned up. Never point tests at `app.db`.
4. Run the full backend suite with `pytest`. Fix failures caused by the change and rerun it. Report the command and outcome; if the environment prevents a clean run, state the exact blocker.

Keep changes scoped to the requested API and its tests. Add dependencies only when the implementation needs them, and update the project's dependency file when doing so.
