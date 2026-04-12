# `/query` API — `curl` examples and sample outputs

These examples call `POST http://127.0.0.1:8000/query` with JSON: `question`, `session_id`, and `message_type` (`human` for user turns).

**Prerequisites:** Redis, MySQL (with NORP/FAA tables as loaded by your setup), optional Georgia crime tables if you use those prompts (`python llm-engine/app/local_database_setup/load_georgia_crime_incidents.py`), MCP server (`python mcp-server/server.py`), and the app (`uvicorn app:app --host 127.0.0.1 --port 8000` from `llm-engine/app`). For MCP-only mode, start the app with `--mcp-only` or set `MCP_ONLY=1`.

**Note:** Wording in `response` can differ per LLM run. The samples below were captured in one environment (MCP-only mode, local sample data). `sql_query` and `query_results` are usually `null` in MCP-only mode.

---

## Generic request shape

```bash
curl -sS --max-time 180 "http://127.0.0.1:8000/query" \
  --request POST \
  --header "Content-Type: application/json" \
  --data '{"question": "YOUR QUESTION HERE", "session_id": 1, "message_type": "human"}'
```

Pretty-print the JSON body of the response:

```bash
curl -sS --max-time 180 "http://127.0.0.1:8000/query" \
  --request POST \
  --header "Content-Type: application/json" \
  --data '{"question": "YOUR QUESTION HERE", "session_id": 1, "message_type": "human"}' \
  | python3 -m json.tool
```

---

## 1. Unemployment (MCP: `get_state_unemployment_summary`)

**Command:**

```bash
curl -sS --max-time 180 "http://127.0.0.1:8000/query" \
  --request POST \
  --header "Content-Type: application/json" \
  --data '{"question": "Give me the unemployment rate for Georgia in 2023.", "session_id": 301, "message_type": "human"}' \
  | python3 -m json.tool
```

**Sample output:**

```json
{
    "response": "Georgia — Unemployment rate in 2023: 3.3% (2022: 3.2%, change +0.1)",
    "sql_query": null,
    "query_results": null
}
```

---

## 2. FAA — N-number lookup (MCP: `fetch_faa_aircraft_data`, `dataset=master`)

**Command:**

```bash
curl -sS --max-time 180 "http://127.0.0.1:8000/query" \
  --request POST \
  --header "Content-Type: application/json" \
  --data '{"question": "Look up FAA registration N100 in the master registry.", "session_id": 302, "message_type": "human"}' \
  | python3 -m json.tool
```

**Sample output** (`response` is CSV text from the tool):

```json
{
    "response": "n_number,serial_number,mfr_mdl_code,eng_mfr_mdl,year_mfr,owner_type,registrant_name,street,street2,city,state,zip_code,region,county,country,last_action_date,cert_issue_date,certification,airworthiness_classification,approved_operations,type_aircraft,type_engine,status_code,mode_s_code,fract_owner,air_worth_date,other_names1,other_names2,other_names3,other_names4,other_names5,expiration_date,unique_id,kit_mfr,kit_model,mode_s_code_hex\nN100,5334,7100510,17003,1940,Individual,BENE MARY D,PO BOX 329,None,KETCHUM,OK,743490329,Southwestern,97,US,2023-01-22,2005-05-06,1,Standard,None,Fixed wing single engine,Reciprocating,Valid Registration,50002263,None,1954-04-30,None,None,None,None,None,2027-04-30,600060,None,None,A004B3",
    "sql_query": null,
    "query_results": null
}
```

---

## 3. FAA — filter by state (master, multiple rows)

**Command:**

```bash
curl -sS --max-time 180 "http://127.0.0.1:8000/query" \
  --request POST \
  --header "Content-Type: application/json" \
  --data '{"question": "Show 3 aircraft registered in Oklahoma from the FAA master registry.", "session_id": 303, "message_type": "human"}' \
  | python3 -m json.tool
```

**Sample output:**

