"""
Tests for J.A.R.V.I.S. Live Observability & Telemetry Engine (Phase 7)
Verifies rolling metrics, token throughput, tool tracking, event bus binding,
and HTTP/SSE telemetry endpoints.
"""
import unittest
import time
import json
from unittest.mock import MagicMock

from interfaces.telemetry import TelemetryEngine, RollingWindow, ToolExecutionStats, telemetry_engine
from core.events import event_bus, Event, EventType
from core.diagnostics import SystemHealthCheck, SubsystemStatus
from main import app


class TestRollingWindow(unittest.TestCase):
    def test_empty_window_stats(self):
        w = RollingWindow(maxlen=10)
        st = w.stats()
        self.assertEqual(st["count"], 0)
        self.assertEqual(st["mean"], 0.0)
        self.assertEqual(st["p50"], 0.0)

    def test_percentile_calculations(self):
        w = RollingWindow(maxlen=100)
        for val in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            w.add(val)
        st = w.stats()
        self.assertEqual(st["count"], 10)
        self.assertEqual(st["min"], 10.0)
        self.assertEqual(st["max"], 100.0)
        self.assertEqual(st["mean"], 55.0)
        self.assertAlmostEqual(st["p50"], 60.0, delta=10.0)

    def test_maxlen_eviction(self):
        w = RollingWindow(maxlen=5)
        for i in range(10):
            w.add(i)
        self.assertEqual(w.count(), 5)
        st = w.stats()
        self.assertEqual(st["min"], 5.0)
        self.assertEqual(st["max"], 9.0)

    def test_get_series(self):
        w = RollingWindow(maxlen=5)
        w.add(42.5)
        series = w.get_series()
        self.assertEqual(len(series), 1)
        self.assertEqual(series[0]["value"], 42.5)
        self.assertIn("timestamp", series[0])


class TestToolExecutionStats(unittest.TestCase):
    def test_stats_aggregation(self):
        stats = ToolExecutionStats()
        stats.calls = 4
        stats.success = 3
        stats.failed = 1
        stats.total_duration_ms = 400.0

        d = stats.to_dict()
        self.assertEqual(d["calls"], 4)
        self.assertEqual(d["success"], 3)
        self.assertEqual(d["failed"], 1)
        self.assertEqual(d["avg_duration_ms"], 100.0)
        self.assertEqual(d["success_rate_pct"], 75.0)


class TestTelemetryEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TelemetryEngine()
        self.engine.reset_metrics()

    def test_hardware_sampling(self):
        hw = self.engine.sample_hardware(force=True)
        self.assertIn("cpu_percent", hw)
        self.assertIn("memory", hw)
        self.assertIn("percent", hw["memory"])
        self.assertIn("pressure", hw["memory"])
        self.assertIn("disk", hw)
        self.assertIn("free_gb", hw["disk"])
        self.assertIn(hw["memory"]["pressure"], ["normal", "warning", "critical", "unknown"])

    def test_record_latency_and_tools(self):
        self.engine.record_request_latency(125.0)
        self.engine.record_request_latency(175.0)
        self.engine.record_tool_execution("macos_window", 45.0, success=True)
        self.engine.record_tool_execution("macos_window", 55.0, success=True)
        self.engine.record_tool_execution("file_ops", 20.0, success=False)

        snap = self.engine.get_snapshot()
        self.assertEqual(snap["latency"]["count"], 2)
        self.assertEqual(snap["latency"]["mean"], 150.0)

        self.assertIn("macos_window", snap["tools"])
        self.assertEqual(snap["tools"]["macos_window"]["calls"], 2)
        self.assertEqual(snap["tools"]["macos_window"]["success"], 2)

        self.assertIn("file_ops", snap["tools"])
        self.assertEqual(snap["tools"]["file_ops"]["failed"], 1)

    def test_record_inference_and_tokens(self):
        self.engine.record_inference("gemini", prompt_tokens=150, completion_tokens=50)
        self.engine.record_inference("local_gemma", prompt_tokens=200, completion_tokens=100)

        snap = self.engine.get_snapshot()
        tok = snap["tokens"]
        self.assertEqual(tok["total_queries"], 2)
        self.assertEqual(tok["prompt_tokens"], 350)
        self.assertEqual(tok["completion_tokens"], 150)
        self.assertEqual(tok["total_tokens"], 500)
        self.assertEqual(tok["provider_queries"]["gemini"], 1)
        self.assertEqual(tok["provider_queries"]["local_gemma"], 1)

    def test_event_bus_binding(self):
        self.engine.connect_event_bus()

        event_bus.publish(Event(EventType.TASK_CREATED, "test", {}))
        snap = self.engine.get_snapshot()
        self.assertEqual(snap["tasks"]["active"], 1)

        event_bus.publish(Event(EventType.TASK_COMPLETED, "test", {"duration_ms": 80.0}))
        snap = self.engine.get_snapshot()
        self.assertEqual(snap["tasks"]["active"], 0)
        self.assertEqual(snap["tasks"]["completed"], 1)
        self.assertGreaterEqual(snap["latency"]["count"], 1)

        event_bus.publish(Event(EventType.TOOL_EXECUTED, "test", {
            "tool_name": "apple_suite",
            "duration_ms": 32.0,
            "success": True
        }))
        snap = self.engine.get_snapshot()
        self.assertIn("apple_suite", snap["tools"])
        self.assertEqual(snap["tools"]["apple_suite"]["calls"], 1)

    def test_stream_events_generator(self):
        gen = self.engine.stream_events(interval_sec=0.01)
        payload = next(gen)
        self.assertTrue(payload.startswith("data: "))
        self.assertTrue(payload.endswith("\n\n"))
        data_json = json.loads(payload[6:].strip())
        self.assertIn("hardware", data_json)
        self.assertIn("uptime_seconds", data_json)


class TestTelemetryAPI(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_api_telemetry_endpoint(self):
        res = self.client.get('/api/telemetry')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("hardware", data)
        self.assertIn("latency", data)
        self.assertIn("tokens", data)
        self.assertIn("tools", data)
        self.assertIn("security", data)

    def test_api_health_endpoint(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("overall_status", data)
        self.assertIn("operational", data)
        self.assertIn("subsystems", data)
        self.assertIn("memory_usage_pct", data)
        self.assertIn("free_ram_gb", data)
        self.assertIn("disk_free_gb", data)
        self.assertTrue(data["operational"])


if __name__ == '__main__':
    unittest.main()
