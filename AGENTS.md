# Repository Guidelines

## Project Structure & Module Organization
- `llm-engine/app/` holds the FastAPI service, LLM integrations, Redis/DB managers, and config files.
- `llm-engine/app/test/` contains unit tests (Python `unittest`).
- `llm-engine/app/local_database_setup/` contains scripts and sample data for local MySQL setup.
- `mcp-server/` holds a basic MCP server implementation and tests.
- Root files: `requirements.txt` for dependencies and `README.md` for setup notes.

## Build, Test, and Development Commands
- `pip install -r requirements.txt` installs Python dependencies.
- `cd llm-engine/app && uvicorn app:app --reload --host 127.0.0.1 --port 8000` starts the API locally.
- `python mcp-server/server.py` runs the MCP server (stdio transport).
- `python test_responses.py --question "..." --session_id 123` sends a sample request to a running server.
- `python -m unittest discover -s llm-engine/app/test` runs the test suite.

## Running The Profiler
To run the MCP vs Text2SQL profiler in `llm-engine/app/profiling.py`, use these steps:

1. Ensure Python dependencies are installed with `pip install -r requirements.txt`.
2. Ensure the required backing services are available:
   Redis using the values in `config.json`.
   MySQL using the values in `config.json`.
3. Ensure LLM credentials are present in `llm-engine/app/sensitive/*.txt` and referenced by `llm-engine/app/llm_config.json`.
4. Confirm the benchmark prompt set exists in `llm-engine/app/benchmark_questions.csv`.
5. Run the profiler from the repo root or any working directory with:
   `python /workspace/llm-engine/app/profiling.py --output-csv /workspace/llm-engine/app/profiling_results.csv`
6. For faster smoke runs, limit the benchmark size with:
   `python /workspace/llm-engine/app/profiling.py --question-limit 5 --output-csv /workspace/llm-engine/app/profiling_results.csv`
7. Use `--port` if `8000` is already occupied, for example:
   `python /workspace/llm-engine/app/profiling.py --port 8014 --question-limit 5 --output-csv /workspace/llm-engine/app/profiling_results.csv`
8. The profiler automatically starts the MCP server when running the MCP benchmark mode and starts the FastAPI app separately for MCP and Text2SQL mode.
9. Read the machine-readable benchmark rows from `llm-engine/app/profiling_results.csv`.
10. Read progress and run summary output from the companion text file, by default `llm-engine/app/profiling_results.txt`.
11. Inspect process logs in `llm-engine/app/profiling_logs/`:
   `mcp_app.log`, `text2sql_app.log`, and `mcp_server.log`.
12. Useful optional flags:
   `--benchmark-csv` to choose a different question file.
   `--summary-txt` to choose a different text summary file.
   `--request-timeout` to increase per-question timeout for slower prompts.
   `--startup-timeout` to give the app more time to boot.
   `--log-dir` to choose a different log directory.

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
