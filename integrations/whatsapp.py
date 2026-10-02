"""
J.A.R.V.I.S. WhatsApp Automation Integration Tool
Provides safe, structured interface to WhatsApp macOS desktop client and WhatsAppAgent.
"""
from typing import Dict, Any, Optional
from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskLevel
from whatsapp_controller.tools import WhatsAppTools


class WhatsAppTool(BaseTool):
    def __init__(self):
        self._wa_tools = None
        self._agent = None

    def _get_wa(self) -> WhatsAppTools:
        if self._wa_tools is None:
            self._wa_tools = WhatsAppTools()
        return self._wa_tools

    def _get_agent(self):
        if self._agent is None:
            from agents.whatsapp import whatsapp_agent
            self._agent = whatsapp_agent
        return self._agent

    @property
    def id(self) -> str:
        return "whatsapp_automation"

    @property
    def name(self) -> str:
        return "WhatsApp Desktop Automation"

    @property
    def description(self) -> str:
        return (
            "Control WhatsApp macOS client and agent. "
            "Supports actions: 'send_message', 'read_chat', 'call', 'send_media', "
            "'summarize', 'get_activity', and 'health_check'."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["send_message", "read_chat", "call", "send_media", "summarize", "get_activity", "health_check"],
                    "description": "WhatsApp action to perform."
                },
                "contact": {
                    "type": "string",
                    "description": "Target contact name or phone number."
                },
                "message": {
                    "type": "string",
                    "description": "Text message to send."
                },
                "file_path": {
                    "type": "string",
                    "description": "Path to media attachment."
                },
                "caption": {
                    "type": "string",
                    "description": "Optional caption for media attachment."
                },
                "video": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to initiate a video call (defaults to audio)."
                },
                "max_messages": {
                    "type": "integer",
                    "default": 10,
                    "description": "Number of recent chat messages to read."
                }
            },
            "required": ["action"]
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.WHATSAPP_AUTOMATION

    @property
    def risk_tier(self) -> RiskLevel:
        return RiskLevel.HIGH

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        action = params.get("action", "").lower().strip()
        contact = params.get("contact", "").strip()

        # Check contact requirement for actions that need it
        if action in ("send_message", "read_chat", "call", "send_media") and not contact:
            return ToolResult(success=False, error=f"Parameter 'contact' is required for action '{action}'.")

        try:
            wa = self._get_wa()

            if action == "send_message":
                msg = params.get("message", "").strip()
                if not msg:
                    return ToolResult(success=False, error="Parameter 'message' cannot be empty for send_message.")
                res = wa.send_message(contact, msg)
                return ToolResult(
                    success=res.get("success", False),
                    data=res,
                    error=res.get("error") or res.get("details")
                )

            elif action == "read_chat":
                max_msgs = int(params.get("max_messages", 10))
                res = wa.read_chat(contact, max_messages=max_msgs)
                return ToolResult(
                    success=res.get("success", False),
                    data=res,
                    error=res.get("error") or res.get("details")
                )

            elif action == "call":
                video = bool(params.get("video", False))
                res = wa.initiate_call(contact, video=video)
                return ToolResult(
                    success=res.get("success", False),
                    data=res,
                    error=res.get("error") or res.get("details")
                )

            elif action == "send_media":
                file_path = params.get("file_path", "").strip()
                caption = params.get("caption", "").strip()
                if not file_path:
                    return ToolResult(success=False, error="Parameter 'file_path' is required for send_media.")
                res = wa.send_media(contact, file_path, caption=caption)
                return ToolResult(
                    success=res.get("success", False),
                    data=res,
                    error=res.get("error") or res.get("details")
                )

            elif action == "summarize":
                agent = self._get_agent()
                if contact:
                    summary = agent.summarize_conversation(contact)
                else:
                    summary = agent.summarize_recent_activity()
                return ToolResult(success=True, data={"summary": summary})

            elif action == "get_activity":
                agent = self._get_agent()
                act = agent.get_recent_activity()
                return ToolResult(success=True, data=act.to_dict())

            elif action == "health_check":
                agent = self._get_agent()
                hc = agent.health_check()
                return ToolResult(success=hc.get("healthy", False), data=hc)

            else:
                return ToolResult(success=False, error=f"Unknown WhatsApp action: '{action}'")

        except Exception as e:
            return ToolResult(success=False, error=f"WhatsApp operation failed: {e}")
