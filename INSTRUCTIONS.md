# INSTRUCTIONS.md — AI Workflow Guide

This document provides everything an LLM (Claude, GPT, Gemini, etc.) needs to build, run, and test the **norp-llm** project. Ingest this file to enable a seamless AI-assisted development workflow.

---

## Project Overview

**norp-llm** is a FastAPI-based data assistant for benchmarking and serving natural-language data queries.
It supports two primary execution paths:

- **MCP mode:** the app answers questions by calling tools exposed by the MCP server
- **Text2SQL mode:** the app generates SQL directly, executes it against MySQL/MariaDB, and formats the result

The repository also includes a benchmark profiler that runs both modes against the same prompt set and writes timestamped CSV, summary, and log artifacts for comparison.

**Tech stack:** Python 3.9+, FastAPI, Redis, MySQL/MariaDB, LangChain-based LLM integrations, and MCP (Model Context Protocol).

---

## Project Structure

```
norp-llm/
├── config.json                         # Root DB + Redis configuration
├── requirements.txt                    # Python dependencies
├── README.md                           # User-facing setup and usage notes
├── INSTRUCTIONS.md                     # AI workflow guide for this repo
├── AGENTS.md                           # Contributor/repo-specific guidance
├── docs/
│   ├── TOOLS.md                        # MCP tool catalog and testing notes
│   └── CURL_EXAMPLES.md                # Example HTTP requests
├── llm-engine/
│   ├── setup.py                        # Package metadata
│   └── app/
│       ├── app.py                      # Main FastAPI application
│       ├── server.py                   # Supporting app entry logic
│       ├── profiling.py                # MCP vs Text2SQL benchmark runner
│       ├── prompts.py                  # Prompt text and prompt helpers
│       ├── LLMManager.py               # LLM provider/model orchestration
│       ├── DatabaseManager.py          # Database access layer
│       ├── RedisManager.py             # Redis/session state management
│       ├── ServiceManager.py           # Shared service wiring
│       ├── summarizer.py               # Conversation summarization support
│       ├── constants.py                # Shared constants
│       ├── util.py                     # Utility helpers
│       ├── llm_config.json             # LLM config and secret file references
│       ├── benchmark_questions.csv     # Profiler benchmark prompt set
│       ├── benchmark_validations.json  # Optional profiler validation rules
│       ├── test_responses.py           # Manual API query script
│       ├── local_database_setup/       # Schema/data bootstrap scripts and sample data
│       └── test/                       # Python unittest suite
└── mcp-server/
    ├── server.py                       # MCP server entrypoint
    ├── test_mcp_server.py              # MCP server tests
    ├── query_db.py                     # DB query helper
    └── tools/                          # MCP tool implementations
```

---

## Prerequisites

- **Python:** 3.9 or higher (3.11 recommended; devcontainer uses 3.11)
- **Redis:** Running instance (default: localhost:6379 or devcontainer: redis-server:6379)
- **MySQL/MariaDB:** Running instance (devcontainer: mysql:3306, host port 3307)
- **LLM API key:** OpenAI, Together AI, or other provider (see Configuration)

---

## Build & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configuration Files

**`config.json`** (repo root) — Database and Redis:

```json
{
  "db_url": "mysql+mysqlconnector://root:root@mysql/local_norp",
  "db_username": "root",
  "db_password": "root",
  "redis_host_url": "redis-server",
  "redis_port": "6379",
  "redis_password": "redis"
}
```

- **Devcontainer:** Use `mysql` and `redis-server` as hosts.
- **Local:** Use `localhost` and adjust ports (e.g., 3307 for MySQL, 6379 for Redis).

**`llm-engine/app/llm_config.json`** — LLM provider:

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key_path": "sensitive/openai.txt"
  }
}
```

Supported providers: `openai`, `togetherai`, etc. Ensure `api_key_path` points to a file containing the API key.

**API keys:** Create `llm-engine/app/sensitive/openai.txt` (or `togetherai.txt`, etc.) with the raw API key. Do not commit these files.

### 3. Database Setup (Local / Devcontainer)

Run the table creation script (from repo root or `llm-engine/app/local_database_setup/`):

```bash
cd llm-engine/app/local_database_setup
python create_NORP_tables.py
```

This creates tables such as `us_shootings`, `experiencing_homelessness_age_demographics`, etc., and loads sample data.

---

## Running the Application

### Option A: Devcontainer (Recommended)

1. Open repo in VS Code.
2. Ensure Docker is running.
3. Run: **Dev Containers: Reopen in Container**.
4. Wait for container build (Python deps, MariaDB, Redis).
5. Inside the container, follow "Option B" below.

### Option B: Manual Run

**Step 1 — Start MCP server** (required before the main app):

```bash
python mcp-server/server.py
```

Keep this running in one terminal (stdio transport).

**Step 2 — Start FastAPI app** (in another terminal):

```bash
cd llm-engine/app
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

API base URL: `http://127.0.0.1:8000`

---

## Running the Profiler

Use `llm-engine/app/profiling.py` to compare MCP mode and Text2SQL mode with the same benchmark questions.

### Quick Steps

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Make sure the required services and config are ready:
- Redis is reachable using values from `config.json`
- MySQL/MariaDB is reachable using values from `config.json`
- `llm-engine/app/llm_config.json` points to a valid API key file in `llm-engine/app/sensitive/`
- `llm-engine/app/benchmark_questions.csv` exists and contains `question_id`, `category`, and `question`

3. Run the profiler from the repo root:

