"""
J.A.R.V.I.S. macOS Calendar Integration Tool
Provides native event creation, today's schedule retrieval, and upcoming agenda viewing via AppleScript.
"""
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskTier
from security.action_validator import sanitize_applescript_string

logger = logging.getLogger("jarvis.integrations.calendar")


class CalendarTool(BaseTool):
    @property
    def id(self) -> str:
        return "calendar"

    @property
    def name(self) -> str:
        return "macOS Calendar"

    @property
    def description(self) -> str:
        return "Manage macOS Calendar: create new calendar events, retrieve today's scheduled agenda, or view upcoming events."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "today", "upcoming"],
                    "description": "Calendar action: 'create' (add event), 'today' (today's agenda), or 'upcoming' (next N days)."
                },
                "title": {
                    "type": "string",
                    "description": "Event title or summary (for action='create')."
                },
                "start_time": {
                    "type": "string",
                    "description": "Event start time (e.g. '2026-09-07 10:00' or '10:00 AM')."
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Event duration in minutes (default: 60)."
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days ahead to search (for action='upcoming', default: 3)."
                }
            },
            "required": ["action"]
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.APP_CONTROL

    @property
    def risk_tier(self) -> RiskTier:
        return RiskTier.MODERATE

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        action = params.get("action", "today").lower().strip()

        try:
            if action == "create":
                raw_title = params.get("title", "New Event").strip()
                title = sanitize_applescript_string(raw_title)
                start_str = params.get("start_time", "").strip()
                dur = max(15, int(params.get("duration_minutes", 60)))

                # Parse start time or default to 1 hour from now
                now = datetime.now()
                start_dt = now + timedelta(hours=1)
                if start_str:
                    try:
                        start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
                    except ValueError:
                        try:
                            # Try parsing as HH:MM today
                            t = datetime.strptime(start_str, "%H:%M").time()
                            start_dt = datetime.combine(now.date(), t)
                        except Exception:
                            pass

                end_dt = start_dt + timedelta(minutes=dur)
                as_start = start_dt.strftime("%m/%d/%Y %I:%M:%S %p")
                as_end = end_dt.strftime("%m/%d/%Y %I:%M:%S %p")

                script = f'''
                tell application "Calendar"
                    tell (first calendar whose read only is false)
                        make new event with properties {{summary:"{title}", start date:date "{as_start}", end date:date "{as_end}"}}
                    end tell
                end tell
                '''
                subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=True)
                return ToolResult(
                    success=True,
                    data=f"Created Calendar event: '{raw_title}' on {start_dt.strftime('%A, %b %d at %I:%M %p')}."
                )

            elif action in ("today", "upcoming"):
                days = 1 if action == "today" else max(1, min(14, int(params.get("days", 3))))
                script = f'''
                set out to ""
                set now_dt to current date
                set end_dt to now_dt + ({days} * days)
                tell application "Calendar"
                    repeat with cal in calendars
                        try
                            set evList to (every event of cal whose start date ≥ now_dt and start date ≤ end_dt)
                            repeat with ev in evList
                                set s_date to start date of ev as string
                                set ev_title to summary of ev
                                set out to out & "• " & ev_title & " (" & s_date & ")" & linefeed
                            end repeat
                        end try
                    end repeat
                end tell
                return out
                '''
                res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
                events_text = res.stdout.strip()
                label = "Today's Agenda" if action == "today" else f"Upcoming Events (Next {days} Days)"
                if not events_text:
                    return ToolResult(success=True, data=f"🗓️ {label}: No events scheduled.")
                return ToolResult(success=True, data=f"🗓️ {label}:\n{events_text}")

            else:
                return ToolResult(success=False, error=f"Unknown calendar action: '{action}'")

        except Exception as e:
            logger.error(f"Calendar error: {e}")
            return ToolResult(success=False, error=f"Calendar action failed: {str(e)}")
