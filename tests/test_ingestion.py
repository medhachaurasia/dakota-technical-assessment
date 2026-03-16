import unittest
from unittest.mock import Mock, patch

from ingestion.fetch_data import create_session, fetch_enrichment, combine_data


class TestIngestion(unittest.TestCase):

    def test_create_session_returns_session(self):
        session = create_session()
        self.assertIsNotNone(session)

    def test_fetch_enrichment_validates_required_keys(self):
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "date": "2025-01-01",
            "region": "CO",
            "temperature_c": 10.5,
            "demand_index": 0.72,
            "grid_stress_level": "medium",
            "renewable_share_pct": 35.0,
        }
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        result = fetch_enrichment(mock_session, "2025-01-01", "CO")

        self.assertEqual(result["region"], "CO")
        self.assertIn("temperature_c", result)
        self.assertIn("renewable_share_pct", result)

    def test_fetch_enrichment_raises_for_missing_keys(self):
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "date": "2025-01-01",
            "region": "CO",
            "temperature_c": 10.5,
        }
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        with self.assertRaises(ValueError):
            fetch_enrichment(mock_session, "2025-01-01", "CO")

    @patch("ingestion.fetch_data.time.sleep", return_value=None)
    @patch("ingestion.fetch_data.fetch_enrichment")
    def test_combine_data_merges_source_and_enrichment(self, mock_fetch_enrichment, mock_sleep):
        mock_fetch_enrichment.return_value = {
            "date": "2025-01-01",
            "region": "CO",
            "temperature_c": 12.3,
            "demand_index": 0.81,
            "grid_stress_level": "high",
            "renewable_share_pct": 42.5,
        }

        eia_data = [
            {
                "period": "2025-01",
                "stateid": "CO",
                "stateDescription": "Colorado",
                "sectorid": "RES",
                "sectorName": "residential",
                "price": "12.34",
                "sales": "456.78",
                "price-units": "cents per kilowatt-hour",
                "sales-units": "million kilowatt hours",
            }
        ]

        result = combine_data(eia_data, Mock())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["period"], "2025-01-01")
        self.assertEqual(result[0]["state_id"], "CO")
        self.assertEqual(result[0]["price"], 12.34)
        self.assertEqual(result[0]["sales"], 456.78)
        self.assertEqual(result[0]["temperature_c"], 12.3)
        self.assertEqual(result[0]["enrichment_region"], "CO")

    @patch("ingestion.fetch_data.time.sleep", return_value=None)
    @patch("ingestion.fetch_data.fetch_enrichment")
    def test_combine_data_skips_records_with_missing_price(self, mock_fetch_enrichment, mock_sleep):
        eia_data = [
            {
                "period": "2025-01",
                "stateid": "CO",
                "stateDescription": "Colorado",
                "sectorid": "RES",
                "sectorName": "residential",
                "price": None,
                "sales": "456.78",
                "price-units": "cents per kilowatt-hour",
                "sales-units": "million kilowatt hours",
            }
        ]

        result = combine_data(eia_data, Mock())

        self.assertEqual(result, [])
        mock_fetch_enrichment.assert_not_called()


if __name__ == "__main__":
    unittest.main()