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
   This file must contain `question_id`, `category`, and `question`.
5. If you want validation enabled for a run, confirm the validation rules exist in `llm-engine/app/benchmark_validations.json`.
   Validation is disabled by default and only runs when `--validation-json` is provided. Validation rules are keyed by `question_id`; keep expected outcomes in this JSON, not in the benchmark CSV.
6. Run a fast smoke benchmark with:
   `python /workspace/llm-engine/app/profiling.py --port 8018 --question-limit 5 --request-timeout 120 --output-csv /workspace/llm-engine/app/profiling_results.csv`
7. For a fuller benchmark, remove `--question-limit` or increase it:
   `python /workspace/llm-engine/app/profiling.py --port 8018 --request-timeout 180 --output-csv /workspace/llm-engine/app/profiling_results.csv`
8. Use a fresh port with `--port` if another app run is already bound to the default port.
9. The profiler automatically:
   starts the MCP server for the MCP run,
   starts the FastAPI app separately for MCP and Text2SQL mode,
   loads validation rules by `question_id` only when `--validation-json` is provided,
   writes versioned timestamped output files for each run.
10. Read the machine-readable results from the generated timestamped CSV, for example:
   `llm-engine/app/profiling_results_YYYYMMDD_HHMMSS.csv`
11. Read progress and aggregate benchmark stats from the matching timestamped summary text file:
   `llm-engine/app/profiling_results_YYYYMMDD_HHMMSS.txt`
12. Inspect run-specific logs in the timestamped log directory:
   `llm-engine/app/profiling_logs/YYYYMMDD_HHMMSS/`
   Files include `mcp_app.log`, `text2sql_app.log`, and `mcp_server.log`.
13. The profiler records:
   per-row validation outcomes when validation is enabled, otherwise rows are marked with validation disabled,
   client and server latency separately,
   app and MCP startup latency,
   SQL execution outcome fields for Text2SQL,
   token usage when available.
14. Estimated cost fields remain blank unless both `PROFILER_INPUT_COST_PER_1M_TOKENS` and `PROFILER_OUTPUT_COST_PER_1M_TOKENS` are set in the environment before the run.
15. Useful optional flags:
   `--benchmark-csv` to choose a different question file.
   `--validation-json` to enable validation and choose the validation rules file.
   `--summary-txt` to choose a different base summary file name.
   `--request-timeout` to increase per-question timeout for slower prompts.
   `--startup-timeout` to give the app more time to boot.
   `--log-dir` to choose a different base log directory.

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