```bash
python /workspace/llm-engine/app/profiling.py --port 8018 --request-timeout 180 --output-csv /workspace/llm-engine/app/profiling_results.csv
```

This default command writes timestamped profiler artifacts and lets the script start the MCP server and both app modes automatically.

4. For a quick smoke run, limit the number of questions:

```bash
python /workspace/llm-engine/app/profiling.py --port 8018 --question-limit 5 --request-timeout 120 --output-csv /workspace/llm-engine/app/profiling_results.csv
```

### Common Optional Flags

- `--benchmark-csv` to use a different benchmark CSV
- `--validation-json` to enable question validation using rules keyed by `question_id`
- `--output-csv` to choose the base CSV output path
- `--summary-txt` to choose the base summary text path
- `--host` to change the app host used by the profiler
- `--port` to use a different app port
- `--startup-timeout` to wait longer for the app to boot
- `--request-timeout` to allow slower prompts to complete
- `--log-dir` to choose a different base directory for run logs
- `--limit` or `--question-limit` to run only the first N benchmark questions

### Generated Artifacts

Each run creates timestamped outputs, including:

- A results CSV such as `llm-engine/app/profiling_results_YYYYMMDD_HHMMSS.csv`
- A summary text file with progress and aggregate stats
- A log directory such as `llm-engine/app/profiling_logs/YYYYMMDD_HHMMSS/`

When validation is enabled with `--validation-json`, the profiler records per-question validation outcomes in the output CSV.

---

## Testing

Before choosing a test path or forming tool-based prompts, read `docs/TOOLS.md` for the current MCP tool inventory and example queries. This is the source of truth for which tools are available to test.

### 1. Manual API Test

With the app running:

```bash
cd llm-engine/app
python test_responses.py --question "Show me 5 shootings in Virgina" --session_id 585
```

Or from repo root:

```bash
python llm-engine/app/test_responses.py --question "Show me 5 shootings in Virginia" --session_id 999
```

For aggregation questions (uses `execute_sql`):

```bash
python llm-engine/app/test_responses.py --question "How many shootings were there in Mississippi in January 2014?" --session_id 999
```

### 2. Unit Tests

```bash
python -m unittest discover -s llm-engine/app/test
```

**Note:** Some tests require live Redis (e.g., `localhost:6379`). Devcontainer Redis uses port 6380 on host; unit tests may need adjustment for that.

### 3. MCP Server Tests

```bash
python mcp-server/test_mcp_server.py
```

---

## MCP Tools (exposed by mcp-server)

For the complete tool list used in testing, including newer dataset-specific tools and example prompts, see `docs/TOOLS.md`.

| Tool | Purpose |
|------|---------|
| `fetch_us_shootings` | Fetch us_shootings rows with optional filters (state, limit, order_by, desc). Use for list/show/get questions about shootings. Returns CSV. |
| `execute_sql` | Run read-only SQL (SELECT, SHOW, DESCRIBE, EXPLAIN). Use for aggregations, counts, other tables, JOINs. Returns CSV. |
| `get_state_unemployment_summary` | Fetch unemployment data for one state or the United States aggregate row. |
| `compare_unemployment_states` | Compare unemployment data for two states, or a state versus the United States. |
| `list_unemployment_rankings` | List unemployment rows ranked by a selected metric such as `Rate_2023` or `State_Rank`. |
| `get_ngo_by_ein` | Fetch full NGO details for a single EIN. |
| `search_ngos` | Search NGO records with optional filters such as state, category, city, county, or partial name. |
| `summarize_ngos` | Summarize NGO counts by category, state, county, city, or NTEE code, with optional filters. |
| `fetch_faa_aircraft_data` | Fetch FAA releasable aircraft data from a selected FAA dataset, with optional exact lookup and state filter. |

---

## Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/query` | POST | Send a question, get SQL + results. Body: `{"question": "...", "session_id": 123, "message_type": "human"}` |

---

## Configuration Reference

| File | Purpose |
|------|---------|
| `config.json` (root) | `db_url`, `db_username`, `db_password`, `redis_host_url`, `redis_port`, `redis_password` |
| `llm-engine/app/llm_config.json` | `provider`, `model`, `api_key_path` |
| `llm-engine/app/sensitive/*.txt` | API keys (one per provider) |

---

## Coding Conventions (from AGENTS.md)

- 4-space indentation; standard Python import ordering
- Manager classes: `CamelCase.py` (e.g., `LLMManager.py`)
- Utilities: `snake_case.py` (e.g., `test_responses.py`)
- Tests: `unittest`, `Test*` classes, `test_*` methods in `test_*.py`
- Commit messages: short, sentence-case, no prefixes

---

## Common Tasks for an LLM

1. **Add a new API endpoint:** Edit `llm-engine/app/app.py`.
2. **Change LLM provider:** Update `llm_config.json` and add `sensitive/{provider}.txt`.
3. **Adjust summarization threshold:** Set `HISTORY_THRESHOLD` in `llm-engine/app/app.py`.
4. **Add database tables:** Use or extend `create_NORP_tables.py` and update schema docs.
5. **Add MCP tools:** Edit `mcp-server/server.py` (e.g., `execute_sql`, `fetch_us_shootings`). Use `@mcp.tool()` decorator.

---

## Troubleshooting

- **403 / Permission denied on push:** Update Git credentials (see README or credential manager).
- **Redis connection refused:** Ensure Redis is running; check `config.json` host/port.
- **Database connection failed:** Verify `db_url`, credentials, and that MariaDB/MySQL is up.
- **LLM errors:** Confirm `api_key_path` exists and key is valid; check `llm_config.json` provider/model.
