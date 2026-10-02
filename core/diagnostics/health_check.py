"""
J.A.R.V.I.S. System Health & Diagnostic Monitor
Real-time integrity auditing across Unified Memory, Storage, Security Kernel, and Model Engines.
"""
import os
import shutil
import psutil
import logging
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

logger = logging.getLogger("jarvis.diagnostics.health")

class SubsystemStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

@dataclass
class HealthReport:
    overall_status: SubsystemStatus
    subsystems: Dict[str, Dict[str, Any]]
    memory_usage_pct: float
    free_ram_gb: float
    disk_free_gb: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    alerts: List[str] = field(default_factory=list)

    def is_operational(self) -> bool:
        return self.overall_status in (SubsystemStatus.HEALTHY, SubsystemStatus.DEGRADED)


class SystemHealthCheck:
    """
    Evaluates hardware metrics, runtime integrity, and subsystem readiness.
    """
    @staticmethod
    def inspect(container: Optional[Any] = None) -> HealthReport:
        subsystems: Dict[str, Dict[str, Any]] = {}
        alerts: List[str] = []
        overall = SubsystemStatus.HEALTHY

        # 1. Host Memory (Apple Silicon Unified RAM)
        vmem = psutil.virtual_memory()
        mem_pct = vmem.percent
        free_ram_gb = vmem.available / (1024 ** 3)
        if mem_pct > 90:
            overall = SubsystemStatus.CRITICAL
            alerts.append(f"Critical memory pressure: {mem_pct}% used")
            subsystems["memory"] = {"status": SubsystemStatus.CRITICAL, "percent": mem_pct, "free_gb": round(free_ram_gb, 2)}
        elif mem_pct > 80:
            if overall == SubsystemStatus.HEALTHY: overall = SubsystemStatus.DEGRADED
            alerts.append(f"High memory pressure: {mem_pct}% used")
            subsystems["memory"] = {"status": SubsystemStatus.DEGRADED, "percent": mem_pct, "free_gb": round(free_ram_gb, 2)}
        else:
            subsystems["memory"] = {"status": SubsystemStatus.HEALTHY, "percent": mem_pct, "free_gb": round(free_ram_gb, 2)}

        # 2. Disk Space
        usage = shutil.disk_usage(os.path.expanduser("~"))
        free_disk_gb = usage.free / (1024 ** 3)
        if free_disk_gb < 5.0:
            overall = SubsystemStatus.CRITICAL
            alerts.append(f"Extremely low disk space: {round(free_disk_gb, 2)} GB remaining")
            subsystems["disk"] = {"status": SubsystemStatus.CRITICAL, "free_gb": round(free_disk_gb, 2)}
        elif free_disk_gb < 15.0:
            if overall == SubsystemStatus.HEALTHY: overall = SubsystemStatus.DEGRADED
            alerts.append(f"Low disk space: {round(free_disk_gb, 2)} GB remaining")
            subsystems["disk"] = {"status": SubsystemStatus.DEGRADED, "free_gb": round(free_disk_gb, 2)}
        else:
            subsystems["disk"] = {"status": SubsystemStatus.HEALTHY, "free_gb": round(free_disk_gb, 2)}

        # 3. Security Kernel Integrity
        if container and hasattr(container, "kill_switch"):
            ks = container.kill_switch
            ks_active = ks.is_active() if callable(getattr(ks, "is_active", None)) else getattr(ks, "is_active", False)
            if ks_active:
                overall = SubsystemStatus.CRITICAL
                alerts.append("Emergency Kill Switch is ACTIVE: all tool execution is halted.")
                subsystems["security"] = {"status": SubsystemStatus.CRITICAL, "kill_switch": "ACTIVE"}
            else:
                subsystems["security"] = {"status": SubsystemStatus.HEALTHY, "kill_switch": "NORMAL"}
        else:
            subsystems["security"] = {"status": SubsystemStatus.HEALTHY, "kill_switch": "STANDBY"}

        # 4. Intelligence Providers & Router
        if container and hasattr(container, "router"):
            local_ok = container.router.providers.get("local_gemma", None) is not None
            subsystems["intelligence"] = {
                "status": SubsystemStatus.HEALTHY if local_ok else SubsystemStatus.DEGRADED,
                "local_gemma": "READY" if local_ok else "NOT_LOADED",
                "active_providers": list(container.router.providers.keys())
            }
        else:
            subsystems["intelligence"] = {"status": SubsystemStatus.UNKNOWN}

        # 5. Tool Framework
        if container and hasattr(container, "tools"):
            tool_count = len(container.tools.list_tools())
            subsystems["tools"] = {
                "status": SubsystemStatus.HEALTHY if tool_count >= 5 else SubsystemStatus.DEGRADED,
                "registered_count": tool_count
            }
        else:
            subsystems["tools"] = {"status": SubsystemStatus.UNKNOWN}

        # 6. Memory Subsystems
        if container and hasattr(container, "semantic_memory"):
            subsystems["memory_stores"] = {
                "status": SubsystemStatus.HEALTHY,
                "semantic_facts": container.semantic_memory.count(),
                "episodes": container.episodic_memory.count() if hasattr(container, "episodic_memory") else 0,
                "procedures": len(container.procedural_memory.list_procedures()) if hasattr(container, "procedural_memory") else 0
            }
        else:
            subsystems["memory_stores"] = {"status": SubsystemStatus.UNKNOWN}

        return HealthReport(
            overall_status=overall,
            subsystems=subsystems,
            memory_usage_pct=mem_pct,
            free_ram_gb=round(free_ram_gb, 2),
            disk_free_gb=round(free_disk_gb, 2),
            alerts=alerts
        )
