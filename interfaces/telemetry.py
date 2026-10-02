"""
J.A.R.V.I.S. Live Observability & Telemetry Engine
Aggregates real-time hardware vitals, model token throughput, tool latencies,
task execution DAG states, and security kernel metrics for the HUD.
"""
import time
import psutil
import shutil
import os
import json
import logging
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Generator
from datetime import datetime

from core.events import event_bus, Event, EventType

logger = logging.getLogger("jarvis.interfaces.telemetry")


@dataclass
class ToolExecutionStats:
    calls: int = 0
    success: int = 0
    failed: int = 0
    total_duration_ms: float = 0.0

    @property
    def avg_duration_ms(self) -> float:
        return round(self.total_duration_ms / max(1, self.calls), 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "calls": self.calls,
            "success": self.success,
            "failed": self.failed,
            "avg_duration_ms": self.avg_duration_ms,
            "success_rate_pct": round((self.success / max(1, self.calls)) * 100.0, 1)
        }


class RollingWindow:
    """Thread-safe circular buffer for computing rolling percentiles and averages."""
    def __init__(self, maxlen: int = 100):
        self.maxlen = maxlen
        self._buffer = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def add(self, value: float):
        with self._lock:
            self._buffer.append((time.time(), float(value)))

    def count(self) -> int:
        with self._lock:
            return len(self._buffer)

    def stats(self) -> Dict[str, float]:
        with self._lock:
            if not self._buffer:
                return {"count": 0, "mean": 0.0, "p50": 0.0, "p90": 0.0, "p95": 0.0, "min": 0.0, "max": 0.0}
            vals = sorted(v for _, v in self._buffer)
            n = len(vals)
            mean_val = sum(vals) / n
            p50 = vals[int(n * 0.50)]
            p90 = vals[min(n - 1, int(n * 0.90))]
            p95 = vals[min(n - 1, int(n * 0.95))]
            return {
                "count": n,
                "mean": round(mean_val, 2),
                "p50": round(p50, 2),
                "p90": round(p90, 2),
                "p95": round(p95, 2),
                "min": round(vals[0], 2),
                "max": round(vals[-1], 2)
            }

    def get_series(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [{"timestamp": ts, "value": round(val, 2)} for ts, val in self._buffer]


class TelemetryEngine:
    """
    Central telemetry and live observability engine for J.A.R.V.I.S.
    Collects system vitals, agent workflow metrics, model throughput, and tool execution stats.
    """
    _instance: Optional["TelemetryEngine"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TelemetryEngine, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, history_len: int = 60):
        if self._initialized:
            return
        self.history_len = history_len
        self._state_lock = threading.Lock()

        # Rolling time series
        self.latency_window = RollingWindow(maxlen=history_len)
        self.cpu_window = RollingWindow(maxlen=history_len)
        self.memory_window = RollingWindow(maxlen=history_len)

        # Tool stats
        self._tool_stats: Dict[str, ToolExecutionStats] = {}

        # Task DAG counters
        self._active_tasks: int = 0
        self._completed_tasks: int = 0
        self._failed_tasks: int = 0

        # Token & Inference counters
        self._prompt_tokens: int = 0
        self._completion_tokens: int = 0
        self._model_queries: int = 0
        self._provider_queries: Dict[str, int] = {}
        self._start_time = time.time()

        # Hardware sample throttle
        self._last_hw_sample = 0.0
        self._cached_hw: Dict[str, Any] = {}

        # Connect to core event bus
        self._connected_bus = False
        self.connect_event_bus()

        self._initialized = True
        logger.info("TelemetryEngine initialized with rolling history length %d.", history_len)

    def connect_event_bus(self):
        """Subscribe to relevant domain events on the global EventBus."""
        if self._connected_bus:
            return
        try:
            event_bus.subscribe(EventType.TASK_CREATED, self._on_task_created)
            event_bus.subscribe(EventType.TASK_COMPLETED, self._on_task_completed)
            event_bus.subscribe(EventType.TASK_FAILED, self._on_task_failed)
            event_bus.subscribe(EventType.TOOL_EXECUTED, self._on_tool_executed)
            event_bus.subscribe(EventType.MODEL_ROUTED, self._on_model_routed)
            self._connected_bus = True
            logger.info("TelemetryEngine bound to core EventBus.")
        except Exception as e:
            logger.warning("TelemetryEngine could not bind to EventBus: %s", e)

    def _on_task_created(self, event: Event):
        with self._state_lock:
            self._active_tasks += 1

    def _on_task_completed(self, event: Event):
        with self._state_lock:
            self._active_tasks = max(0, self._active_tasks - 1)
            self._completed_tasks += 1
            duration_ms = event.payload.get("duration_ms", 0.0)
            if duration_ms > 0:
                self.latency_window.add(duration_ms)

    def _on_task_failed(self, event: Event):
        with self._state_lock:
            self._active_tasks = max(0, self._active_tasks - 1)
            self._failed_tasks += 1
            duration_ms = event.payload.get("duration_ms", 0.0)
            if duration_ms > 0:
                self.latency_window.add(duration_ms)

    def _on_tool_executed(self, event: Event):
        tool_name = event.payload.get("tool_name", "unknown")
        duration_ms = float(event.payload.get("duration_ms", 0.0))
        success = bool(event.payload.get("success", True))
        self.record_tool_execution(tool_name, duration_ms, success)

    def _on_model_routed(self, event: Event):
        provider = event.payload.get("provider", "unknown")
        prompt_tokens = int(event.payload.get("prompt_tokens", 0))
        completion_tokens = int(event.payload.get("completion_tokens", 0))
        self.record_inference(provider, prompt_tokens, completion_tokens)

    def record_request_latency(self, duration_ms: float):
        """Explicitly record a request latency observation."""
        self.latency_window.add(duration_ms)

    def record_tool_execution(self, tool_name: str, duration_ms: float, success: bool = True):
        """Record execution metrics for a specific tool."""
        with self._state_lock:
            if tool_name not in self._tool_stats:
                self._tool_stats[tool_name] = ToolExecutionStats()
            st = self._tool_stats[tool_name]
            st.calls += 1
            if success:
                st.success += 1
            else:
                st.failed += 1
            st.total_duration_ms += duration_ms

    def record_inference(self, provider: str, prompt_tokens: int = 0, completion_tokens: int = 0):
        """Record model inference invocation and token consumption."""
        with self._state_lock:
            self._model_queries += 1
            self._prompt_tokens += prompt_tokens
            self._completion_tokens += completion_tokens
            self._provider_queries[provider] = self._provider_queries.get(provider, 0) + 1

    def sample_hardware(self, force: bool = False) -> Dict[str, Any]:
        """Poll host CPU, memory, and disk headroom, caching briefly to prevent load."""
        now = time.time()
        if not force and (now - self._last_hw_sample < 0.5) and self._cached_hw:
            return self._cached_hw

        try:
            # Memory
            vmem = psutil.virtual_memory()
            mem_pct = round(vmem.percent, 1)
            used_mb = round(vmem.used / (1024 * 1024), 1)
            total_mb = round(vmem.total / (1024 * 1024), 1)
            free_gb = round(vmem.available / (1024 * 1024 * 1024), 2)

            # Unified Memory Pressure indicator
            if mem_pct > 90:
                pressure = "critical"
            elif mem_pct > 80:
                pressure = "warning"
            else:
                pressure = "normal"

            # CPU
            cpu_pct = round(psutil.cpu_percent(interval=None), 1)
            cpu_count = psutil.cpu_count() or 8

            # Disk
            disk = shutil.disk_usage(os.path.expanduser("~"))
            disk_total_gb = round(disk.total / (1024 ** 3), 1)
            disk_free_gb = round(disk.free / (1024 ** 3), 1)
            disk_pct = round((disk.used / disk.total) * 100.0, 1)

            # Battery (macOS laptop support)
            battery_pct = None
            power_plugged = None
            if hasattr(psutil, "sensors_battery"):
                batt = psutil.sensors_battery()
                if batt:
                    battery_pct = round(batt.percent, 1)
                    power_plugged = batt.power_plugged

            hw_data = {
                "cpu_percent": cpu_pct,
                "cpu_count": cpu_count,
                "memory": {
                    "used_mb": used_mb,
                    "total_mb": total_mb,
                    "percent": mem_pct,
                    "free_gb": free_gb,
                    "pressure": pressure
                },
                "disk": {
                    "total_gb": disk_total_gb,
                    "free_gb": disk_free_gb,
                    "percent": disk_pct
                },
                "battery": {
                    "percent": battery_pct,
                    "plugged": power_plugged
                }
            }

            self.cpu_window.add(cpu_pct)
            self.memory_window.add(mem_pct)
            self._cached_hw = hw_data
            self._last_hw_sample = now
            return hw_data

        except Exception as e:
            logger.error("Error sampling hardware telemetry: %s", e)
            return {
                "cpu_percent": 0.0,
                "cpu_count": 8,
                "memory": {"used_mb": 0.0, "total_mb": 0.0, "percent": 0.0, "free_gb": 0.0, "pressure": "unknown"},
                "disk": {"total_gb": 0.0, "free_gb": 0.0, "percent": 0.0},
                "battery": {"percent": None, "plugged": None}
            }

    def get_snapshot(self, container: Optional[Any] = None) -> Dict[str, Any]:
        """
        Produce a complete, JSON-serializable snapshot of all system vitals and agent telemetry.
        """
        hw = self.sample_hardware()
        now_iso = datetime.utcnow().isoformat() + "Z"
        uptime_sec = round(time.time() - self._start_time, 1)

        with self._state_lock:
            # Latency stats
            lat_stats = self.latency_window.stats()

            # Tool metrics
            tool_data = {t: stats.to_dict() for t, stats in self._tool_stats.items()}

            # Task counters
            total_tasks = self._completed_tasks + self._failed_tasks
            success_rate = round((self._completed_tasks / max(1, total_tasks)) * 100.0, 1)
            task_data = {
                "active": self._active_tasks,
                "completed": self._completed_tasks,
                "failed": self._failed_tasks,
                "total": total_tasks,
                "success_rate_pct": success_rate
            }

            # Tokens
            total_tokens = self._prompt_tokens + self._completion_tokens
            tokens_per_sec = round(total_tokens / max(1.0, uptime_sec), 2)
            token_data = {
                "total_tokens": total_tokens,
                "prompt_tokens": self._prompt_tokens,
                "completion_tokens": self._completion_tokens,
                "total_queries": self._model_queries,
                "tokens_per_sec": tokens_per_sec,
                "provider_queries": dict(self._provider_queries)
            }

            # Security Kernel state
            sec_data = {
                "kill_switch_engaged": False,
                "trust_level": "LOCAL_IMMUTABLE_ADMIN",
                "audit_chain_valid": True
            }
            if container:
                if hasattr(container, "kill_switch"):
                    ks = container.kill_switch
                    ks_active = ks.is_active() if callable(getattr(ks, "is_active", None)) else getattr(ks, "is_active", False)
                    sec_data["kill_switch_engaged"] = bool(ks_active)
                if hasattr(container, "audit"):
                    try:
                        valid, count, _ = container.audit.verify_chain()
                        sec_data["audit_chain_valid"] = valid
                        sec_data["audit_records_count"] = count
                    except Exception:
                        pass

            # Time Series history (recent samples)
            cpu_series = self.cpu_window.get_series()
            mem_series = self.memory_window.get_series()
            lat_series = self.latency_window.get_series()

        return {
            "timestamp": now_iso,
            "uptime_seconds": uptime_sec,
            "hardware": hw,
            "latency": lat_stats,
            "tokens": token_data,
            "tools": tool_data,
            "tasks": task_data,
            "security": sec_data,
            "time_series": {
                "cpu": cpu_series,
                "memory": mem_series,
                "latency": lat_series
            }
        }

    def stream_events(self, interval_sec: float = 1.0, container: Optional[Any] = None) -> Generator[str, None, None]:
        """
        Generate Server-Sent Events (SSE) stream payloads for real-time HUD dashboards.
        Format: data: <json>\n\n
        """
        while True:
            snapshot = self.get_snapshot(container=container)
            payload = f"data: {json.dumps(snapshot)}\n\n"
            yield payload
            time.sleep(interval_sec)

    def reset_metrics(self):
        """Reset operational counters for testing and new sessions."""
        with self._state_lock:
            self._tool_stats.clear()
            self._active_tasks = 0
            self._completed_tasks = 0
            self._failed_tasks = 0
            self._prompt_tokens = 0
            self._completion_tokens = 0
            self._model_queries = 0
            self._provider_queries.clear()
            self._start_time = time.time()
            self.latency_window = RollingWindow(maxlen=self.history_len)
            self.cpu_window = RollingWindow(maxlen=self.history_len)
            self.memory_window = RollingWindow(maxlen=self.history_len)


# Global singleton
telemetry_engine = TelemetryEngine()
