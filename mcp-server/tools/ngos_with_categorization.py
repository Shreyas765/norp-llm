#!/usr/bin/env python3
"""
Simple tools to fetch ngos_with_categorization data from the database.
Uses config.json at repo root via the MCP server helpers.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mysql.connector import Error, connect


ALLOWED_GROUP_BY = ("Category", "State", "County", "City", "Ntee_Code")
ALLOWED_ORDER = ("asc", "desc")
SEARCH_COLUMNS = (
    "Ein",
    "Name",
    "City",
    "State",
    "County",
    "Ntee_Code",
    "Category",
)
DETAIL_COLUMNS = (
    "Ein",
    "Name",
    "Fulladdr",
    "City",
    "State",
    "Zip",
    "County",
    "Ntee_Code",
    "Category",
    "Is_Category_Llm_Generated",
)


def _validate_limit(limit: int) -> int:
    if limit < 1:
        raise ValueError("Validation error: limit must be greater than 0.")
    return limit


def _validate_order(order: str) -> str:
    normalized_order = order.lower()
    if normalized_order not in ALLOWED_ORDER:
        allowed = ", ".join(ALLOWED_ORDER)
        raise ValueError(f"Validation error: order must be one of {allowed}.")
    return normalized_order


def _validate_group_by(group_by: str) -> str:
    if group_by not in ALLOWED_GROUP_BY:
        allowed = ", ".join(ALLOWED_GROUP_BY)
        raise ValueError(f"Validation error: group_by must be one of {allowed}.")
    return group_by


def get_ngo_by_ein(config: dict, ein: int):
    """Fetch a single NGO row by exact EIN."""
    query = """
        SELECT Ein, Name, Fulladdr, City, State, Zip, County, Ntee_Code, Category, Is_Category_Llm_Generated
        FROM ngos_with_categorization
        WHERE Ein = %s
    """

    with connect(**config) as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, (ein,))
            return cursor.fetchall()


def search_ngos(
    config: dict,
    state: str | None = None,
    category: str | None = None,
    city: str | None = None,
    county: str | None = None,
    name_query: str | None = None,
    limit: int = 10,
):
    """Fetch NGO rows using optional filters and a bounded result size."""
    validated_limit = _validate_limit(limit)

    query = f"SELECT {', '.join(SEARCH_COLUMNS)} FROM ngos_with_categorization"
    conditions = []
    params = []

    if state:
        conditions.append("State = %s")
        params.append(state)
    if category:
        conditions.append("Category = %s")
        params.append(category)
    if city:
        conditions.append("City = %s")
        params.append(city)
    if county:
        conditions.append("County = %s")
        params.append(county)
    if name_query:
        conditions.append("Name LIKE %s")
        params.append(f"%{name_query}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY Name ASC, Ein ASC"
    query += " LIMIT %s"
    params.append(validated_limit)

    with connect(**config) as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def summarize_ngos(
    config: dict,
    group_by: str = "Category",
    state: str | None = None,
    category: str | None = None,
    limit: int = 10,
    order: str = "desc",
):
    """Summarize NGO counts by a validated dimension with optional filters."""
    validated_group_by = _validate_group_by(group_by)
    validated_order = _validate_order(order)
    validated_limit = _validate_limit(limit)

    query = f"SELECT {validated_group_by}, COUNT(*) AS ngo_count FROM ngos_with_categorization"
    conditions = []
    params = []

    if state:
        conditions.append("State = %s")
        params.append(state)
    if category:
        conditions.append("Category = %s")
        params.append(category)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += f" GROUP BY {validated_group_by}"
    query += f" ORDER BY ngo_count {validated_order.upper()}, {validated_group_by} {validated_order.upper()}"
    query += " LIMIT %s"
    params.append(validated_limit)

    with connect(**config) as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def main():
    parser = argparse.ArgumentParser(description="Fetch ngos_with_categorization data from the database")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ein_parser = subparsers.add_parser("ein", help="Fetch a single NGO by EIN")
    ein_parser.add_argument("ein", type=int, help="Exact EIN value")

    search_parser = subparsers.add_parser("search", help="Search NGOs with optional filters")
    search_parser.add_argument("--state")
    search_parser.add_argument("--category")
    search_parser.add_argument("--city")
    search_parser.add_argument("--county")
    search_parser.add_argument("--name-query")
    search_parser.add_argument("--limit", "-n", type=int, default=10)

    summarize_parser = subparsers.add_parser("summarize", help="Summarize NGO counts")
    summarize_parser.add_argument("--group-by", default="Category", choices=ALLOWED_GROUP_BY)
    summarize_parser.add_argument("--state")
    summarize_parser.add_argument("--category")
    summarize_parser.add_argument("--limit", "-n", type=int, default=10)
    summarize_parser.add_argument("--order", default="desc", choices=ALLOWED_ORDER)

    args = parser.parse_args()

    try:
        from server import get_mysql_connection_config

        config = get_mysql_connection_config()
        if args.command == "ein":
            rows = get_ngo_by_ein(config=config, ein=args.ein)
        elif args.command == "search":
            rows = search_ngos(
                config=config,
                state=args.state,
                category=args.category,
                city=args.city,
                county=args.county,
                name_query=args.name_query,
                limit=args.limit,
            )
        else:
            rows = summarize_ngos(
                config=config,
                group_by=args.group_by,
                state=args.state,
                category=args.category,
                limit=args.limit,
                order=args.order,
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
