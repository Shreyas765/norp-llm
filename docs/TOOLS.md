# MCP Tools

| Tool | Table / dataset | Description | Example LLM query |
| --- | --- | --- | --- |
| `execute_sql` | Configured MySQL database, read-only queries only | Runs a read-only SQL query (`SELECT`, `SHOW`, `DESCRIBE`, `EXPLAIN`) against the configured MySQL database and returns CSV text. | N/A |
| `fetch_us_shootings` | `us_shootings` | Fetches US shooting incident rows with optional state filter, limit, and sort order. | `Give me US shootings in Louisiana from the year 2014.` |
| `get_state_unemployment_summary` | `unemployment_rates_by_state` | Fetches unemployment data for one state or the United States aggregate row. | `Give me the unemployment rate for Georgia in 2023.` |
| `compare_unemployment_states` | `unemployment_rates_by_state` | Compares unemployment data for two states, or a state versus the United States.` | `How does the unemployment rate in Hawaii compare to Indiana in 2023?` |
| `list_unemployment_rankings` | `unemployment_rates_by_state` | Lists unemployment rows ranked by a selected metric such as `Rate_2023` or `State_Rank`. | `What were the five states with the lowest unemployment rates in 2022?` |
| `get_ngo_by_ein` | `ngos_with_categorization` | Fetches full NGO details for a single EIN. | `Give me the full name and full address of the NGO with EIN 100006500.` |
| `search_ngos` | `ngos_with_categorization` | Searches NGO records with optional filters such as state, category, city, county, or partial name. | `Give me NGOs in Albany County.` |
| `summarize_ngos` | `ngos_with_categorization` | Summarizes NGO counts by category, state, county, city, or NTEE code, with optional filters. | `Which states have the most religion-related NGOs?` |
| `fetch_faa_aircraft_data` | `faa_master`, `faa_acftref`, `faa_engine`, `faa_dealer`, `faa_docindex`, `faa_dereg`, `faa_reserved` | Fetches FAA releasable aircraft data from one selected FAA dataset, with optional exact lookup and state filter. | `Look up FAA registration N100 in the master registry.` |
