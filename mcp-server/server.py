"""Basic MCP server with arithmetic and read-only MySQL tools."""

import json
from pathlib import Path
from urllib.parse import urlparse

from mcp.server.fastmcp import FastMCP
from mysql.connector import Error, connect

mcp = FastMCP("Basic MCP Server")

ALLOWED_READ_ONLY_SQL = ("SELECT", "SHOW", "DESCRIBE", "EXPLAIN")


def get_shared_config_path() -> Path:
    """Resolve the repo-root shared configuration path."""
    return Path(__file__).resolve().parent.parent / "config.json"


def load_shared_config() -> dict:
    """Load and validate shared DB/Redis config values."""
    config_path = get_shared_config_path()
    if not config_path.exists():
        raise RuntimeError(f"Configuration error: missing config file at {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as file:
            config = json.load(file)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Configuration error: invalid JSON in {config_path}") from exc

    required_keys = ("db_url", "db_username", "db_password")
    missing_keys = [key for key in required_keys if not config.get(key)]
    if missing_keys:
        raise RuntimeError(f"Configuration error: missing required keys: {', '.join(missing_keys)}")
    return config


def get_mysql_connection_config() -> dict:
    """Build mysql-connector config from shared settings."""
    config = load_shared_config()
    parsed = urlparse(config["db_url"])
    if parsed.scheme != "mysql+mysqlconnector":
        raise RuntimeError("Configuration error: db_url must use mysql+mysqlconnector scheme")
    if not parsed.hostname:
        raise RuntimeError("Configuration error: db_url is missing host")

    database = parsed.path.lstrip("/")
    if not database:
        raise RuntimeError("Configuration error: db_url is missing database name")

    username = config.get("db_username") or parsed.username
    password = config.get("db_password") or parsed.password
    if not username or not password:
        raise RuntimeError("Configuration error: database username/password are required")

    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": username,
        "password": password,
        "database": database,
        "autocommit": True,
    }


def _validate_read_only_query(query: str) -> str:
    trimmed_query = query.strip()
    if not trimmed_query:
        raise ValueError("Validation error: query is required.")

    first_statement = trimmed_query.split(";", 1)[0].strip()
    first_keyword = first_statement.split(None, 1)[0].upper() if first_statement else ""
    if first_keyword not in ALLOWED_READ_ONLY_SQL:
        allowed = ", ".join(ALLOWED_READ_ONLY_SQL)
        raise ValueError(f"Validation error: only read-only SQL is allowed ({allowed}).")
    return trimmed_query


def _rows_to_csv_text(columns, rows) -> str:
    header = ",".join(str(column) for column in columns)
    data_rows = [",".join(str(value) for value in row) for row in rows]
    return "\n".join([header] + data_rows)


@mcp.tool()
def divide(a: int, b: int) -> int:
    """Divide two numbers."""
    return a // b


@mcp.tool()
def execute_sql(query: str) -> str:
    """Execute a read-only SQL query against the configured MySQL database."""
    try:
        validated_query = _validate_read_only_query(query)
    except ValueError as exc:
        return str(exc)

    try:
        mysql_config = get_mysql_connection_config()
        with connect(**mysql_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(validated_query)
                if cursor.description is None:
                    return "Query executed successfully. No result set was returned."

                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                return _rows_to_csv_text(columns, rows)
    except RuntimeError as exc:
        return str(exc)
    except Error as exc:
        return f"Database error: {exc}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
