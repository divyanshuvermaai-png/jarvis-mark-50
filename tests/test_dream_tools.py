"""
Unit and Integration Tests for Dream Tools (Milestone 2 - Track 1):
- WeatherTool (wttr.in)
- NewsTool (RSS/NewsAPI)
- FinanceTool (Market Quotes)
- SystemControlTool (macOS Audio, Display Lock, WiFi, Clipboard, Notifications)
- DataAnalyticsTool (CSV/Tabular Profiling with pandas)
"""
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
import shutil

from tools.builtins.weather_tool import WeatherTool
from tools.builtins.news_tool import NewsTool
from tools.builtins.finance_tool import FinanceTool
from tools.builtins.system_control_tool import SystemControlTool
from tools.builtins.data_analytics_tool import DataAnalyticsTool
from tools.registry import ToolRegistry


class TestWeatherTool(unittest.TestCase):
    def setUp(self):
        self.tool = WeatherTool()

    def test_schema_and_capability(self):
        self.assertEqual(self.tool.id, "weather")
        self.assertIn("location", self.tool.parameters_schema["properties"])

    @patch("requests.get")
    def test_weather_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "current_condition": [{
                "temp_C": "28",
                "FeelsLikeC": "30",
                "weatherDesc": [{"value": "Sunny"}],
                "humidity": "45",
                "windspeedKmph": "12"
            }],
            "weather": [{
                "maxtempC": "34",
                "mintempC": "22",
                "astronomy": [{"sunrise": "06:10 AM", "sunset": "06:45 PM"}]
            }]
        }
        mock_get.return_value = mock_resp

        res = self.tool.execute({"location": "Jaipur", "format": "detailed"})
        self.assertTrue(res.success)
        self.assertIn("Weather for Jaipur", res.data)
        self.assertIn("Sunny", res.data)
        self.assertIn("28°C", res.data)

    @patch("requests.get")
    def test_weather_network_fallback(self, mock_get):
        mock_get.side_effect = Exception("Connection timeout")
        res = self.tool.execute({"location": "Jaipur"})
        self.assertFalse(res.success)
        self.assertIn("Could not retrieve weather", res.error)


class TestNewsTool(unittest.TestCase):
    def setUp(self):
        self.tool = NewsTool()

    @patch("requests.get")
    def test_rss_news_fallback(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item><title>Apple Unveils M5 Chip Architecture - TechNews</title></item>
                <item><title>AI Agents Breakthrough in 2026 - AI Times</title></item>
            </channel>
        </rss>"""
        mock_get.return_value = mock_resp

        res = self.tool.execute({"category": "technology", "limit": 2})
        self.assertTrue(res.success)
        self.assertIn("Apple Unveils M5 Chip", res.data)
        self.assertIn("AI Agents Breakthrough", res.data)


class TestFinanceTool(unittest.TestCase):
    def setUp(self):
        self.tool = FinanceTool()

    def test_missing_symbol(self):
        res = self.tool.execute({})
        self.assertFalse(res.success)
        self.assertIn("symbol/ticker is required", res.error)

    @patch("requests.get")
    def test_ticker_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "chart": {
                "result": [{
                    "meta": {
                        "regularMarketPrice": 242.50,
                        "chartPreviousClose": 238.00,
                        "currency": "USD",
                        "exchangeName": "NASDAQ",
                        "regularMarketDayHigh": 245.00,
                        "regularMarketDayLow": 237.50,
                        "instrumentType": "EQUITY"
                    }
                }]
            }
        }
        mock_get.return_value = mock_resp

        res = self.tool.execute({"symbol": "AAPL"})
        self.assertTrue(res.success)
        self.assertIn("AAPL (NASDAQ)", res.data)
        self.assertIn("242.5", res.data)
        self.assertIn("+4.5", res.data)


class TestSystemControlTool(unittest.TestCase):
    def setUp(self):
        self.tool = SystemControlTool()

    @patch("subprocess.run")
    def test_set_volume(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        res = self.tool.execute({"action": "set_volume", "value": "75"})
        self.assertTrue(res.success)
        self.assertIn("75%", res.data)
        mock_run.assert_called()

    @patch("subprocess.run")
    def test_wifi_status(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="Current Wi-Fi Network: Verma_5G\n")
        res = self.tool.execute({"action": "wifi_status"})
        self.assertTrue(res.success)
        self.assertIn("Verma_5G", res.data)

    @patch("subprocess.run")
    def test_notify(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        res = self.tool.execute({"action": "notify", "title": "JARVIS Alert", "value": "Task completed"})
        self.assertTrue(res.success)
        self.assertIn("Notification dispatched", res.data)


class TestDataAnalyticsTool(unittest.TestCase):
    def setUp(self):
        self.tool = DataAnalyticsTool()
        self.test_dir = tempfile.mkdtemp()
        self.csv_path = os.path.join(self.test_dir, "sample.csv")
        with open(self.csv_path, "w") as f:
            f.write("id,category,score\n1,AI,95\n2,Cloud,88\n3,Security,92\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_csv_analysis(self):
        res = self.tool.execute({"file_path": self.csv_path})
        self.assertTrue(res.success)
        self.assertIn("3 rows × 3 columns", res.data)
        self.assertIn("score", res.data)
        self.assertIn("mean=", res.data)

    def test_missing_file(self):
        res = self.tool.execute({"file_path": "/tmp/nonexistent_xyz_123.csv"})
        self.assertFalse(res.success)
        self.assertIn("does not exist", res.error)


if __name__ == "__main__":
    unittest.main()
