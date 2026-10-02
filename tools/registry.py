"""
J.A.R.V.I.S. Secure Tool Registry
Registers, describes, and safely executes tools under deterministic security policy.
"""
from typing import Dict, List, Any, Optional
import logging
from .base import BaseTool, ToolResult
from security import security_kernel, TrustLevel, audit_chain
from core.events import event_bus, Event, EventType

logger = logging.getLogger("jarvis.tools")

class ToolRegistry:
    _instance = None

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """Register a new tool instance and synchronize with security policy manifest."""
        self._tools[tool.id] = tool
        try:
            from security.capabilities import TOOL_MANIFEST, ToolManifestEntry, OWNER_ONLY
            if tool.id not in TOOL_MANIFEST:
                TOOL_MANIFEST[tool.id] = ToolManifestEntry(
                    tool_name=tool.id,
                    capability=tool.required_capability,
                    risk_level=tool.risk_tier,
                    allowed_trust_levels=OWNER_ONLY,
                    requires_confirmation=False,
                    description=tool.description
                )
        except Exception:
            pass
        logger.info(f"Registered tool: {tool.id} [{tool.risk_tier.name}]")

    def get_tool(self, tool_id: str) -> Optional[BaseTool]:
        return self._tools.get(tool_id)

    def has_tool(self, tool_id: str) -> bool:
        return tool_id in self._tools

    def list_tools(self) -> List[BaseTool]:

        return list(self._tools.values())

    def export_schemas(self) -> List[Dict[str, Any]]:
        """Export tool definitions in OpenAI/Gemini function-calling format."""
        schemas = []
        for tool in self._tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.id,
                    "description": tool.description,
                    "parameters": tool.parameters_schema
                }
            })
        return schemas

    def execute_tool(
        self,
        tool_id: str,
        params: Dict[str, Any],
        trust_level: TrustLevel = TrustLevel.LOCAL_OWNER
    ) -> ToolResult:
        """Execute tool through the deterministic security kernel."""
        tool = self.get_tool(tool_id)
        if not tool:
            return ToolResult(success=False, error=f"Unknown tool: '{tool_id}'")

        # 1. Deterministic Security Kernel Policy Check
        auth = security_kernel.authorize_action(tool_id, params, trust_level=trust_level)
        if not auth.allowed:
            audit_chain.log_event(
                event_type="TOOL_EXECUTION_BLOCKED",
                action=tool_id,
                result="DENIED",
                trust_level=trust_level.value,
                risk_level=tool.risk_tier.name,
                details={"reason": auth.reason, "params": params}
            )
            return ToolResult(success=False, error=f"Security Policy Restriction: {auth.reason}")

        # 2. Bounded Execution
        event_bus.publish(Event(
            event_type=EventType.TOOL_REQUESTED,
            source="ToolRegistry",
            payload={"tool_id": tool_id, "params": params}
        ))

        try:
            result = tool.execute(params)
            
            # 3. Tamper-evident audit log
            audit_chain.log_event(
                event_type="TOOL_EXECUTED",
                action=tool_id,
                result="SUCCESS" if result.success else "FAILED",
                trust_level=trust_level.value,
                risk_level=tool.risk_tier.name,
                details={"params": params, "error": result.error}
            )

            event_bus.publish(Event(
                event_type=EventType.TOOL_EXECUTED,
                source="ToolRegistry",
                payload={"tool_id": tool_id, "success": result.success}
            ))
            return result

        except Exception as e:
            logger.error(f"Error executing tool {tool_id}: {e}")
            audit_chain.log_event(
                event_type="TOOL_EXECUTION_EXCEPTION",
                action=tool_id,
                result="ERROR",
                trust_level=trust_level.value,
                risk_level=tool.risk_tier.name,
                details={"exception": str(e)}
            )
            return ToolResult(success=False, error=f"Execution error: {str(e)}")

tool_registry = ToolRegistry()
