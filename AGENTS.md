# Repository Guidelines

## Project Structure & Module Organization
- `llm-engine/app/` holds the FastAPI service, LLM integrations, Redis/DB managers, and config files.
- `llm-engine/app/test/` contains unit tests (Python `unittest`).
- `llm-engine/app/local_database_setup/` contains scripts and sample data for local MySQL setup.
- Root files: `requirements.txt` for dependencies and `README.md` for setup notes.

## Build, Test, and Development Commands
- `pip install -r requirements.txt` installs Python dependencies.
- `cd llm-engine/app && uvicorn app:app --reload --host 127.0.0.1 --port 8000` starts the API locally.
- `python test_responses.py --question "..." --session_id 123` sends a sample request to a running server.
- `python -m unittest discover -s llm-engine/app/test` runs the test suite.

## Coding Style & Naming Conventions
- Use 4-space indentation and standard Python import ordering.
- File naming follows mixed patterns: manager classes use `CamelCase.py` (for example, `LLMManager.py`), utilities use `snake_case.py` (for example, `test_responses.py`). Match existing conventions in the touched area.
- No formatter or linter is configured; keep changes minimal and consistent with nearby code.

## Testing Guidelines
- Framework: `unittest` with `Test*` classes and `test_*` methods in `test_*.py` files.
- Some tests require live services (for example, Redis on `localhost:6379`). Note external dependencies in your PR when applicable.

## Commit & Pull Request Guidelines
- Commit messages are short, sentence-case descriptions without prefixes (for example, "Updated devcontainer", "Added threshold info to README"). Follow that style.
- PRs should include: a brief summary, test commands run (or why not), and any config changes (`config.json`, `llm_config.json`, `sensitive/*`). Attach request/response examples when behavior changes.

## Configuration & Secrets
- Store API keys in `llm-engine/app/sensitive/*.txt` and reference them from `llm-engine/app/llm_config.json`.
- Database and Redis connection details live in `llm-engine/app/config.json`.
