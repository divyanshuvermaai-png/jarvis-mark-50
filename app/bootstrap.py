"""
J.A.R.V.I.S. Dependency Injection & System Bootstrap
Assembles the complete production agent operating system.
"""
from dataclasses import dataclass
from typing import Optional, Any
import logging

from app.config import JarvisConfig, get_config
from core.events import event_bus, Event, EventType
from intelligence.router import ModelRouter
from tools.registry import ToolRegistry, tool_registry
from tools.builtins import (
    SystemInfoTool,
    FileOpsTool,
    WebSearchTool,
    WeatherTool,
    NewsTool,
    FinanceTool,
    SystemControlTool,
    DataAnalyticsTool,
    BiometricTool
)
from tools.macos import MacOSWindowTool, MacOSKeyboardTool, MacOSMouseTool, MacOSVisionTool
from integrations import (
    AppleSuiteTool,
    WhatsAppTool,
    GmailTool,
    TelegramTool,
    CalendarTool,
    InstagramTool,
    YouTubeUploaderTool
)
from core.protocols import MorningProtocolTool
from core.scheduler import TaskScheduler
from memory.short_term import ShortTermMemory
from memory.preferences import PreferenceStore
from memory.semantic import SemanticMemory
from memory.episodic import EpisodicMemory
from memory.procedural import ProceduralMemory
from intelligence.context import ContextEngine
from core.orchestration import AgentOrchestrator
from agents.computer import ComputerAgent
from voice import TextToSpeechEngine, SpeechToTextEngine, VoiceInterface
from core.diagnostics import SystemHealthCheck, RecoveryManager, SandboxedToolVerifier
from interfaces.telemetry import TelemetryEngine, telemetry_engine
from security import (
    security_kernel,
    kill_switch,
    audit_chain,
    TrustLevel
)

logger = logging.getLogger("jarvis.bootstrap")

@dataclass
class BootstrapContainer:
    config: JarvisConfig
    router: ModelRouter
    tools: ToolRegistry
    memory: ShortTermMemory
    preferences: PreferenceStore
    semantic_memory: SemanticMemory
    episodic_memory: EpisodicMemory
    procedural_memory: ProceduralMemory
    context_engine: ContextEngine
    orchestrator: AgentOrchestrator
    computer_agent: ComputerAgent
    scheduler: TaskScheduler
    tts: TextToSpeechEngine
    stt: SpeechToTextEngine
    voice: VoiceInterface
    diagnostics: SystemHealthCheck
    recovery: RecoveryManager
    telemetry: Any = None
    security: Any = security_kernel
    kill_switch: Any = kill_switch
    audit: Any = audit_chain






_global_container: Optional[BootstrapContainer] = None

