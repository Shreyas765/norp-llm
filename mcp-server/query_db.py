#!/usr/bin/env python3
"""
Small CLI tool to run read-only SQL against the shared MySQL database.
Uses the same config as the MCP server (config.json at repo root).
"""
import sys
from pathlib import Path

# Add parent so we can import from server
sys.path.insert(0, str(Path(__file__).resolve().parent))

from server import get_mysql_connection_config, execute_sql


def main():
    if len(sys.argv) < 2:
        print("Usage: python query_db.py <SQL query>")
        print("Example: python query_db.py 'SELECT * FROM us_population_county LIMIT 5'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    result = execute_sql(query)
    print(result)


if __name__ == "__main__":
    main()
