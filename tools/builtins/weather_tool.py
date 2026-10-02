"""
J.A.R.V.I.S. Live Weather Tool
Provides real-time atmospheric vitals and multi-day forecasts via wttr.in.
Zero external API key required.
"""
import urllib.parse
import requests
import logging
from typing import Dict, Any, Optional

from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskTier

logger = logging.getLogger("jarvis.tools.weather")


class WeatherTool(BaseTool):
    @property
    def id(self) -> str:
        return "weather"

    @property
    def name(self) -> str:
        return "Weather & Forecast"

    @property
    def description(self) -> str:
        return "Fetch current weather conditions, temperature, humidity, wind, and forecast for any city or location."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City or location name (e.g. 'Jaipur', 'London', 'New York'). Defaults to Jaipur if omitted."
                },
                "format": {
                    "type": "string",
                    "enum": ["summary", "detailed", "full"],
                    "description": "Output format: 'summary' (one-line), 'detailed' (conditions + stats), or 'full'."
                }
            }
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.STATUS

    @property
    def risk_tier(self) -> RiskTier:
        return RiskTier.LOW

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        location = params.get("location", "Jaipur").strip() or "Jaipur"
        fmt = params.get("format", "detailed")

        encoded_loc = urllib.parse.quote(location)
        url = f"https://wttr.in/{encoded_loc}?format=j1"

        try:
            resp = requests.get(url, timeout=8, headers={"User-Agent": "curl/7.68.0"})
            if resp.status_code != 200:
                # Fallback to plain text format
                fallback_resp = requests.get(f"https://wttr.in/{encoded_loc}?format=3", timeout=6)
                if fallback_resp.status_code == 200:
                    return ToolResult(success=True, data=fallback_resp.text.strip())
                return ToolResult(success=False, error=f"Weather service returned HTTP {resp.status_code}")

            data = resp.json()
            curr = data.get("current_condition", [{}])[0]
            temp_c = curr.get("temp_C", "?")
            feels_c = curr.get("FeelsLikeC", "?")
            desc = curr.get("weatherDesc", [{}])[0].get("value", "Clear")
            humidity = curr.get("humidity", "?")
            wind_kmh = curr.get("windspeedKmph", "?")

            today = data.get("weather", [{}])[0]
            max_c = today.get("maxtempC", "?")
            min_c = today.get("mintempC", "?")
            astronomy = today.get("astronomy", [{}])[0]
            sunrise = astronomy.get("sunrise", "?")
            sunset = astronomy.get("sunset", "?")

            if fmt == "summary":
                summary = f"{location}: {desc}, {temp_c}°C (Feels like {feels_c}°C)"
                return ToolResult(success=True, data=summary, metadata={"temp_c": temp_c, "desc": desc})

            detailed = (
                f"🌤️ Weather for {location}:\n"
                f"• Condition:   {desc}\n"
                f"• Temperature: {temp_c}°C (Feels like: {feels_c}°C)\n"
                f"• Range Today: Min {min_c}°C / Max {max_c}°C\n"
                f"• Humidity:    {humidity}%\n"
                f"• Wind Speed:  {wind_kmh} km/h\n"
                f"• Daylight:    Sunrise {sunrise} · Sunset {sunset}"
            )

            return ToolResult(
                success=True,
                data=detailed,
                metadata={
                    "location": location,
                    "temp_c": temp_c,
                    "feels_like_c": feels_c,
                    "condition": desc,
                    "humidity": humidity,
                    "wind_kmh": wind_kmh
                }
            )

        except Exception as e:
            logger.warning(f"Weather fetch error for {location}: {e}")
            # Try quick one-line fallback
            try:
                fb = requests.get(f"https://wttr.in/{encoded_loc}?format=3", timeout=5)
                if fb.status_code == 200:
                    return ToolResult(success=True, data=fb.text.strip())
            except Exception:
                pass
            return ToolResult(success=False, error=f"Could not retrieve weather for '{location}': {str(e)}")
