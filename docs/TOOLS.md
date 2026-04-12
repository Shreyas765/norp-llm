# MCP Tools

| Tool | Table / dataset | Description | Example LLM query |
| --- | --- | --- | --- |
| `execute_sql` | Configured MySQL database, read-only queries only | Runs a read-only SQL query (`SELECT`, `SHOW`, `DESCRIBE`, `EXPLAIN`) against the configured MySQL database and returns CSV text. | `How many victims were killed in California in 2023?` |
| `fetch_us_shootings` | `us_shootings` | Fetches US shooting incident rows with optional state filter, limit, and sort order. | `Give me US shootings in Louisiana from the year 2014.` |
| `get_state_unemployment_summary` | `unemployment_rates_by_state` | Fetches unemployment data for one state or the United States aggregate row. | `Give me the unemployment rate for Georgia in 2023.` |
| `compare_unemployment_states` | `unemployment_rates_by_state` | Compares unemployment data for two states, or a state versus the United States. | `How does the unemployment rate in Hawaii compare to Indiana in 2023?` |
| `list_unemployment_rankings` | `unemployment_rates_by_state` | Lists unemployment rows ranked by a selected metric such as `Rate_2023` or `State_Rank`. | `What were the five states with the lowest unemployment rates in 2022?` |
| `get_ngo_by_ein` | `ngos_with_categorization` | Fetches full NGO details for a single EIN. | `Give me the full name and full address of the NGO with EIN 100006500.` |
| `search_ngos` | `ngos_with_categorization` | Searches NGO records with optional filters such as state, category, city, county, or partial name. | `Give me NGOs in Albany County.` |
| `summarize_ngos` | `ngos_with_categorization` | Summarizes NGO counts by category, state, county, city, or NTEE code, with optional filters. | `Which states have the most religion-related NGOs?` |
| `fetch_faa_aircraft_data` | `faa_master`, `faa_acftref`, `faa_engine`, `faa_dealer`, `faa_docindex`, `faa_dereg`, `faa_reserved` | Fetches FAA releasable aircraft data from one selected FAA dataset, with optional exact lookup and state filter. | `Look up FAA registration N100 in the master registry.` |
| `fetch_georgia_crime_incidents` | `georgia_crime_incidents_2022`, `georgia_crime_incidents_2023`, `georgia_crime_incidents_2024` | Fetches Georgia crime incident/offense rows for one calendar year; optional offense category, offense name substring, and hate-crime filter. | `Show 5 larceny offenses in Georgia in 2023.` |

## `fetch_georgia_crime_incidents` parameters

| Argument | Description |
| --- | --- |
| `year` | **Required.** `2022`, `2023`, or `2024` — selects the matching `georgia_crime_incidents_<year>` table. |
| `limit` | Max rows (default 10, max 500). |
| `order_by` | One of: `incident_date`, `submission_date`, `incident_hour`, `offense_code`, `incident_id`, `offense_incident_id`. |
| `desc` | Sort descending if `true` (default), ascending if `false`. |
| `offense_category` | Optional exact match on `offense_category_name` (e.g. `Larceny/Theft Offenses`, `Sex Offenses`). |
| `offense_name_contains` | Optional substring match on `offense_name`. |
| `is_hate_crime` | Optional boolean filter when set. |

**Loading data:** create and populate the three tables from the CSV exports using [`llm-engine/app/local_database_setup/load_georgia_crime_incidents.py`](../llm-engine/app/local_database_setup/load_georgia_crime_incidents.py) (expects the `query_result_*.csv` files in the same directory). The MCP tool returns CSV text (same pattern as other fetch tools).
