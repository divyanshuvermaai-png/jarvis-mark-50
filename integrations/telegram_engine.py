"""
J.A.R.V.I.S. Telegram Bot Integration Engine
Provides remote alerting, notification dispatch, and message polling via Telegram Bot API.
"""
import os
import requests
import logging
from typing import Dict, Any, Optional

from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskTier

logger = logging.getLogger("jarvis.integrations.telegram")


class TelegramTool(BaseTool):
    @property
    def id(self) -> str:
        return "telegram"

    @property
    def name(self) -> str:
        return "Telegram Bot"

    @property
    def description(self) -> str:
        return "Send alerts or messages to Telegram, or retrieve recent messages received by the bot."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["send", "receive", "status"],
                    "description": "Action: 'send' (dispatch message), 'receive' (poll recent updates), or 'status'."
                },
                "message": {
                    "type": "string",
                    "description": "Message text to deliver (for action='send')."
                },
                "chat_id": {
                    "type": "string",
                    "description": "Target Telegram Chat ID (defaults to TELEGRAM_CHAT_ID in environment)."
                }
            },
            "required": ["action"]
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.APP_CONTROL

    @property
    def risk_tier(self) -> RiskTier:
        return RiskTier.SENSITIVE

    def _get_credentials(self) -> tuple[Optional[str], Optional[str]]:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        return token, chat_id

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        action = params.get("action", "send").lower().strip()
        token, default_chat_id = self._get_credentials()

        if not token:
            return ToolResult(
                success=False,
                error="Telegram bot token not configured. Please set TELEGRAM_BOT_TOKEN in environment."
            )

        base_url = f"https://api.telegram.org/bot{token}"

        try:
            if action == "send":
                text = params.get("message", "").strip()
                chat_id = params.get("chat_id") or default_chat_id
                if not chat_id:
                    return ToolResult(success=False, error="Target chat_id is required (or set TELEGRAM_CHAT_ID).")
                if not text:
                    return ToolResult(success=False, error="Message text cannot be empty.")

                resp = requests.post(
                    f"{base_url}/sendMessage",
                    json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                    timeout=8
                )
                if resp.status_code == 200:
                    return ToolResult(success=True, data=f"Telegram message sent to chat {chat_id}.")
                return ToolResult(success=False, error=f"Telegram API returned HTTP {resp.status_code}: {resp.text}")

            elif action == "receive":
                resp = requests.get(f"{base_url}/getUpdates", timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    updates = data.get("result", [])[-5:]
                    if not updates:
                        return ToolResult(success=True, data="No recent Telegram messages.")
                    lines = ["📩 Recent Telegram Messages:"]
                    for u in updates:
                        msg = u.get("message", {})
                        sender = msg.get("from", {}).get("first_name", "Unknown")
                        t = msg.get("text", "(media)")
                        lines.append(f"• {sender}: {t}")
                    return ToolResult(success=True, data="\n".join(lines))
                return ToolResult(success=False, error=f"Telegram getUpdates failed: {resp.text}")

            elif action == "status":
                resp = requests.get(f"{base_url}/getMe", timeout=6)
                if resp.status_code == 200:
                    bot_data = resp.json().get("result", {})
                    name = bot_data.get("first_name", "JARVIS Bot")
                    username = bot_data.get("username", "")
                    return ToolResult(
                        success=True,
                        data=f"Telegram Bot online: @{username} ({name}).",
                        metadata=bot_data
                    )
                return ToolResult(success=False, error="Failed to connect to Telegram Bot.")

            else:
                return ToolResult(success=False, error=f"Unknown Telegram action: '{action}'")

        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return ToolResult(success=False, error=f"Telegram connection error: {str(e)}")
