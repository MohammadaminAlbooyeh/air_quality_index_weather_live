# Tests for the main application
import unittest
from fastapi.testclient import TestClient
from backend.main import app

class TestMainApp(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json())

    def test_air_quality_endpoint(self):
        response = self.client.get('/air-quality-coords/45.0703/7.6869')
        self.assertEqual(response.status_code, 200)
        self.assertIn('aqi', response.json())

if __name__ == '__main__':
    unittest.main()