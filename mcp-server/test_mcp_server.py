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
    def assert_live_db_result(self, result: str):
        if "Database error:" in result or "Configuration error:" in result:
            self.skipTest(result)
        self.assertIsInstance(result, str)

    def test_add_tool(self):
        self.assertEqual(module.divide(1, 2), 0)

    def test_execute_sql_live_select_1(self):
        result = module.execute_sql("SELECT COUNT(*) FROM us_population_county")
        self.assert_live_db_result(result)
        self.assertIn("5", result)

    def test_execute_sql_show_tables(self):
        result = module.execute_sql("SHOW TABLES")
        self.assert_live_db_result(result)

    def test_fetch_us_shootings(self):
        result = module.fetch_us_shootings(limit=1)
        self.assert_live_db_result(result)
        self.assertIn("IncidentID", result)

    def test_get_state_unemployment_summary(self):
        result = module.get_state_unemployment_summary("California")
        self.assert_live_db_result(result)
        self.assertIn("State", result)
        self.assertIn("Rate_2023", result)
        self.assertIn("California", result)

    def test_get_state_unemployment_summary_united_states(self):
        result = module.get_state_unemployment_summary("United States")
        self.assert_live_db_result(result)
        self.assertIn("United States", result)

    def test_compare_unemployment_states(self):
        result = module.compare_unemployment_states("Texas", "California")
        self.assert_live_db_result(result)
        self.assertIn("Texas", result)
        self.assertIn("California", result)

    def test_compare_unemployment_states_default_target(self):
        result = module.compare_unemployment_states("Texas")
        self.assert_live_db_result(result)
        self.assertIn("Texas", result)
        self.assertIn("United States", result)

    def test_list_unemployment_rankings(self):
        result = module.list_unemployment_rankings(limit=3)
        self.assert_live_db_result(result)
        self.assertIn("State", result)

    def test_list_unemployment_rankings_rate_change_asc(self):
        result = module.list_unemployment_rankings(metric="Rate_Change", order="asc", limit=5)
        self.assert_live_db_result(result)
        self.assertIn("Rate_Change", result)

    def test_list_unemployment_rankings_rejects_invalid_metric(self):
        result = module.list_unemployment_rankings(metric="BadMetric")
        self.assertIn("Validation error:", result)

    def test_list_unemployment_rankings_rejects_invalid_order(self):
        result = module.list_unemployment_rankings(order="sideways")
        self.assertIn("Validation error:", result)

    def test_execute_sql_rejects_write_query(self):
        result = module.execute_sql("DELETE FROM fake_table")
        self.assertIn("only read-only SQL is allowed", result)

    def test_server_has_run_method(self):
        self.assertTrue(hasattr(module, "mcp"))
        self.assertTrue(callable(getattr(module.mcp, "run", None)))


if __name__ == "__main__":
    unittest.main()
