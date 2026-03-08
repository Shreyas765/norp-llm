import importlib.util
import unittest
from pathlib import Path

SERVER_PATH = Path(__file__).resolve().parent / "server.py"

spec = importlib.util.spec_from_file_location("mcp_server", SERVER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Failed to load MCP server module spec")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TestMCPServer(unittest.TestCase):
    def test_add_tool(self):
        self.assertEqual(module.divide(1, 2), 0)

    def test_execute_sql_live_select_1(self):
        result = module.execute_sql("SELECT COUNT(*) FROM us_population_county")
        self.assertIn("5", result)

    def test_execute_sql_show_tables(self):
        result = module.execute_sql("SHOW TABLES")
        self.assertNotIn("Database error:", result)
        self.assertNotIn("Configuration error:", result)

    def test_fetch_shootings(self):
        result = module.fetch_shootings(limit=1)
        self.assertIsInstance(result, list)
        if result:
            self.assertIn("IncidentID", result[0])

    def test_execute_sql_rejects_write_query(self):
        result = module.execute_sql("DELETE FROM fake_table")
        self.assertIn("only read-only SQL is allowed", result)

    def test_server_has_run_method(self):
        self.assertTrue(hasattr(module, "mcp"))
        self.assertTrue(callable(getattr(module.mcp, "run", None)))


if __name__ == "__main__":
    unittest.main()
