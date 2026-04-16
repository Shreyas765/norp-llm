---
name: add-dataset
description: |
  Skill to add a CSV dataset to `llm-engine` and create matching MCP tools in `mcp-server`.
  The skill guides a user from a single CSV to: schema decisions, MySQL table creation (via
  updating and running `create_NORP_tables.py`), data ingestion, and adding a small MCP tool
  in `mcp-server/tools/` that exposes basic queries over the dataset.
---

# Add Dataset Skill

**Purpose**: Make it easy for a developer to add a new CSV-backed dataset into the
`llm-engine` local MySQL database and register simple tools in `mcp-server` so
that the MCP server can access and query the dataset.

**When to use**: You have a CSV file and you want it available to the project as a
database table and as a callable tool for the MCP server. The user provides only the CSV
and optional tool ideas (query names, example inputs, desired outputs).

**Scope**: Workspace-scoped. The skill edits `llm-engine/app/local_database_setup/create_NORP_tables.py`,
adds ingestion guidance, and scaffolds a new tool file in `mcp-server/tools/`.

## Workflow (Step-by-step)

1. Receive the CSV file (or a path). Ask the user for any existing tool ideas.
2. Inspect CSV header and sample rows to propose a schema (column names, candidate types,
   primary key, nullable). Present schema for confirmation.
3. Update `create_NORP_tables.py` to add a CREATE TABLE block for the new dataset,
  and add a mapping entry in the `table_data` dict that points to the CSV file.
  Use the project's `upload_data_from_csv` helper for CSV ingestion (it skips the
  header and normalizes empty/boolean values). Follow the repository convention of
  routing all ingestion through `create_NORP_tables.py` — do not add a separate
  one-off ingestion script.
5. Scaffold a new MCP tool in `mcp-server/tools/` with a clear name and one or two
   simple query functions (examples: `get_<table>_by_id`, `search_<table>_by_column`).
6. Add a short test or example usage for the new tool and register any necessary imports
   in `mcp-server/server.py` if your project's MCP server requires explicit registration.
7. Run a quick verification: connect to MySQL and run a sample query, then call the
   MCP tool locally and confirm expected output.

## Required Execution Stages (Do not skip)

After implementing dataset/table/tool changes, the agent must complete all stages below
in the same run and must not ask the human to run these steps manually.

1. Run local table creation and ingestion immediately (via `create_NORP_tables.py`):
  - `cd /workspace/llm-engine/app/local_database_setup && python create_NORP_tables.py`
  - Verify the command exits successfully and that new table creation/loading messages appear.
2. Run MCP server tests using a command that works with the hyphenated folder name:
  - Use: `python /workspace/mcp-server/test_mcp_server.py`
  - Do not use: `python -m unittest mcp-server/test_mcp_server.py` (module import fails because of `-`).
3. Update docs for newly added tools:
  - Update `/workspace/docs/TOOLS.md` with each new tool and its purpose/arguments.
  - Update `/workspace/docs/CURL_EXAMPLES.md` with example `/query` prompts that route to each new tool.
4. Update benchmark prompts and run them:
  - Add the same new example questions to `/workspace/llm-engine/app/benchmark_questions.csv`.
  - Execute each new benchmark question and confirm a non-empty response is produced.
  - Preferred command pattern: `python /workspace/llm-engine/app/test_responses.py --question "..." --session_id <id>`.
5. Report outcomes for all stages:
  - Include migration result, test result summary, and query execution summary.
  - If a stage is blocked by environment/service availability, capture the exact failure and attempt
    an equivalent local validation path before returning.

## Decision Points & Branching

- Column typing: prefer VARCHAR/TEXT for unknown mixed types; suggest INT/FLOAT/DATE
  when values parse consistently. Ask user if strict typing is required.
- Primary key: if CSV contains a stable unique id column, use it; otherwise create an
  auto-increment integer id and document it in the tool interface.
- Size/scale: for very large CSVs (>>100k rows), recommend bulk-load strategies (LOAD DATA
  INFILE) and adding indexes; for small datasets, row-by-row insertion is acceptable.
- Tool complexity: keep initial MCP tool minimal (one-row lookup + simple filter)
  — iterate later for complex analytics.

## Quality Criteria / Completion Checks

