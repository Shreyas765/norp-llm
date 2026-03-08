# INSTRUCTIONS.md — AI Workflow Guide

This document provides everything an LLM (Claude, GPT, Gemini, etc.) needs to build, run, and test the **norp-llm** project. Ingest this file to enable a seamless AI-assisted development workflow.

---

## Project Overview

**norp-llm** is a SQL chatbot application that:
- Accepts natural language questions from users
- Generates SQL queries via an LLM (LangChain)
- Executes queries against a MySQL/MariaDB database
- Returns formatted results and maintains conversational context via Redis

**Tech stack:** Python 3.9+, FastAPI, LangChain, Redis, MySQL/MariaDB, MCP (Model Context Protocol).

---

## Project Structure

```
norp-llm/
├── config.json                 # DB + Redis connection (repo root)
├── requirements.txt            # Python dependencies
├── INSTRUCTIONS.md             # This file
├── README.md                   # User-facing docs
├── AGENTS.md                   # Repo guidelines for contributors
├── .devcontainer/              # Dev container + Docker Compose
│   ├── devcontainer.json
│   └── docker-compose.yml      # MariaDB, Redis, phpMyAdmin
├── llm-engine/app/             # Main FastAPI service
│   ├── app.py                  # FastAPI app entry
│   ├── config.json             # (optional override; repo root used)
│   ├── llm_config.json         # LLM provider + model + API key path
│   ├── sensitive/              # API keys (gitignored): openai.txt, etc.
│   ├── test_responses.py       # Manual API test script
│   ├── local_database_setup/   # create_NORP_tables.py, sample data
│   └── test/                   # Unit tests (unittest)
├── mcp-server/                 # MCP server (execute_sql, fetch_us_shootings)
│   ├── server.py               # Run before main app
│   └── tools/                  # Tool implementations
│       └── fetch_us_shootings.py
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

## Testing

### 1. Manual API Test

With the app running:

```bash
cd llm-engine/app
python test_responses.py --question "Show me 5 shootings in Texas" --session_id 585
```

Or from repo root:

```bash
python llm-engine/app/test_responses.py --question "Show me 5 shootings in Texas" --session_id 999
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

| Tool | Purpose |
|------|---------|
| `fetch_us_shootings` | Fetch us_shootings rows with optional filters (state, limit, order_by, desc). Use for list/show/get questions about shootings. Returns CSV. |
| `execute_sql` | Run read-only SQL (SELECT, SHOW, DESCRIBE, EXPLAIN). Use for aggregations, counts, other tables, JOINs. Returns CSV. |
| `divide` | Integer division (utility). |

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
