#!/usr/bin/env python3
"""
Read-only helpers for FAA Releasable Aircraft tables loaded from FAA_Releasable_Aircraft_*.csv.
Uses config.json at repo root via the MCP server helpers.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mysql.connector import Error, connect

DATASET_TO_TABLE = {
    "master": "faa_master",
    "acftref": "faa_acftref",
    "engine": "faa_engine",
    "dealer": "faa_dealer",
    "docindex": "faa_docindex",
    "dereg": "faa_dereg",
    "reserved": "faa_reserved",
}

ORDER_BY_COLUMN = {
    "master": "n_number",
    "acftref": "code",
    "engine": "code",
    "dealer": "certificate_number",
    "docindex": "id",
    "dereg": "id",
    "reserved": "n_number",
}

MAX_LIMIT = 500


def _validate_dataset(dataset: str) -> str:
    normalized = dataset.strip().lower()
    if normalized not in DATASET_TO_TABLE:
        allowed = ", ".join(sorted(DATASET_TO_TABLE))
        raise ValueError(f"Validation error: dataset must be one of: {allowed}.")
    return normalized


def _validate_limit(limit: int) -> int:
    if limit < 1:
        raise ValueError("Validation error: limit must be greater than 0.")
    if limit > MAX_LIMIT:
        raise ValueError(f"Validation error: limit must be at most {MAX_LIMIT}.")
    return limit


def fetch_faa_aircraft_data(
    config: dict,
    dataset: str,
    limit: int = 10,
    search_value: str | None = None,
    state: str | None = None,
):
    """
    Return up to `limit` rows from the selected FAA table.

    search_value (optional):
      - master, reserved, dereg: match n_number (e.g. N100)
      - acftref, engine: match code
      - dealer: match certificate_number
      - docindex: match doc_id OR collateral_aircraft OR serial_id

    state (optional): filter by state column for master, reserved, dealer; for dereg uses
    state_abbrev_mail.
    """
    ds = _validate_dataset(dataset)
    lim = _validate_limit(limit)
    table = DATASET_TO_TABLE[ds]
    order_col = ORDER_BY_COLUMN[ds]

    conditions: list[str] = []
    params: list = []

    if search_value is not None and search_value.strip() != "":
        sv = search_value.strip()
        if ds in ("master", "reserved", "dereg"):
            conditions.append("n_number = %s")
            params.append(sv)
        elif ds in ("acftref", "engine"):
            conditions.append("code = %s")
            params.append(sv)
        elif ds == "dealer":
            conditions.append("certificate_number = %s")
            params.append(sv)
        elif ds == "docindex":
            conditions.append("(doc_id = %s OR collateral_aircraft = %s OR serial_id = %s)")
            params.extend([sv, sv, sv])

    if state is not None and state.strip() != "":
        st = state.strip()
        if ds in ("master", "reserved", "dealer"):
            conditions.append("state = %s")
            params.append(st)
        elif ds == "dereg":
            conditions.append("state_abbrev_mail = %s")
            params.append(st)

    where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"SELECT * FROM {table}{where_clause} ORDER BY {order_col} ASC LIMIT %s"
    params.append(lim)

    with connect(**config) as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchall()


def main():
    parser = argparse.ArgumentParser(description="Fetch FAA releasable aircraft tables from MySQL")
    parser.add_argument(
        "dataset",
        choices=sorted(DATASET_TO_TABLE.keys()),
        help="Which FAA dataset / table to query",
    )
    parser.add_argument("--limit", "-n", type=int, default=10)
    parser.add_argument("--search-value", "-q", default=None)
    parser.add_argument("--state", default=None)
    args = parser.parse_args()

    try:
        from server import get_mysql_connection_config

        config = get_mysql_connection_config()
        rows = fetch_faa_aircraft_data(
            config=config,
            dataset=args.dataset,
            limit=args.limit,
            search_value=args.search_value,
            state=args.state,
        )
    except (Error, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    if not rows:
        print("No rows found.")
        return

    cols = list(rows[0].keys())
    header = " | ".join(f"{c:24}" for c in cols)
    print(header)
    print("-" * len(header))
    for row in rows:
        line = " | ".join(str(row.get(c, ""))[:24].ljust(24) for c in cols)
        print(line)


if __name__ == "__main__":
    main()
