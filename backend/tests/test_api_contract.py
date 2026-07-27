import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rescue_me.api import open_db


class ApiContractTest(unittest.TestCase):
    def test_api_can_initialize_database(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as tmp:
            connection = open_db(tmp.name)
            policy = connection.execute("SELECT id FROM escalation_policies").fetchone()
            connection.close()

        self.assertEqual(policy["id"], "default-sar")

    def test_forecast_contract_documents_contours(self):
        with open("docs/api/monitored-session-api.md", encoding="utf-8") as handle:
            contract = handle.read()

        self.assertIn("probability contours", contract)
        self.assertIn("Telemetry ingestion is idempotent", contract)
        self.assertIn("X-Incident-Share-Token", contract)


if __name__ == "__main__":
    unittest.main()