- Table created successfully in MySQL `local_norp`.
- CSV rows ingested without errors (or with documented skipped rows).
- MCP tool file present in `mcp-server/tools/` and importable by the MCP server.
- One or more example queries run and return expected sample results.
- `create_NORP_tables.py` executed by the agent in the current run (not deferred to human).
- `test_mcp_server.py` executed by the agent using the correct command path.
- `TOOLS.md`, `CURL_EXAMPLES.md`, and `benchmark_questions.csv` updated for new tools.

## Files Touched

- `llm-engine/app/local_database_setup/create_NORP_tables.py`
- `mcp-server/tools/<dataset>_tool.py` (scaffolded)
- Optionally: `mcp-server/server.py` (if manual registration is required)

## Example Prompts (use these to invoke the skill)

- "Add dataset: path/to/my_data.csv — tool ideas: ['find_by_zip', 'count_by_state']"
- "Import CSV users.csv, make `user_id` the PK, provide a MCP tool `users_tool`"

## Clarifying Questions (ask the user)

1. Please upload or provide the CSV path. Is there a header row? If not, describe columns.
2. Any preferred primary key column? If none, create `id` INT AUTO_INCREMENT.
3. Tool ideas: list function names and the expected inputs/outputs (one-line each).
4. Are there performance concerns (rows count, expected query patterns, indexes)?

## Implementation Notes / Suggested Templates

- To add the table, append a CREATE TABLE SQL block to `create_NORP_tables.py` following
  existing patterns (see other table definitions in that file).
- To ingest, add an entry to the `table_data` dict similar to existing entries and
  reuse `upload_data_from_csv` (it skips header and cleans boolean/empty values).
  Do not create a separate ingestion script; the canonical flow is to have
  `create_NORP_tables.py` both create tables and ingest CSV files so a single
  top-level command seeds the local database.
- To scaffold a tool, add `mcp-server/tools/<dataset>_tool.py` with functions:

  - `def get_<table>_by_pk(pk):` — returns single row dict
  - `def search_<table>_by_column(col, value, limit=50):` — returns list of rows

- Keep the tool surface minimal; the MCP server can be extended later to add auth,
  pagination, and parameter validation.

## Running the table creation step automatically

The skill will update `create_NORP_tables.py` and then run it to create tables and
ingest the CSV. This follows the project's existing approach (see `create_NORP_tables.py`).
If your environment requires different MySQL credentials or hostnames, update the
constants at the top of that file before running.

## References & History

- This skill follows the project's existing pattern for table creation and ingestion in
  `llm-engine/app/local_database_setup/create_NORP_tables.py`.
- Guidance was reviewed against prior repository work (commit hashes: 2e4de9, 41a942c)
  to remain compatible with past implementations and naming conventions.

## Next Steps / Iteration

1. I will propose a concrete schema after I inspect your CSV. Confirm or edit it.
2. I will patch `create_NORP_tables.py` and scaffold the `mcp-server/tools` file.
3. I will run table creation and ingestion, then run a verification query and return results.
4. When patching `create_NORP_tables.py` apply the following fixes (implemented as discrete, reviewable steps):

- Add a `CREATE TABLE` block for the new dataset (example name: `socioeconomic_data_2024`) with an auto-increment `id` primary key and a `UNIQUE KEY` on `(state_code, county_code)` if you want to prevent duplicate state/county rows. Keep types permissive (BIGINT/INT/VARCHAR) unless strict typing is required.

- Use the existing helper `upload_data_from_csv_fixed(file_path, insert_query, expected_len)` when CSV rows may have inconsistent column counts or stray separators; it pads or truncates rows to match the number of `%s` placeholders. For well-formed CSVs with consistent column counts, continue using `upload_data_from_csv` which assumes uniform rows and slightly simpler behavior.

- Update `table_data` to include the new dataset with a matching `insert_query` that uses exactly `expected_len` `%s` placeholders.

- Verification tip: if you encounter duplicate-key integrity errors while exploring ingestion results, you may run a temporary `INSERT IGNORE` during local testing to observe inserted rows without changing the committed ingestion semantics. Do not commit `INSERT IGNORE` into the canonical script unless you intentionally change uniqueness semantics.

These steps reduce "Not enough parameters for the SQL statement" failures and make seeding tolerant to occasional malformed rows while preserving data for later inspection.

Would you like me to proceed? If yes, please provide the CSV file (or path) and any
tool idea list you already have.
