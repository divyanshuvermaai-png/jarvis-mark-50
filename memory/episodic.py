"""
J.A.R.V.I.S. Episodic Memory Subsystem
Records and queries structured, chronological event logs, task milestones,
tool actions, and error recoveries across all sessions.
"""
import os
import json
import sqlite3
import hashlib
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("jarvis.memory.episodic")

class EpisodicMemory:
    """
    Persistent SQLite store for chronological episodic events, task histories, and milestones.
    """
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            config_dir = Path(os.path.expanduser("~/.jarvis_system"))
            config_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = config_dir / "episodic_memory.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._init_db()

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
                    CREATE TABLE IF NOT EXISTS episodes (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        task_id TEXT,
                        event_type TEXT NOT NULL,
                        summary TEXT NOT NULL,
                        details_json TEXT DEFAULT '{}',
                        importance INTEGER DEFAULT 1
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ep_timestamp ON episodes(timestamp);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ep_session ON episodes(session_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ep_event_type ON episodes(event_type);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ep_task_id ON episodes(task_id);")
                conn.commit()
            finally:
                conn.close()

    def record_episode(
        self,
        summary: str,
        event_type: str = "general",
        session_id: str = "default",
        task_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        importance: int = 1,
        timestamp: Optional[str] = None
    ) -> str:
        """
        Record an episodic event.
        """
        summary = summary.strip()
        if not summary:
            raise ValueError("Episode summary cannot be empty")

        now = timestamp or datetime.now().isoformat()
        ep_id = hashlib.sha256(f"{now}:{session_id}:{event_type}:{summary}".encode("utf-8")).hexdigest()[:16]
        details_json = json.dumps(details or {})

        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO episodes (id, timestamp, session_id, task_id, event_type, summary, details_json, importance)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (ep_id, now, session_id, task_id, event_type, summary, details_json, importance))
                conn.commit()
                return ep_id
            finally:
                conn.close()

    def get_recent_episodes(
        self,
        limit: int = 10,
        event_type: Optional[str] = None,
        session_id: Optional[str] = None,
        min_importance: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Fetch most recent episodes matching criteria.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            query = "SELECT id, timestamp, session_id, task_id, event_type, summary, details_json, importance FROM episodes WHERE importance >= ?"
            params: List[Any] = [min_importance]

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)

            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)

            query += " ORDER BY timestamp DESC LIMIT ?;"
            params.append(limit)

            cursor.execute(query, tuple(params))
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "session_id": row["session_id"],
                    "task_id": row["task_id"],
                    "event_type": row["event_type"],
                    "summary": row["summary"],
                    "details": json.loads(row["details_json"] or "{}"),
                    "importance": row["importance"]
                })
            return results
        finally:
            conn.close()

    def count(self) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM episodes;")
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def clear(self):
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM episodes;")
                conn.commit()
            finally:
                conn.close()

    def format_recent_context(self, limit: int = 5) -> str:
        """
        Format recent significant episodes for prompt context injection.
        """
        episodes = self.get_recent_episodes(limit=limit, min_importance=2)
        if not episodes:
            return ""

        lines = ["[RECENT ACTIVITY & MILESTONES]"]
        for ep in reversed(episodes):
            ts = ep["timestamp"][:16].replace("T", " ")
            lines.append(f"• [{ts}] ({ep['event_type']}) {ep['summary']}")
        lines.append("[END RECENT ACTIVITY]")
        return "\n".join(lines)
