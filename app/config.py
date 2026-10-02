"""
J.A.R.V.I.S. Unified Configuration Engine
Provides centralized, type-safe settings loaded from environment, .env, and JSON files.
"""
import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

def _load_dotenv_safely(env_path: Path):
    if not env_path.exists():
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass

@dataclass
class HardwareConfig:
    platform: str = "macOS Apple Silicon"
    chip: str = "Apple M5"
    unified_memory_gb: int = 32
    cpu_cores: int = 10
    gpu_cores: int = 10
    has_neural_engine: bool = True

@dataclass
class ModelConfig:
    # Local Models (MLX)
    local_primary: str = "mlx-community/gemma-4-e2b-it-4bit"
    local_secondary: str = "mlx-community/gemma-3-12b-it-4bit"
    local_quantization: str = "4-bit"
    max_local_tokens: int = 2048
    temperature: float = 0.7
    
    # Cloud Models
    gemini_model: str = "gemini-2.5-flash"
    groq_model: str = "llama-3.3-70b-versatile"
    nvidia_model: str = "meta/llama-3.3-70b-instruct"
    openrouter_model: str = "google/gemini-2.5-flash"

@dataclass
class SecuritySettings:
    defense_in_depth: bool = True
    prompt_firewall_enabled: bool = True
    context_isolation_enabled: bool = True
    max_execution_steps: int = 15
    action_timeout_seconds: int = 30
    kill_switch_enabled: bool = True
    zero_trust_network: bool = True

@dataclass
class JarvisConfig:
    owner_name: str = "Divyanshu Verma"
    organization: str = "Divyanshu Industries"
    system_name: str = "J.A.R.V.I.S."
    version: str = "5.1.0-prod"
    environment: str = "development"
    
    # Hardware & Resources
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    
    # Models & Routing
    models: ModelConfig = field(default_factory=ModelConfig)
    
    # Security
    security: SecuritySettings = field(default_factory=SecuritySettings)
    
    # API Keys
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    nvidia_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    
    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    config_dir: Path = field(default_factory=lambda: Path(os.path.expanduser("~/.jarvis_system")))
    memory_dir: Path = field(default_factory=lambda: Path(os.path.expanduser("~/.jarvis_system/memory")))
    audit_log_path: Path = field(default_factory=lambda: Path(os.path.expanduser("~/.jarvis_system/audit_chain.jsonl")))

    @classmethod
    def load(cls) -> "JarvisConfig":
        base_dir = Path(__file__).resolve().parent.parent
        _load_dotenv_safely(base_dir / ".env")
        _load_dotenv_safely(Path.home() / ".jarvis_system" / ".env")
        
        config_dir = Path(os.path.expanduser("~/.jarvis_system"))
        config_dir.mkdir(parents=True, exist_ok=True)
        memory_dir = config_dir / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Load JSON config file if present
        json_file = config_dir / "config.json"
        data = {}
        if json_file.exists():
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

        return cls(
            owner_name=os.getenv("JARVIS_OWNER_NAME", data.get("owner_name", "Divyanshu Verma")),
            organization=os.getenv("JARVIS_ORGANIZATION", data.get("organization", "Divyanshu Industries")),
            environment=os.getenv("JARVIS_ENV", data.get("environment", "development")),
            gemini_api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or data.get("gemini_api_key"),
            groq_api_key=os.getenv("GROQ_API_KEY") or data.get("groq_api_key"),
            nvidia_api_key=os.getenv("NVIDIA_API_KEY") or data.get("nvidia_api_key"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY") or data.get("openrouter_api_key"),
            base_dir=base_dir,
            config_dir=config_dir,
            memory_dir=memory_dir,
            audit_log_path=config_dir / "audit_chain.jsonl"
        )

_global_config: Optional[JarvisConfig] = None

def get_config() -> JarvisConfig:
    global _global_config
    if _global_config is None:
        _global_config = JarvisConfig.load()
    return _global_config
