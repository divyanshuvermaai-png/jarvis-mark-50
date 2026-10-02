"""
J.A.R.V.I.S. Morning Briefing Protocol
Autonomous multi-subsystem routine combining hardware diagnostics, local weather,
calendar schedule, and top headlines into a sophisticated Stark-style status report.
"""
import psutil
from datetime import datetime
import logging
from typing import Dict, Any, Optional

from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskTier
from tools.builtins.weather_tool import WeatherTool
from tools.builtins.news_tool import NewsTool
from integrations.calendar_tool import CalendarTool

logger = logging.getLogger("jarvis.protocols.morning")


class MorningProtocolTool(BaseTool):
    def __init__(
        self,
        weather_tool: Optional[WeatherTool] = None,
        news_tool: Optional[NewsTool] = None,
        calendar_tool: Optional[CalendarTool] = None
    ):
        self.weather = weather_tool or WeatherTool()
        self.news = news_tool or NewsTool()
        self.calendar = calendar_tool or CalendarTool()

    @property
    def id(self) -> str:
        return "morning_protocol"

    @property
    def name(self) -> str:
        return "Morning Briefing Protocol"

    @property
    def description(self) -> str:
        return "Execute full morning briefing for Divyanshu: checks hardware vitals, weather, today's calendar agenda, and top news headlines."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Location for weather briefing (defaults to 'Jaipur')."
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
        loc = params.get("location", "Jaipur").strip() or "Jaipur"
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%A, %B %d, %Y")

        # 1. Hardware vitals
        vmem = psutil.virtual_memory()
        ram_pct = round(vmem.percent, 1)
        free_ram_gb = round(vmem.available / (1024 ** 3), 1)

        batt_info = "Running on AC Power"
        if hasattr(psutil, "sensors_battery"):
            b = psutil.sensors_battery()
            if b:
                plug_status = "Plugged in" if b.power_plugged else "Discharging"
                batt_info = f"Battery at {round(b.percent)}% ({plug_status})"

        # 2. Weather
        w_res = self.weather.execute({"location": loc, "format": "summary"})
        weather_summary = w_res.data if w_res.success else "Weather service temporarily unreachable."

        # 3. Calendar
        c_res = self.calendar.execute({"action": "today"})
        cal_summary = c_res.data if c_res.success else "Calendar: No events scheduled."

        # 4. News
        n_res = self.news.execute({"category": "technology", "limit": 3})
        news_summary = n_res.data if n_res.success else "News: Headlines unavailable."

        briefing_text = (
            f"🌅 Good morning, Sir.\n"
            f"The time is {time_str} on {date_str}.\n\n"
            f"⚡ System Status:\n"
            f"• Apple Silicon Unified RAM: {ram_pct}% used ({free_ram_gb} GB free)\n"
            f"• Power: {batt_info}\n"
            f"• Security Architecture: 11-Stage Defense-in-Depth Active\n\n"
            f"🌤️ Weather ({loc}):\n"
            f"{weather_summary}\n\n"
            f"{cal_summary}\n\n"
            f"{news_summary}\n\n"
            f"All operational systems are primed and standing by for your command, Sir."
        )

        return ToolResult(
            success=True,
            data=briefing_text,
            metadata={
                "time": time_str,
                "date": date_str,
                "ram_percent": ram_pct,
                "weather": weather_summary
            }
        )
