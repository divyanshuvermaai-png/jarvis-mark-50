"""
J.A.R.V.I.S. Procedural Memory Subsystem
Stores and retrieves codified workflows, proven action recipes, and tool execution sequences.
Allows J.A.R.V.I.S. to reuse known successful procedures without re-planning from scratch.
"""
import os
import json
import re
import sqlite3
import hashlib
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("jarvis.memory.procedural")

class ProceduralMemory:
    """
    Persistent SQLite store for execution recipes, multi-step procedures, and tool chains.
    """
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            config_dir = Path(os.path.expanduser("~/.jarvis_system"))
            config_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = config_dir / "procedural_memory.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._init_db()
        self._seed_default_procedures()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS procedures (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        trigger_patterns_json TEXT NOT NULL,
                        steps_json TEXT NOT NULL,
                        success_count INTEGER DEFAULT 0,
                        failure_count INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        last_used TEXT
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_proc_name ON procedures(name);")
                conn.commit()
            finally:
                conn.close()

    def register_procedure(
        self,
        name: str,
        description: str,
        trigger_patterns: List[str],
        steps: List[Dict[str, Any]],
        proc_id: Optional[str] = None
    ) -> str:
        """
        Register or update a procedural workflow recipe.
        """
        name = name.strip()
        if not name:
            raise ValueError("Procedure name cannot be empty")

        if not proc_id:
            proc_id = hashlib.sha256(name.lower().encode("utf-8")).hexdigest()[:16]

        patterns_json = json.dumps(trigger_patterns)
        steps_json = json.dumps(steps)
        now = datetime.now().isoformat()

        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO procedures (id, name, description, trigger_patterns_json, steps_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name=excluded.name,
                        description=excluded.description,
                        trigger_patterns_json=excluded.trigger_patterns_json,
                        steps_json=excluded.steps_json;
                """, (proc_id, name, description, patterns_json, steps_json, now))
                conn.commit()
                return proc_id
            finally:
                conn.close()

    def find_matching_procedure(self, intent: str) -> Optional[Dict[str, Any]]:
        """
        Find the best matching procedure based on trigger patterns.
        """
        intent_clean = intent.lower().strip()
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description, trigger_patterns_json, steps_json, success_count, failure_count, last_used FROM procedures;")
            best_match = None
            highest_score = 0

            for row in cursor.fetchall():
                patterns = json.loads(row["trigger_patterns_json"])
                for pattern in patterns:
                    # Check exact regex or keyword
                    if re.search(r'\b' + re.escape(pattern.lower()) + r'\b', intent_clean):
                        # Calculate reliability score: success_count - failure_count
                        score = 10 + (row["success_count"] - row["failure_count"])
                        if score > highest_score:
                            highest_score = score
                            best_match = {
                                "id": row["id"],
                                "name": row["name"],
                                "description": row["description"],
                                "trigger_patterns": patterns,
                                "steps": json.loads(row["steps_json"]),
                                "success_count": row["success_count"],
                                "failure_count": row["failure_count"],
                                "last_used": row["last_used"]
                            }
            return best_match
        finally:
            conn.close()

    def record_outcome(self, proc_id: str, success: bool):
        """
        Increment success or failure count for a procedure.
        """
        now = datetime.now().isoformat()
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                if success:
                    cursor.execute("""
                        UPDATE procedures SET
                            success_count = success_count + 1,
                            last_used = ?
                        WHERE id = ?;
                    """, (now, proc_id))
                else:
                    cursor.execute("""
                        UPDATE procedures SET
                            failure_count = failure_count + 1,
                            last_used = ?
                        WHERE id = ?;
                    """, (now, proc_id))
                conn.commit()
            finally:
                conn.close()

    def get_procedure(self, proc_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description, trigger_patterns_json, steps_json, success_count, failure_count, last_used FROM procedures WHERE id = ?;", (proc_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "trigger_patterns": json.loads(row["trigger_patterns_json"]),
                "steps": json.loads(row["steps_json"]),
                "success_count": row["success_count"],
                "failure_count": row["failure_count"],
                "last_used": row["last_used"]
            }
        finally:
            conn.close()

    def list_procedures(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description, trigger_patterns_json, steps_json, success_count, failure_count, last_used FROM procedures ORDER BY success_count DESC;")
            return [{
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "trigger_patterns": json.loads(row["trigger_patterns_json"]),
                "steps": json.loads(row["steps_json"]),
                "success_count": row["success_count"],
                "failure_count": row["failure_count"],
                "last_used": row["last_used"]
            } for row in cursor.fetchall()]
        finally:
            conn.close()

    def _seed_default_procedures(self):
        """
        Populate foundational standard operating procedures for J.A.R.V.I.S.
        """
        defaults = [
            {
                "name": "Inspect Hardware Performance",
                "description": "Inspect CPU, RAM, and battery metrics on Apple Silicon",
                "trigger_patterns": ["system info", "cpu usage", "ram usage", "battery status", "system diagnostics"],
                "steps": [
                    {
                        "step_name": "Read System Metrics",
                        "tool": "system_info",
                        "params": {"category": "all"}
                    }
                ]
            },
            {
                "name": "Safe File Content Inspection",
                "description": "Read file safely within whitelisted project boundaries",
                "trigger_patterns": ["read file", "inspect file", "check file contents"],
                "steps": [
                    {
                        "step_name": "Read File Target",
                        "tool": "file_ops",
                        "params": {"action": "read"}
                    }
                ]
            }
        ]

        for proc in defaults:
            try:
                self.register_procedure(
                    name=proc["name"],
                    description=proc["description"],
                    trigger_patterns=proc["trigger_patterns"],
                    steps=proc["steps"]
                )
            except Exception:
                pass
