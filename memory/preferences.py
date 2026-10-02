"""
J.A.R.V.I.S. User Preferences Store
Persists custom developer and user preferences, communication style, and habitual workflows.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class PreferenceStore:
    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            config_dir = Path(os.path.expanduser("~/.jarvis_system"))
            config_dir.mkdir(parents=True, exist_ok=True)
            self.storage_path = config_dir / "preferences.json"
        else:
            self.storage_path = storage_path
            
        self._cache: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        defaults = {
            "tone": "composed, precise, and authoritative",
            "autonomy_level": 1,  # 0=Advisory, 1=Assisted, 2=Autonomous, 3=High
            "privacy_tier": "BALANCED",
            "voice_enabled": True,
            "default_browser": "Chrome",
            "code_editor": "VS Code"
        }
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    defaults.update(data)
            except Exception:
                pass
        return defaults

    def get(self, key: str, default: Any = None) -> Any:
        return self._cache.get(key, default)

    def set(self, key: str, value: Any):
        self._cache[key] = value
        self.save()

    def save(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)
        except Exception:
            pass

    def all(self) -> Dict[str, Any]:
        return dict(self._cache)