```json
{
    "response": "n_number,serial_number,mfr_mdl_code,eng_mfr_mdl,year_mfr,owner_type,registrant_name,street,street2,city,state,zip_code,region,county,country,last_action_date,cert_issue_date,certification,airworthiness_classification,approved_operations,type_aircraft,type_engine,status_code,mode_s_code,fract_owner,air_worth_date,other_names1,other_names2,other_names3,other_names4,other_names5,expiration_date,unique_id,kit_mfr,kit_model,mode_s_code_hex\nN100,5334,7100510,17003,1940,Individual,BENE MARY D,PO BOX 329,None,KETCHUM,OK,743490329,Southwestern,97,US,2023-01-22,2005-05-06,1,Standard,None,Fixed wing single engine,Reciprocating,Valid Registration,50002263,None,1954-04-30,None,None,None,None,None,2027-04-30,600060,None,None,A004B3\nN1000E,550-1011,2076604,52065,2002,Corporation,WR HESS CO,3636 S MERIDIAN AVE,None,OKLAHOMA CITY,OK,731192420,Southwestern,109,US,2023-07-18,2016-02-16,1T,Standard,Transport,Fixed wing multi engine,Turbo-fan,Valid Registration,50003421,None,2016-02-19,None,None,None,None,None,2029-02-28,1207444,None,None,A00711\nN1000J,M-1000,1151208,17033,1966,Corporation,EAGLE MOUNTAIN AVIATION INC,16653 E 78TH ST N,None,OWASSO,OK,740555726,Southwestern,143,US,2024-05-14,2024-05-14,1N,Standard,Normal,Fixed wing single engine,Reciprocating,Valid Registration,50003425,None,1966-10-28,None,None,None,None,None,2031-05-31,340110,None,None,A00715",
    "sql_query": null,
    "query_results": null
}
```

---

## 4. FAA — manufacturer / model reference code (acftref)

**Command:**

```bash
curl -sS --max-time 180 "http://127.0.0.1:8000/query" \
  --request POST \
  --header "Content-Type: application/json" \
  --data '{"question": "What is FAA aircraft reference acftref code 7100510?", "session_id": 304, "message_type": "human"}' \
  | python3 -m json.tool
```

**Sample output** (model may summarize tool CSV into prose):

```json
{
    "response": "Here’s the acftref record for code 7100510 (exact fields from the FAA reference):\n\n- code: 7100510\n- mfr_code: 710\n- model_code: 5\n- series_code: 10\n- mfr: PIPER\n- model: J3C-65\n- type_acft: Fixed wing single engine\n- type_eng: Reciprocating\n- ac_cat: Land\n- build_cert_ind: Type Certificated\n- no_eng: 1\n- no_seats: 2\n- ac_weight: Up to 12,499\n- speed: 67\n- tc_data_sheet: None\n- tc_data_holder: None",
    "sql_query": null,
    "query_results": null
}
```

---

## 5. NGOs — search by county (MCP: `search_ngos`)

**Command:**

```bash
curl -sS --max-time 180 "http://127.0.0.1:8000/query" \
  --request POST \
  --header "Content-Type: application/json" \
  --data '{"question": "Give me NGOs in Albany County.", "session_id": 305, "message_type": "human"}' \
  | python3 -m json.tool
```

**Sample output:**

```json
{
    "response": "Here are 5 NGOs in Albany County (from the database):\n\n- EIN: 222719837 - 100 South Swan Street Realty Corp - Albany, NY - NTEE: S47 - Category: Community Improvement, Capacity Building\n- EIN: 352433476 - 105Th Military Police Company Alumni Association Troy New York - Latham, NY - NTEE: W30 - Category: Public & Societal Benefit\n- EIN: 100004869 - 195 Fort Edward Inc - Albany, NY - NTEE: S47 - Category: Community Improvement, Capacity Building\n- EIN: 352381188 - 2-1-1 New York Inc - Latham, NY - NTEE: E70 - Category: Health Care\n- EIN: 141760872 - 222 Riverside Plaza Corp - Albany, NY - NTEE: C99 - Category: Environment\n\nWould you like more results, a different limit, or to filter by category (for example, Health Care, Education, Environment)?",
    "sql_query": null,
    "query_results": null
}
```

---

## 6. NGOs — summarize by state for a category (MCP: `summarize_ngos`)

**Command:**

```bash
curl -sS --max-time 180 "http://127.0.0.1:8000/query" \
  --request POST \
  --header "Content-Type: application/json" \
  --data '{"question": "Which states have the most religion-related NGOs?", "session_id": 306, "message_type": "human"}' \
  | python3 -m json.tool
```

**Sample output:**

