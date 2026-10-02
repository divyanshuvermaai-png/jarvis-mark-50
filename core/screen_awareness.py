"""
J.A.R.V.I.S. Continuous Screen Awareness Engine
Real-time display perception using macOS System Events, AppKit, Quartz, and Apple Silicon Vision OCR.
"""
import os
import re
import time
import json
import logging
import threading
import subprocess
from typing import Dict, Any, Optional

logger = logging.getLogger("jarvis.screen_awareness")

class ScreenAwarenessEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ScreenAwarenessEngine, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, check_interval_sec: float = 3.0, ocr_interval_sec: float = 12.0):
        if getattr(self, '_initialized', False):
            return
        self._initialized = True
        self.check_interval = check_interval_sec
        self.ocr_interval = ocr_interval_sec
        self.enabled = True
        self._running = False
        self._thread = None
        self._state_lock = threading.Lock()

        self._state = {
            "active_app": "",
            "window_title": "",
            "browser_url": "",
            "browser_title": "",
            "media_info": "",
            "watching_summary": "System running, desktop visible.",
            "ocr_text": "",
            "last_window_check": 0.0,
            "last_ocr_check": 0.0,
            "monitoring": True
        }

    def start(self):
        """Start background screen perception thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="jarvis-screen-awareness")
        self._thread.start()
        logger.info("[SCREEN AWARENESS] Real-time screen perception engine started.")

    def stop(self):
        """Stop background screen perception."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("[SCREEN AWARENESS] Screen perception engine stopped.")

    def toggle(self, enabled: Optional[bool] = None) -> bool:
        """Toggle continuous screen monitoring on or off."""
        with self._state_lock:
            if enabled is None:
                self.enabled = not self.enabled
            else:
                self.enabled = enabled
            self._state["monitoring"] = self.enabled
            return self.enabled

    def get_status(self) -> Dict[str, Any]:
        with self._state_lock:
            return dict(self._state)

    def _get_frontmost_app_info(self) -> Dict[str, str]:
        """Fast (<25ms) extraction of frontmost application and active window/tab."""
        info = {
            "app": "",
            "window": "",
            "url": "",
            "tab_title": ""
        }

        # 1. Try PyObjC AppKit for frontmost app
        try:
            from AppKit import NSWorkspace
            front_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            if front_app:
                info["app"] = front_app.localizedName() or ""
        except Exception:
            pass

        # 2. Extract window title and browser URL/title via AppleScript
        script = '''
set appName to ""
set winTitle to ""
set extraUrl to ""
set extraTitle to ""

tell application "System Events"
    try
        set frontApp to first application process whose frontmost is true
        set appName to name of frontApp
        try
            set winTitle to name of front window of frontApp
        end try
    end try
end tell

if appName is "Google Chrome" then
    try
        tell application "Google Chrome"
            set activeTab to active tab of front window
            set extraUrl to URL of activeTab
            set extraTitle to title of activeTab
        end tell
    end try
else if appName is "Safari" then
    try
        tell application "Safari"
            set currentTab to current tab of front window
            set extraUrl to URL of currentTab
            set extraTitle to name of currentTab
        end tell
    end try
else if appName is "Brave Browser" then
    try
        tell application "Brave Browser"
            set activeTab to active tab of front window
            set extraUrl to URL of activeTab
            set extraTitle to title of activeTab
        end tell
    end try
end if

return appName & ":::" & winTitle & ":::" & extraUrl & ":::" & extraTitle
'''
        try:
            res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and res.stdout.strip():
                parts = res.stdout.strip().split(':::')
                if len(parts) >= 1 and parts[0]:
                    info["app"] = parts[0].strip()
                if len(parts) >= 2 and parts[1]:
                    info["window"] = parts[1].strip()
                if len(parts) >= 3 and parts[2]:
                    info["url"] = parts[2].strip()
                if len(parts) >= 4 and parts[3]:
                    info["tab_title"] = parts[3].strip()
        except Exception as e:
            logger.debug(f"AppleScript window query error: {e}")

        return info

    def _synthesize_watching_summary(self, app: str, window: str, url: str, tab_title: str) -> str:
        """Formulate a natural language description of what the user is currently watching or doing."""
        if not app:
            return "User is viewing the macOS Desktop."

        # Video Streaming / YouTube
        if "youtube.com" in url.lower() or "youtube" in window.lower():
            title = tab_title or window
            clean_title = re.sub(r' - YouTube.*$', '', title, flags=re.IGNORECASE).strip()
            return f"Watching YouTube video: '{clean_title}' in {app}"

        if "netflix.com" in url.lower() or "netflix" in window.lower():
            return f"Watching Netflix in {app} ({window})"

        if "twitch.tv" in url.lower():
            return f"Watching Twitch livestream in {app} ({tab_title or window})"

        if "disneyplus.com" in url.lower() or "primevideo.com" in url.lower():
            return f"Streaming video in {app} ({window})"

        # Media Players
        if app in ("VLC", "QuickTime Player", "IINA"):
            return f"Watching media in {app}: '{window}'"

        # Coding / Development
        if app in ("Visual Studio Code", "Code", "Xcode", "PyCharm", "Cursor", "Sublime Text"):
            return f"Coding in {app} (Active document: '{window}')"

        # Terminal / Shell
        if app in ("Terminal", "iTerm2", "Alacritty", "Warp"):
            return f"Working in command line {app} ('{window}')"

        # Messaging / Social
        if app in ("WhatsApp", "Telegram", "Slack", "Discord", "Messages"):
            return f"Communicating on {app} ({window})"

        # Web Browsing
        if url:
            title = tab_title or window
            return f"Browsing '{title}' in {app} ({url})"

        return f"Active in {app} ('{window}')"

    def _perform_ocr(self, image_path: Optional[str] = None) -> str:
        """Extract visible on-screen text via Apple Silicon Vision framework."""
        try:
            from desktop_controller.screen import ScreenController
            target_path = image_path or self._state.get('shared_screen_path')
            ocr_res = ScreenController.ocr_screen(image_path=target_path)
            if ocr_res.get('success') and ocr_res.get('data'):
                raw = ocr_res['data'].strip()
                clean_lines = [line.strip() for line in raw.splitlines() if line.strip()]
                return "\n".join(clean_lines[:40])
        except Exception as e:
            logger.debug(f"OCR extraction error: {e}")
        return ""

    def force_refresh(self) -> Dict[str, Any]:
        """Force an immediate update of window state and OCR text."""
        info = self._get_frontmost_app_info()
        ocr = self._perform_ocr()
        summary = self._synthesize_watching_summary(info["app"], info["window"], info["url"], info["tab_title"])

        with self._state_lock:
            self._state.update({
                "active_app": info["app"],
                "window_title": info["window"],
                "browser_url": info["url"],
                "browser_title": info["tab_title"],
                "watching_summary": summary,
                "ocr_text": ocr,
                "last_window_check": time.time(),
                "last_ocr_check": time.time()
            })
            return dict(self._state)

    def _monitor_loop(self):
        """Background loop updating window status frequently, and OCR on change."""
        last_app = ""
        last_win = ""

        while self._running:
            try:
                if self.enabled:
                    info = self._get_frontmost_app_info()
                    now = time.time()

                    app_changed = (info["app"] != last_app or info["window"] != last_win)
                    ocr_due = (now - self._state["last_ocr_check"]) > self.ocr_interval

                    new_ocr = None
                    if app_changed or ocr_due:
                        new_ocr = self._perform_ocr()
                        last_app = info["app"]
                        last_win = info["window"]

                    summary = self._synthesize_watching_summary(
                        info["app"], info["window"], info["url"], info["tab_title"]
                    )

                    with self._state_lock:
                        self._state["active_app"] = info["app"]
                        self._state["window_title"] = info["window"]
                        self._state["browser_url"] = info["url"]
                        self._state["browser_title"] = info["tab_title"]
                        self._state["watching_summary"] = summary
                        self._state["last_window_check"] = now
                        if new_ocr is not None:
                            self._state["ocr_text"] = new_ocr
                            self._state["last_ocr_check"] = now

            except Exception as e:
                logger.debug(f"Error in screen awareness loop: {e}")

            time.sleep(self.check_interval)

    def get_perception_context(self) -> str:
        """
        Generates clean Markdown context block for dynamic LLM prompt injection.
        Guarantees J.A.R.V.I.S. knows what the user is watching/doing on the screen.
        """
        with self._state_lock:
            if not self.enabled:
                return "- Live Screen Monitoring: Standby"

            app = self._state.get("active_app", "Desktop")
            win = self._state.get("window_title", "")
            summary = self._state.get("watching_summary", "")
            url = self._state.get("browser_url", "")
            ocr = self._state.get("ocr_text", "")

            lines = []
            if self._state.get('shared_screen_active'):
                lines.append("- Live Screen Sharing: STREAMING (Direct HUD Optical Feed Active)")
            lines.extend([
                f"- Current Foreground App: {app}",
                f"- Active Window Title: {win}",
                f"- User Screen Activity: {summary}",
            ])
            if url:
                lines.append(f"- Browser URL: {url}")
            if ocr:
                excerpt = ocr[:600].replace('\n', ' | ')
                lines.append(f"- On-Screen Text Excerpt: {excerpt}")

            return "\n".join(lines)

# Singleton global instance
screen_awareness = ScreenAwarenessEngine()
