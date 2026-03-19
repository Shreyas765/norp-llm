# `/query` API — `curl` examples and sample outputs

These examples call `POST http://127.0.0.1:8000/query` with JSON: `question`, `session_id`, and `message_type` (`human` for user turns).

**Prerequisites:** Redis, MySQL (with NORP/FAA tables as loaded by your setup), MCP server (`python mcp-server/server.py`), and the app (`uvicorn app:app --host 127.0.0.1 --port 8000` from `llm-engine/app`).

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
