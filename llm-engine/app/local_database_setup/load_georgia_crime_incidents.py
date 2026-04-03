#!/usr/bin/env python3
"""
Create georgia_crime_incidents_2022/2023/2024 tables and load rows from the three
query_result_*.csv exports (same schema; one file per calendar year).

Uses repo-root config.json (same as the MCP server). Run from any cwd:

    python llm-engine/app/local_database_setup/load_georgia_crime_incidents.py

Requires: mysql-connector-python, large CSVs present next to this script.
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path

import mysql.connector

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "mcp-server"))
from server import get_mysql_connection_config  # noqa: E402

from tools.georgia_crime_incidents import YEAR_TO_TABLE  # noqa: E402

SCRIPT_DIR = Path(__file__).resolve().parent

# CSV exports in this folder mapped to calendar year (verified from Incident Date samples).
YEAR_CSV_FILES = {
    2022: "query_result_2026-04-03T13_15_02.749469135-04_00.csv",
    2023: "query_result_2026-04-03T13_14_21.12783701-04_00.csv",
    2024: "query_result_2026-04-03T13_15_53.81246561-04_00.csv",
}

INSERT_SQL = """
INSERT INTO `{table}` (
  incident_id, submission_date, incident_date, incident_hour, incident_status,
  offense_incident_id, offense_code, offense_name, crime_against,
  is_counter_terrorism, is_hate_crime, offense_category_name,
  location_code, location_name, victim_id, ethnicity_name,
  offender_id, ethnicity_name_offender, victim_type_name
) VALUES (
  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
"""


def _parse_date(value: str):
    value = (value or "").strip()
    if not value:
        return None
    return datetime.strptime(value[:10], "%Y-%m-%d").date()


def _parse_int(value: str):
    value = (value or "").strip()
    if not value:
        return None
    return int(value)


def _parse_bool(value: str):
    value = (value or "").strip()
    if not value:
        return None
    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    return None


def _row_tuple(row: dict):
    return (
        _parse_int(row["Incident ID"]),
        _parse_date(row["Submission Date"]),
        _parse_date(row["Incident Date"]),
        _parse_int(row["Incident Hour"]),
        (row.get("Incident Status") or "").strip() or None,
        _parse_int(row["Offense Incident ID"]),
        (row.get("Offense Code") or "").strip() or None,
        (row.get("Offense Name") or "").strip() or None,
        (row.get("Crime Against") or "").strip() or None,
        _parse_bool(row["Is Counter Terrorism"]),
        _parse_bool(row["Is Hate Crime"]),
        (row.get("Offense Category Name") or "").strip() or None,
        _parse_int(row["Location Code"]),
        (row.get("Location Name") or "").strip() or None,
        _parse_int(row["Victim ID"]),
        (row.get("Ethnicity Name") or "").strip() or None,
        _parse_int(row["Offender ID"]),
        (row.get("Ethnicity Name Offender") or "").strip() or None,
        (row.get("Victim Type Name") or "").strip() or None,
    )


def _create_table(cursor, table: str) -> None:
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS `{table}` (
          incident_id BIGINT NOT NULL,
          submission_date DATE NULL,
          incident_date DATE NULL,
          incident_hour INT NULL,
          incident_status VARCHAR(32) NULL,
          offense_incident_id BIGINT NOT NULL PRIMARY KEY,
          offense_code VARCHAR(16) NULL,
          offense_name VARCHAR(512) NULL,
          crime_against VARCHAR(64) NULL,
          is_counter_terrorism BOOLEAN NULL,
          is_hate_crime BOOLEAN NULL,
          offense_category_name VARCHAR(128) NULL,
          location_code INT NULL,
          location_name VARCHAR(255) NULL,
          victim_id BIGINT NULL,
          ethnicity_name VARCHAR(64) NULL,
          offender_id BIGINT NULL,
          ethnicity_name_offender VARCHAR(64) NULL,
          victim_type_name VARCHAR(64) NULL,
          KEY idx_incident_date (incident_date),
          KEY idx_offense_category (offense_category_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )


def _load_csv(conn, table: str, csv_path: Path, batch_size: int = 2000) -> int:
    insert = INSERT_SQL.format(table=table)
    count = 0
    batch = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            batch.append(_row_tuple(row))
            if len(batch) >= batch_size:
                with conn.cursor() as cursor:
                    cursor.executemany(insert, batch)
                conn.commit()
                count += len(batch)
                batch = []
        if batch:
            with conn.cursor() as cursor:
                cursor.executemany(insert, batch)
            conn.commit()
            count += len(batch)
    return count


def main() -> None:
    config = get_mysql_connection_config()
    with mysql.connector.connect(**config) as conn:
        for year, filename in YEAR_CSV_FILES.items():
            table = YEAR_TO_TABLE[year]
            csv_path = SCRIPT_DIR / filename
            if not csv_path.is_file():
                print(f"Skip {year}: missing {csv_path}", file=sys.stderr)
                continue
            with conn.cursor() as cursor:
                _create_table(cursor, table)
                cursor.execute(f"TRUNCATE TABLE `{table}`")
            conn.commit()
            print(f"Loading {year} -> {table} from {filename} ...")
            n = _load_csv(conn, table, csv_path)
            print(f"  inserted {n} rows.")
    print("Done.")


if __name__ == "__main__":
    main()