```json
{
    "response": "Here are the states with the most religion-related NGOs (top 10):\n\n- NY: 17,655\n- CA: 12,977\n- OH: 11,201\n- PA: 11,124\n- TX: 7,153\n- IN: 7,148\n- NJ: 6,804\n- FL: 6,081\n- IL: 4,311\n- GA: 3,453\n\nIf you want this as a CSV, a chart, or filtered by per-capita counts (religion NGOs per 100k residents), I can provide that too.",
    "sql_query": null,
    "query_results": null
}
```

---

## 7. NGOs — fetch one NGO by EIN (MCP: `get_ngo_by_ein`)

**Command:**

```bash
curl -sS --max-time 180 "http://127.0.0.1:8000/query" \
  --request POST \
  --header "Content-Type: application/json" \
  --data '{"question": "Give me the full name and full address of the NGO with EIN 100006500.", "session_id": 307, "message_type": "human"}' \
  | python3 -m json.tool
```

**Sample output:**

```json
{
    "response": "Here's the NGO you requested:\n\nName: Lebanon Volunteer Fire Department\nFull address: PO BOX 51, LEBANON, CT, 06249-0051\n\nDo you need anything else about this NGO?",
    "sql_query": null,
    "query_results": null
}
```

---

## 8. Georgia crime incidents (MCP: `fetch_georgia_crime_incidents`)

Use after loading `georgia_crime_incidents_2022` / `_2023` / `_2024` (see `llm-engine/app/local_database_setup/load_georgia_crime_incidents.py`). Ask for a specific **year** so the model maps to the right table.

**Command:**

```bash
curl -sS --max-time 180 "http://127.0.0.1:8000/query" \
  --request POST \
  --header "Content-Type: application/json" \
  --data '{"question": "List 3 drug-related offenses in Georgia in 2023 with incident dates.", "session_id": 308, "message_type": "human"}' \
  | python3 -m json.tool
```

**Sample output** (`response` may be raw CSV from the tool or a short summary, depending on the model):

```json
{
    "response": "incident_id,submission_date,incident_date,incident_hour,incident_status,offense_incident_id,offense_code,offense_name,crime_against,is_counter_terrorism,is_hate_crime,offense_category_name,location_code,location_name,victim_id,ethnicity_name,offender_id,ethnicity_name_offender,victim_type_name\n166616620,2023-02-14,2023-01-03,10,ACCEPTED,198881307,35A,Drug/Narcotic Violations,Society,0,1,Drug/Narcotic Offenses,13,Highway/Road/Alley/Street/Sidewalk,184526430,Not Specified,189157289,Not Hispanic or Latino,Society/Public",
    "sql_query": null,
    "query_results": null
}
```

**Stricter tool routing** (explicit year and filters):

```bash
curl -sS --max-time 180 "http://127.0.0.1:8000/query" \
  --request POST \
  --header "Content-Type: application/json" \
  --data '{"question": "Using Georgia crime data for 2024 only, show 2 hate crime offenses and include offense name and incident date.", "session_id": 309, "message_type": "human"}' \
  | python3 -m json.tool
```

---

## PowerShell (Windows)

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/query" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"question": "Give me the unemployment rate for Georgia in 2023.", "session_id": 301, "message_type": "human"}'
```

---

## Script alternative

From `llm-engine/app`:

```bash
python test_responses.py --question "YOUR QUESTION" --session_id 585
```

---

## 9. SQL — direct `execute_sql` example

Use this when you want the app to run a read-only SQL query via the `execute_sql` tool. The `question` is written in natural language and the agent maps it to an appropriate `SELECT` statement.

**Command:**

```bash
curl -sS --max-time 180 "http://127.0.0.1:8000/query" \
  --request POST \
  --header "Content-Type: application/json" \
  --data '{"question": "How many victims were killed in California in 2023?", "session_id": 320, "message_type": "human"}' \
  | python3 -m json.tool
```

**Sample output (example):**

```json
{
    "response": "Killed victims in CA in 2023: 123",
    "sql_query": "SELECT COUNT(*) AS killed_count FROM us_shootings WHERE state = 'CA' AND YEAR(incident_date) = 2023 AND killed IS NOT NULL AND killed > 0;",
    "query_results": "killed_count\n123"
}
```

Note: actual `sql_query` and `query_results` fields depend on routing (MCP vs direct SQL tool) and the model's SQL translation; the agent will attempt only read-only SQL statements.
