import unittest

import pandas as pd

from app.models.reconciliation_result import ReconciliationStatus
from app.services.reconciliation_engine import ReconciliationEngine


class ReconciliationEngineTests(unittest.TestCase):
    def test_transaction_in_later_processor_file_is_not_missing(self):
        company = pd.DataFrame([
            {"transaction_id": "company-only", "amount": 100, "status": "SUCCESS"},
            {"transaction_id": "in-second-file", "amount": 200, "status": "SUCCESS"},
        ])
        first_processor = pd.DataFrame([
            {"transaction_id": "company-only", "amount": 100, "status": "SUCCESS"},
        ])
        second_processor = pd.DataFrame([
            {"transaction_id": "in-second-file", "amount": 200, "status": "SUCCESS"},
        ])

        results = ReconciliationEngine.reconcile(
            company, pd.concat([first_processor, second_processor], ignore_index=True)
        )
        statuses = {row["transaction_id"]: row["status"] for row in results}

        self.assertEqual(statuses["company-only"], ReconciliationStatus.MATCHED)
        self.assertEqual(statuses["in-second-file"], ReconciliationStatus.MATCHED)
        self.assertNotIn(ReconciliationStatus.MISSING_IN_PROCESSOR, statuses.values())

    def test_missing_in_processor_requires_absence_from_combined_dataset(self):
        company = pd.DataFrame([
            {"transaction_id": "not-in-any-file", "amount": 100, "status": "SUCCESS"},
        ])
        processors = pd.DataFrame([
            {"transaction_id": "other-transaction", "amount": 100, "status": "SUCCESS"},
        ])

        results = ReconciliationEngine.reconcile(company, processors)
        statuses = {row["transaction_id"]: row["status"] for row in results}

        self.assertEqual(
            statuses["not-in-any-file"], ReconciliationStatus.MISSING_IN_PROCESSOR
        )


if __name__ == "__main__":
    unittest.main()
