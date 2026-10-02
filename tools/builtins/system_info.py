"""
System Telemetry & Diagnostics Tool
"""
from typing import Dict, Any
import platform
import psutil
from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskTier

class SystemInfoTool(BaseTool):
    @property
    def id(self) -> str:
        return "system_info"

    @property
    def name(self) -> str:
        return "System Info & Telemetry"

    @property
    def description(self) -> str:
        return "Retrieve real-time hardware status, CPU/RAM utilization, and macOS platform metrics."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": ["all", "cpu", "memory", "platform", "battery"],
                    "default": "all",
                    "description": "Specific subsystem metric to inspect"
                }
            }
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.SYSTEM_INFO_READ

    @property
    def risk_tier(self) -> RiskTier:
        return RiskTier.LOW

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        metric = params.get("metric", "all")
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.1)
        
        data = {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cpu_percent": cpu,
            "ram_total_gb": round(mem.total / (1024**3), 1),
            "ram_used_gb": round(mem.used / (1024**3), 1),
            "ram_percent": mem.percent
        }
        
        battery = psutil.sensors_battery()
        if battery:
            data["battery_percent"] = battery.percent
            data["power_plugged"] = battery.power_plugged

        if metric == "all":
            return ToolResult(success=True, data=data)
        elif metric in data:
            return ToolResult(success=True, data={metric: data[metric]})
        return ToolResult(success=True, data=data)