def bootstrap_jarvis(config: Optional[JarvisConfig] = None) -> BootstrapContainer:
    """Initialize and wire all core J.A.R.V.I.S. operating system components."""
    global _global_container
    if _global_container is not None:
        return _global_container

    cfg = config or get_config()

    # 1. Setup Logging & Events
    event_bus.publish(Event(
        event_type=EventType.SYSTEM_STARTUP,
        source="Bootstrap",
        payload={"system": cfg.system_name, "version": cfg.version}
    ))

    # 2. Tool Registry & Builtins (Core + Native macOS)
    registry = tool_registry
    if not registry.get_tool("system_info"):
        registry.register(SystemInfoTool())
    if not registry.get_tool("file_ops"):
        registry.register(FileOpsTool())
    if not registry.get_tool("web_search"):
        registry.register(WebSearchTool())
    if not registry.get_tool("macos_window"):
        registry.register(MacOSWindowTool())
    if not registry.get_tool("macos_keyboard"):
        registry.register(MacOSKeyboardTool())
    if not registry.get_tool("macos_mouse"):
        registry.register(MacOSMouseTool())
    if not registry.get_tool("macos_vision"):
        registry.register(MacOSVisionTool())
    if not registry.get_tool("apple_suite"):
        registry.register(AppleSuiteTool())
    if not registry.get_tool("whatsapp_automation"):
        registry.register(WhatsAppTool())
    if not registry.get_tool("instagram_automation"):
        registry.register(InstagramTool())
    if not registry.get_tool("youtube_uploader"):
        registry.register(YouTubeUploaderTool())
    if not registry.get_tool("weather"):
        registry.register(WeatherTool())
    if not registry.get_tool("news"):
        registry.register(NewsTool())
    if not registry.get_tool("finance"):
        registry.register(FinanceTool())
    if not registry.get_tool("system_control"):
        registry.register(SystemControlTool())
    if not registry.get_tool("data_analytics"):
        registry.register(DataAnalyticsTool())
    if not registry.get_tool("gmail"):
        registry.register(GmailTool())
    if not registry.get_tool("telegram"):
        registry.register(TelegramTool())
    if not registry.get_tool("calendar"):
        registry.register(CalendarTool())
    if not registry.get_tool("morning_protocol"):
        registry.register(MorningProtocolTool())
    if not registry.get_tool("biometrics"):
        registry.register(BiometricTool())

    # 3. Model Router
    router = ModelRouter(config=cfg)

    # 4. Multi-Tier Memory Stores
    memory = ShortTermMemory(max_turns=12)
    preferences = PreferenceStore(storage_path=cfg.config_dir / "preferences.json")
    semantic = SemanticMemory(db_path=cfg.config_dir / "semantic_memory.db")
    episodic = EpisodicMemory(db_path=cfg.config_dir / "episodic_memory.db")
    procedural = ProceduralMemory(db_path=cfg.config_dir / "procedural_memory.db")

    # Seed macOS & Integration procedures
    procedural.register_procedure(
        name="Capture Desktop Screen",
        description="Take a high-resolution screenshot of the macOS display",
        trigger_patterns=["take a screenshot", "capture screen", "screenshot"],
        steps=[{"step_name": "Full Screen Capture", "tool": "macos_vision", "params": {"action": "screenshot"}}]
    )
    procedural.register_procedure(
        name="Screen Optical Character Recognition",
        description="Extract and parse visible text on screen using Apple Vision Framework",
        trigger_patterns=["read screen", "ocr screen", "what is on my screen", "extract text from screen"],
        steps=[{"step_name": "Apple Vision OCR", "tool": "macos_vision", "params": {"action": "ocr"}}]
    )
    procedural.register_procedure(
        name="Maximize Frontmost Window",
        description="Expand active application window to full screen",
        trigger_patterns=["maximize window", "fullscreen window", "full screen"],
        steps=[{"step_name": "Maximize Window", "tool": "macos_window", "params": {"action": "snap", "position": "maximize"}}]
    )
    procedural.register_procedure(
        name="Send WhatsApp Message",
        description="Open WhatsApp and deliver a text message to a contact",
        trigger_patterns=["send whatsapp", "whatsapp message", "message on whatsapp"],
        steps=[{"step_name": "Send WhatsApp Text", "tool": "whatsapp_automation", "params": {"action": "send_message"}}]
    )
    procedural.register_procedure(
        name="Send iMessage",
        description="Send an Apple iMessage to a recipient",
        trigger_patterns=["send imessage", "text via imessage", "imessage to"],
        steps=[{"step_name": "Dispatch iMessage", "tool": "apple_suite", "params": {"action": "imessage"}}]
    )
    procedural.register_procedure(
        name="Morning Briefing Routine",
        description="Execute full Stark morning status briefing with hardware vitals, weather, agenda, and news",
        trigger_patterns=["good morning", "morning briefing", "morning report", "run morning protocol", "brief me"],
        steps=[{"step_name": "Run Morning Protocol", "tool": "morning_protocol", "params": {"location": "Jaipur"}}]
    )
    procedural.register_procedure(
        name="Check Calendar Schedule",
        description="Inspect macOS Calendar for today's scheduled agenda and upcoming events",
        trigger_patterns=["check my calendar", "what's on my schedule", "calendar agenda", "today's agenda"],
        steps=[{"step_name": "Read Calendar Agenda", "tool": "calendar", "params": {"action": "today"}}]
    )
    procedural.register_procedure(
        name="Send Gmail Message",
        description="Draft and dispatch an email via Gmail SMTP integration",
        trigger_patterns=["send email", "send gmail", "email to"],
        steps=[{"step_name": "Dispatch Gmail", "tool": "gmail", "params": {"action": "send"}}]
    )
    procedural.register_procedure(
        name="Send Telegram Message",
        description="Send an alert or message via Telegram Bot integration",
        trigger_patterns=["send telegram", "telegram message", "telegram alert"],
        steps=[{"step_name": "Dispatch Telegram Message", "tool": "telegram", "params": {"action": "send"}}]
    )
    procedural.register_procedure(
        name="Profile Dataset Analytics",
        description="Analyze tabular CSV/JSON dataset and extract key statistical distributions",
        trigger_patterns=["analyze data", "profile dataset", "inspect csv", "summarize data"],
        steps=[{"step_name": "Profile Dataset", "tool": "data_analytics", "params": {"action": "profile"}}]
    )
    procedural.register_procedure(
        name="Biometric Identity Verification",
        description="Prompt the user for hardware Touch ID biometric authentication",
        trigger_patterns=["verify identity", "touch id", "biometric check", "verify my identity", "fingerprint"],
        steps=[{"step_name": "Prompt Touch ID", "tool": "biometrics", "params": {"action": "verify"}}]
    )

    # 5. Context Assembly Engine
    context_engine = ContextEngine(
        short_term=memory,
        preferences=preferences,
        semantic=semantic,
        episodic=episodic,
        procedural=procedural,
        soul_path=cfg.config_dir / "soul.md"
    )

    # 6. Computer Control Agent
    computer_agent = ComputerAgent(router=router, tools=registry)

    # 7. Agent Orchestrator
    orchestrator = AgentOrchestrator(
        router=router,
        tools=registry,
        episodic_memory=episodic,
        procedural_memory=procedural,
        context_engine=context_engine
    )

    # 8. Background Task Scheduler
    scheduler = TaskScheduler(
        db_path=cfg.config_dir / "scheduler.db",
        dispatcher=lambda action, params: orchestrator.run(params.get("objective", action))
    )

    # 9. Voice & Audio Engines
    tts = TextToSpeechEngine()
    stt = SpeechToTextEngine()
    voice = VoiceInterface(orchestrator=orchestrator, tts_engine=tts, stt_engine=stt)

    # 10. Self-Management & Diagnostics
    recovery = RecoveryManager(episodic_memory=episodic)
    diagnostics = SystemHealthCheck()

    # 11. Live Observability & Telemetry
    telemetry = telemetry_engine
    telemetry.connect_event_bus()

    # 12. Assemble Container
    _global_container = BootstrapContainer(
        config=cfg,
        router=router,
        tools=registry,
        memory=memory,
        preferences=preferences,
        semantic_memory=semantic,
        episodic_memory=episodic,
        procedural_memory=procedural,
        context_engine=context_engine,
        orchestrator=orchestrator,
        computer_agent=computer_agent,
        scheduler=scheduler,
        tts=tts,
        stt=stt,
        voice=voice,
        diagnostics=diagnostics,
        recovery=recovery,
        telemetry=telemetry
    )

    logger.info("J.A.R.V.I.S. Core Foundation, Memory Systems, macOS Automation, Integrations, Voice, Diagnostics, and Telemetry successfully assembled.")
    return _global_container





