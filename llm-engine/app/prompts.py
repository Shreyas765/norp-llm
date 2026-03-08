from langchain_classic.prompts import ChatPromptTemplate, MessagesPlaceholder

from constants import TOP_K_ROWS

## Prompts to create SQL query
# This is the first prompt with all table schema, 3 rows of every table information
INITIAL_DATABASE_INFO_PROMPT = "You are a MySQL expert. Given an input question, create a syntactically correct SQL query to run. Unless otherwise specified, do not return more than {top_k} rows.\n\nHere is the relevant table info: {table_info}."
# For upcoming chat, where table info is already present in the history
CONTINUATION_PROMPT = "Generate ONLY the SQL query based on user's question and history. Filter out rows with any NULL field. If the question is unclear, try your best to create SQL query."
RESPONSE_FORMAT = " IMPORTANT: Respond ONLY with the complete SQL query, without any additional text or explanation."
# Failure message when LLM is unable to generate the SQL query
FAILURE_MESSAGE_FORMAT = " If you could not generate a SQL query, give the reason in at most 50 words."
# MCP-only prompt (previous version retained for later use)
# MCP_SYSTEM_PROMPT = (
#     "You are assisting with an MCP server that exposes tools. "
#     "Do not generate SQL. "
#     "Available MCP tools: divide(a: int, b: int) -> int (integer division). "
#     "Use tools when appropriate; otherwise respond directly."
# )
MCP_SYSTEM_PROMPT = (
    "You are assisting with an MCP server that exposes tools. "
    "Available MCP tools: "
    "fetch_us_shootings(state: str | None, limit: int, order_by: str, desc: bool) -> str "
    "(fetch us_shootings rows, returns CSV); "
    "divide(a: int, b: int) -> int (integer division); "
    "execute_sql(query: str) -> str (run a read-only SQL query against the MySQL database, returns CSV). "
    "\n\n"
    "TOOL SELECTION - IMPORTANT:\n"
    "• Use fetch_us_shootings when the user asks to list, show, get, or retrieve us_shootings rows "
    "(e.g. 'Show me 5 shootings in Texas', 'List shootings in California', 'Get shootings in New York', "
    "'What shootings happened in Florida?'). Pass state as the state name (e.g. 'Texas', 'California'). "
    f"Default limit={TOP_K_ROWS} unless the user specifies otherwise.\n"
    "• Use execute_sql only for: COUNT/SUM/AVG aggregations, questions about other tables, "
    "date-range filters, JOINs, or when fetch_us_shootings cannot answer (e.g. 'How many shootings in X?').\n"
    "\n"
    "If you use a tool, return the exact value from that tool and treat it as truth. "
    "Use tools when appropriate; otherwise respond directly.\n\n"
    "Database schema:\n{table_info}"
)
# Aggregated Group by
GROUP_BY_PROMPT = """
    While working with MySQL databases under `ONLY_FULL_GROUP_BY` mode.
    Ensure the query satisfies:
    1. All non-aggregated columns in the `SELECT` list are included in the `GROUP BY` clause or are aggregated.
    2. Use aggregate functions appropriately.
    """
GROUP_BY_PROMPT_V2 = """
1. Ensure all non-aggregated columns in the `SELECT` list are included in the `GROUP BY` clause or are aggregated.
2. Use aggregate functions appropriately to avoid grouping errors.
3. Provide meaningful aliases for calculated columns.
"""
GROUP_BY_PROMPT_V3 = """
You are a SQL expert working with MySQL databases under `ONLY_FULL_GROUP_BY` mode.
Constraints:
1. Ensure all non-aggregated columns in the `SELECT` list are included in the `GROUP BY` clause or are aggregated.
2. Use aggregate functions appropriately to avoid grouping errors.
3. Provide meaningful aliases for calculated columns.

For example:
Write the query for this task:
"Calculate victims killed per million capita for each state."

Correct:
SELECT State,
       SUM(VictimsKilled) / SUM(PopulationCount) * 1000000 AS VictimsKilledPerMillionCapita
FROM us_shootings
JOIN us_population ON us_shootings.State = us_population.State
GROUP BY State;

Incorrect:
SELECT State,
       SUM(VictimsKilled) / PopulationCount * 1000000 AS VictimsKilledPerMillionCapita
FROM us_shootings
JOIN us_population ON us_shootings.State = us_population.State
GROUP BY State;
"""
# Chat prompt template for a new chat
INITIAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", INITIAL_DATABASE_INFO_PROMPT),
])

# Chat prompt tenplate for a continuation chat
CONTINUATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", CONTINUATION_PROMPT + GROUP_BY_PROMPT_V3 + RESPONSE_FORMAT + FAILURE_MESSAGE_FORMAT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])

# MCP-only prompt template (table_info, question, history)
MCP_PROMPT = ChatPromptTemplate.from_messages([
    ("system", MCP_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])
