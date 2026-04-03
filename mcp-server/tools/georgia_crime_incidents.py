"""
Georgia NIBRS-style incident/offense rows (one table per calendar year: 2022–2024).
Uses the same MySQL config pattern as other mcp-server tools.
"""
from mysql.connector import connect

ALLOWED_YEARS = (2022, 2023, 2024)

YEAR_TO_TABLE = {
    2022: "georgia_crime_incidents_2022",
    2023: "georgia_crime_incidents_2023",
    2024: "georgia_crime_incidents_2024",
}

ALLOWED_ORDER_BY = (
    "incident_date",
    "submission_date",
    "incident_hour",
    "offense_code",
    "incident_id",
    "offense_incident_id",
)


def _validate_year(year: int) -> int:
    if year not in ALLOWED_YEARS:
        allowed = ", ".join(str(y) for y in ALLOWED_YEARS)
        raise ValueError(f"Validation error: year must be one of {allowed}.")
    return year


def _validate_limit(limit: int) -> int:
    if limit < 1:
        raise ValueError("Validation error: limit must be greater than 0.")
    if limit > 500:
        raise ValueError("Validation error: limit cannot exceed 500.")
    return limit


def _validate_order_by(order_by: str) -> str:
    if order_by not in ALLOWED_ORDER_BY:
        allowed = ", ".join(ALLOWED_ORDER_BY)
        raise ValueError(f"Validation error: order_by must be one of {allowed}.")
    return order_by


def fetch_georgia_crime_incidents(
    config: dict,
    year: int,
    limit: int = 10,
    order_by: str = "incident_date",
    desc: bool = True,
    offense_category: str | None = None,
    offense_name_contains: str | None = None,
    is_hate_crime: bool | None = None,
):
    """
    Fetch rows from the Georgia crime incidents table for the given year.
    Tables: georgia_crime_incidents_2022, _2023, _2024.
    """
    year = _validate_year(year)
    limit = _validate_limit(limit)
    order_by = _validate_order_by(order_by)
    table = YEAR_TO_TABLE[year]

    query = f"SELECT * FROM `{table}`"
    clauses = []
    params = []

    if offense_category is not None and offense_category.strip():
        clauses.append("offense_category_name = %s")
        params.append(offense_category.strip())

    if offense_name_contains is not None and offense_name_contains.strip():
        clauses.append("offense_name LIKE %s")
        params.append(f"%{offense_name_contains.strip()}%")

    if is_hate_crime is not None:
        clauses.append("is_hate_crime = %s")
        params.append(is_hate_crime)

    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    query += f" ORDER BY `{order_by}` {'DESC' if desc else 'ASC'}"
    query += " LIMIT %s"
    params.append(limit)

    with connect(**config) as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
