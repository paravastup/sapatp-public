# Repository Guidelines

## Project Structure & Module Organization
- Core Django project lives in `atp/`; `manage.py`/`manage_secure.py` are entry points and the `chatbot`, `stockcheck`, and `middleware` apps own AI, SAP, and middleware logic.
- Shared templates and static files sit under `atp/templates/` and `atp/static/`; keep new pages aligned with existing directories.
- Operational assets (Dockerfiles, compose manifests, training utilities) reside at the repository root and in `scripts/`, while SAP SDK binaries remain in `nwrfcsdk/`.

## Build, Test, and Development Commands
- `docker-compose -f docker-compose-port5000-secure.yml up -d` brings up web, MySQL, Redis, and Ollama; follow with `docker-compose -f docker-compose-port5000-secure.yml exec web python manage_secure.py migrate`.
- Without Docker: `python -m venv .venv && pip install -r requirements.txt`, then `python atp/manage_secure.py runserver 0.0.0.0:8000` for local iteration.
- Rebuild assets via `docker-compose -f docker-compose-port5000-secure.yml exec web python manage_secure.py collectstatic --noinput`; retrain models with `python scripts/train_windows_fixed.py` (Windows) or `python scripts/train_basic_gpu.py` (Linux/GPU).

## Coding Style & Naming Conventions
- Apply PEP 8 with 4-space indents, grouped imports, and the type hints/docstrings pattern used in `chatbot/services/ollama_client.py`.
- Use snake_case for modules, CamelCase for models/classes, and kebab-case for URL names; store prompts or helpers inside the owning app.
- Keep views thin—push business logic into services/utilities and configure behavior with environment variables rather than editing `settings_secure.py`.

## Testing Guidelines
- Chatbot smoke scripts: `python atp/test_chatbot_simple.py` and `python atp/test_chat_integration.py`; both require a reachable Ollama endpoint (`OLLAMA_BASE_URL`).
- SAP flows: `python atp/test_bulk_queries.py`; add focused tests under `atp/chatbot/tests/` or the relevant app `tests.py`.
- Run Django suites inside containers via `docker-compose -f docker-compose-port5000-secure.yml exec web python manage_secure.py test` and capture failures in PR notes.

## Commit & Pull Request Guidelines
- Keep commit subjects imperative and concise (~50 characters) to match history (`Fix bulk queries...`, `Enable bulk brand...`); add bodies when rollout context matters.
- Update `CHANGELOG.md` and affected docs/scripts whenever APIs, schemas, or deployment steps shift.
- PRs should outline the problem, solution, verification commands, linked issues, and UI or chatbot transcript screenshots when visuals changed.

## Security & Configuration Notes
- Keep credentials and SAP endpoints in untracked environment files; consult `ADMIN_CREDENTIALS.md` before rotating defaults.
- Leave `nwrfcsdk/` binaries untouched unless coordinating an upgrade and document any version changes in PRs.
- Verify `OLLAMA_*` and database variables in compose overrides before switching environments or running acceptance tests.
