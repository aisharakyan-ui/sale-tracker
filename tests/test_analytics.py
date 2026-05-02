from __future__ import annotations

import os
import tempfile
import unittest

from app import analytics, db
from app.seed import seed_demo_data


class AnalyticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        db.DB_PATH = os.path.join(self.temp_dir.name, "test.db")
        db.init_db()
        seed_demo_data()

    def tearDown(self) -> None:
        db.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_lists_seeded_brands(self) -> None:
        brands = analytics.list_brands()
        self.assertEqual(len(brands), 6)

    def test_price_history_returns_two_year_metrics(self) -> None:
        history = analytics.get_price_history(product_id=1, days=730)
        self.assertGreater(len(history["points"]), 90)
        self.assertGreaterEqual(history["max_price"], history["min_price"])
        self.assertEqual(history["currency"], "USD")

    def test_sale_calendar_ranks_peak_months(self) -> None:
        calendar = analytics.get_brand_sale_calendar(brand_id=1, days=730, sale_threshold=0.92)
        self.assertTrue(calendar["top_sale_months"])
        november = next(month for month in calendar["months"] if month["month"] == 11)
        self.assertGreater(november["sale_rate"], 0)


if __name__ == "__main__":
    unittest.main()
