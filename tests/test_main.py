# Tests for the main application
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import os
import sys

# Set environment variable for testing
os.environ["WAQI_API_TOKEN"] = "test_token_12345"

from backend.main import app, get_cached_data, set_cached_data, cache, request_stats


class TestMainApp(unittest.TestCase):
    """Test suite for the Air Quality Index API"""

    def setUp(self):
        """Set up test client and clear cache before each test"""
        self.client = TestClient(app)
        cache.clear()
        # Reset request stats
        request_stats["total_requests"] = 0
        request_stats["cache_hits"] = 0
        request_stats["cache_misses"] = 0
        request_stats["errors"] = 0

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        response = self.client.get("/api")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("version", data)
        self.assertIn("endpoints", data)

    def test_health_check(self):
        """Test the health check endpoint"""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)
        self.assertIn("cache_size", data)

    def test_stats_endpoint(self):
        """Test the statistics endpoint"""
        response = self.client.get("/api/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_requests", data)
        self.assertIn("cache_hits", data)
        self.assertIn("cache_misses", data)
        self.assertIn("cache_hit_rate", data)
        self.assertIn("errors", data)
        self.assertIn("cached_items", data)

    @patch("backend.main.requests.get")
    def test_air_quality_city_endpoint(self, mock_get):
        """Test fetching AQI data by city name"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "data": {"aqi": 50, "city": {"name": "London"}, "dominentpol": "pm25"},
        }
        mock_get.return_value = mock_response

        response = self.client.get("/api/air-quality/London")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("aqi", data)
        self.assertEqual(data["aqi"], 50)

    @patch("backend.main.requests.get")
    def test_air_quality_coords_endpoint(self, mock_get):
        """Test fetching AQI data by coordinates"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok", "data": {"aqi": 75, "city": {"name": "Paris"}, "dominentpol": "o3"}}
        mock_get.return_value = mock_response

        response = self.client.get("/api/air-quality-coords/48.8566/2.3522")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("aqi", data)
        self.assertEqual(data["aqi"], 75)

    @patch("backend.main.requests.get")
    def test_air_quality_city_not_found(self, mock_get):
        """Test handling of city not found error"""
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        response = self.client.get("/api/air-quality/InvalidCityName")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("detail", data)

    @patch("backend.main.requests.get")
    def test_caching_functionality(self, mock_get):
        """Test that caching works correctly"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "data": {"aqi": 100, "city": {"name": "Tokyo"}, "dominentpol": "pm25"},
        }
        mock_get.return_value = mock_response

        # First request - should hit the API
        response1 = self.client.get("/api/air-quality/Tokyo")
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(mock_get.call_count, 1)

        # Second request - should use cache
        response2 = self.client.get("/api/air-quality/Tokyo")
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(mock_get.call_count, 1)  # Should not call API again

        # Verify both responses are identical
        self.assertEqual(response1.json(), response2.json())

    def test_cache_functions(self):
        """Test cache helper functions"""
        # Test setting and getting cache
        test_key = "test_key"
        test_data = {"test": "data"}

        # Initially should return None
        self.assertIsNone(get_cached_data(test_key))

        # Set cache
        set_cached_data(test_key, test_data)

        # Should now return cached data
        cached = get_cached_data(test_key)
        self.assertEqual(cached, test_data)

    @patch("backend.main.requests.get")
    def test_api_timeout_handling(self, mock_get):
        """Test handling of API timeout errors"""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout()

        response = self.client.get("/api/air-quality/TestCity")
        self.assertEqual(response.status_code, 504)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("timeout", data["detail"].lower())

    @patch("backend.main.requests.get")
    def test_api_connection_error(self, mock_get):
        """Test handling of connection errors"""
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError()

        response = self.client.get("/api/air-quality/TestCity")
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("connection", data["detail"].lower())


class TestCacheManagement(unittest.TestCase):
    """Test suite for cache management"""

    def setUp(self):
        """Clear cache before each test"""
        cache.clear()

    def test_cache_expiration(self):
        """Test that cache expires after CACHE_DURATION"""
        import time
        from backend.main import CACHE_DURATION

        test_key = "expiry_test"
        test_data = {"test": "data"}

        # Set cache with old timestamp (expired)
        cache[test_key] = (test_data, time.time() - CACHE_DURATION - 10)

        # Should return None as cache is expired
        result = get_cached_data(test_key)
        self.assertIsNone(result)

    def test_multiple_cache_entries(self):
        """Test handling multiple cache entries"""
        entries = {"city:London": {"aqi": 50}, "city:Paris": {"aqi": 60}, "coords:48.85:2.35": {"aqi": 70}}

        # Set all entries
        for key, data in entries.items():
            set_cached_data(key, data)

        # Verify all can be retrieved
        for key, expected_data in entries.items():
            cached = get_cached_data(key)
            self.assertEqual(cached, expected_data)


if __name__ == "__main__":
    unittest.main()
