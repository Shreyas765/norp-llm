#!/usr/bin/env python3
"""
Simple tools to fetch unemployment_rates_by_state data from the database.
Uses config.json at repo root via the MCP server helpers.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mysql.connector import Error, connect


ALLOWED_METRICS = ("Rate_2022", "Rate_2023", "Rate_Change", "State_Rank")
ALLOWED_ORDER = ("asc", "desc")
UNEMPLOYMENT_COLUMNS = (
    "State",
    "Rate_2022",
    "Rate_2023",
    "Rate_Change",
    "State_Rank",
)


def _validate_metric(metric: str) -> str:
    if metric not in ALLOWED_METRICS:
        allowed = ", ".join(ALLOWED_METRICS)
        raise ValueError(f"Validation error: metric must be one of {allowed}.")
    return metric


def _validate_order(order: str) -> str:
    normalized_order = order.lower()
    if normalized_order not in ALLOWED_ORDER:
        allowed = ", ".join(ALLOWED_ORDER)
        raise ValueError(f"Validation error: order must be one of {allowed}.")
    return normalized_order


def _validate_limit(limit: int) -> int:
    if limit < 1:
        raise ValueError("Validation error: limit must be greater than 0.")
    return limit


def get_state_unemployment_summary(config: dict, state: str):
    """Fetch a single unemployment_rates_by_state row by exact state name."""
    query = """
        SELECT State, Rate_2022, Rate_2023, Rate_Change, State_Rank
        FROM unemployment_rates_by_state
        WHERE State = %s
    """

    with connect(**config) as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, (state,))
            return cursor.fetchall()


def compare_unemployment_states(config: dict, state_a: str, state_b: str = "United States"):
    """Fetch up to two unemployment rows in the same order as the requested states."""
    query = """
        SELECT State, Rate_2022, Rate_2023, Rate_Change, State_Rank
        FROM unemployment_rates_by_state
        WHERE State IN (%s, %s)
    """

    with connect(**config) as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, (state_a, state_b))
            rows = cursor.fetchall()

    row_by_state = {row["State"]: row for row in rows}
    ordered_rows = []
    for state in (state_a, state_b):
        row = row_by_state.get(state)
        if row:
            ordered_rows.append(row)
    return ordered_rows


def list_unemployment_rankings(
    config: dict,
    metric: str = "Rate_2023",
    order: str = "desc",
    limit: int = 10,
    include_united_states: bool = False,
):
    """Fetch ranked unemployment rows by a validated metric and sort order."""
    validated_metric = _validate_metric(metric)
    validated_order = _validate_order(order)
    validated_limit = _validate_limit(limit)

    select_columns = ", ".join(UNEMPLOYMENT_COLUMNS)
    query = f"SELECT {select_columns} FROM unemployment_rates_by_state"
    params = []

    if not include_united_states:
        query += " WHERE State <> %s"
        params.append("United States")

    query += f" ORDER BY {validated_metric} {validated_order.upper()}, State ASC"
    query += " LIMIT %s"
    params.append(validated_limit)

    with connect(**config) as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def main():
    parser = argparse.ArgumentParser(description="Fetch unemployment_rates_by_state data from the database")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="Fetch a single state row")
    summary_parser.add_argument("state", help="Exact state name, e.g. California or United States")

    compare_parser = subparsers.add_parser("compare", help="Compare two states")
    compare_parser.add_argument("state_a", help="First state")
    compare_parser.add_argument("state_b", nargs="?", default="United States", help="Second state")

    rankings_parser = subparsers.add_parser("rankings", help="List ranked state rows")
    rankings_parser.add_argument("--metric", default="Rate_2023", choices=ALLOWED_METRICS)
    rankings_parser.add_argument("--order", default="desc", choices=ALLOWED_ORDER)
    rankings_parser.add_argument("--limit", "-n", type=int, default=10)
    rankings_parser.add_argument("--include-united-states", action="store_true")

    args = parser.parse_args()

    try:
        from server import get_mysql_connection_config

        config = get_mysql_connection_config()
        if args.command == "summary":
            rows = get_state_unemployment_summary(config=config, state=args.state)
        elif args.command == "compare":
            rows = compare_unemployment_states(
                config=config,
                state_a=args.state_a,
                state_b=args.state_b,
            )
        else:
            rows = list_unemployment_rankings(
                config=config,
                metric=args.metric,
                order=args.order,
                limit=args.limit,
                include_united_states=args.include_united_states,
            )
    except (Error, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    if not rows:
        print("No rows found.")
        return

    cols = list(rows[0].keys())
    header = " | ".join(f"{c:20}" for c in cols)
    print(header)
    print("-" * len(header))

    for row in rows:
        line = " | ".join(str(row.get(c, ""))[:20].ljust(20) for c in cols)
        print(line)


if __name__ == "__main__":
    main()
