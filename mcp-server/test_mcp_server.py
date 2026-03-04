import importlib.util
import unittest
from pathlib import Path

SERVER_PATH = Path(__file__).resolve().parent / "server.py"

spec = importlib.util.spec_from_file_location("mcp_server", SERVER_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TestMCPServer(unittest.TestCase):
    def test_add_tool(self):
        self.assertEqual(module.add(1, 2), 3)

    def test_server_has_run_method(self):
        self.assertTrue(hasattr(module, "mcp"))
        self.assertTrue(callable(getattr(module.mcp, "run", None)))


if __name__ == "__main__":
    unittest.main()
