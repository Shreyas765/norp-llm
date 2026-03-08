#!/usr/bin/env python3
"""
Simple tool to fetch us_shootings data from the MySQL database.
Uses config.json at repo root (same as MCP server).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mysql.connector import connect, Error


def fetch_shootings(config: dict, state=None, limit=10, order_by="IncidentDate", desc=True):
    """Fetch rows from us_shootings with optional filters."""
    query = "SELECT IncidentID, Address, IncidentDate, State, CityOrCountry, VictimsKilled, VictimsInjured FROM us_shootings"
    params = []

    if state:
        query += " WHERE State = %s"
        params.append(state)

    query += f" ORDER BY {order_by} {'DESC' if desc else 'ASC'}"
    query += " LIMIT %s"
    params.append(limit)

    with connect(**config) as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def main():
    parser = argparse.ArgumentParser(description="Fetch us_shootings data from the database")
    parser.add_argument("--state", "-s", help="Filter by state (e.g. California, Texas)")
    parser.add_argument("--limit", "-n", type=int, default=10, help="Max rows to return (default: 10)")
    parser.add_argument("--order", "-o", default="IncidentDate",
                        choices=["IncidentDate", "VictimsKilled", "State", "IncidentID"],
                        help="Column to order by (default: IncidentDate)")
    parser.add_argument("--asc", action="store_true", help="Sort ascending (default: descending)")
    args = parser.parse_args()

    try:
        rows = fetch_shootings(state=args.state, limit=args.limit, order_by=args.order, desc=not args.asc)
    except Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Config error: {e}", file=sys.stderr)
        sys.exit(1)

    if not rows:
        print("No rows found.")
        return

    # Print header
    cols = list(rows[0].keys())
    header = " | ".join(f"{c:20}" for c in cols)
    print(header)
    print("-" * len(header))

    for row in rows:
        line = " | ".join(str(row.get(c, ""))[:20].ljust(20) for c in cols)
        print(line)


if __name__ == "__main__":
    main()
