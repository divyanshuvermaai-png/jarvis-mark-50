"""
J.A.R.V.I.S. Background Task Scheduler
Provides persistent, thread-safe delayed and recurring execution for autonomous tasks and alerts.
Backed by SQLite for state persistence across system restarts.
"""
import os
import time
import json
import sqlite3
import hashlib
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger("jarvis.scheduler")

@dataclass
class ScheduledJob:
    id: str
    name: str
    action: str
    params: Dict[str, Any]
    job_type: str  # 'one_time' or 'interval'
    interval_seconds: float
    next_run_ts: float
    status: str    # 'scheduled', 'running', 'completed', 'cancelled'
    last_run_ts: Optional[float] = None
    created_at: str = ""


class TaskScheduler:
    """
    Persistent background job runner supporting one-time delayed tasks and recurring interval tasks.
    """
    def __init__(
        self,
        db_path: Optional[Path] = None,
        dispatcher: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        tick_rate: float = 1.0
    ):
        if db_path is None:
            config_dir = Path(os.path.expanduser("~/.jarvis_system"))
            config_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = config_dir / "scheduler.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.dispatcher = dispatcher
        self.tick_rate = tick_rate
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None

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
                    CREATE TABLE IF NOT EXISTS scheduled_jobs (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        action TEXT NOT NULL,
                        params_json TEXT DEFAULT '{}',
                        job_type TEXT NOT NULL,
                        interval_seconds REAL DEFAULT 0,
                        next_run_ts REAL NOT NULL,
                        status TEXT DEFAULT 'scheduled',
                        last_run_ts REAL,
                        created_at TEXT NOT NULL
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_sched_next_run ON scheduled_jobs(next_run_ts, status);")
                conn.commit()
            finally:
                conn.close()

    def schedule_in(
        self,
        delay_seconds: float,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        name: str = "",
        job_id: Optional[str] = None
    ) -> str:
        """
        Schedule a one-time task to execute after delay_seconds.
        """
        now = time.time()
        next_run = now + max(0.1, delay_seconds)
        jid = job_id or hashlib.sha256(f"onetime:{action}:{next_run}:{time.time()}".encode("utf-8")).hexdigest()[:16]
        job_name = name or f"Delayed {action}"
        params_json = json.dumps(params or {})
        created_str = datetime.now().isoformat()

        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO scheduled_jobs (id, name, action, params_json, job_type, interval_seconds, next_run_ts, status, created_at)
                    VALUES (?, ?, ?, ?, 'one_time', 0, ?, 'scheduled', ?);
                """, (jid, job_name, action, params_json, next_run, created_str))
                conn.commit()
                return jid
            finally:
                conn.close()

    def schedule_every(
        self,
        interval_seconds: float,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        name: str = "",
        job_id: Optional[str] = None
    ) -> str:
        """
        Schedule a recurring interval task.
        """
        now = time.time()
        next_run = now + max(0.01, interval_seconds)

        jid = job_id or hashlib.sha256(f"recurring:{action}:{interval_seconds}:{time.time()}".encode("utf-8")).hexdigest()[:16]
        job_name = name or f"Recurring {action}"
        params_json = json.dumps(params or {})
        created_str = datetime.now().isoformat()

        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO scheduled_jobs (id, name, action, params_json, job_type, interval_seconds, next_run_ts, status, created_at)
                    VALUES (?, ?, ?, ?, 'interval', ?, ?, 'scheduled', ?)
                    ON CONFLICT(id) DO UPDATE SET
                        interval_seconds=excluded.interval_seconds,
                        next_run_ts=excluded.next_run_ts,
                        status='scheduled';
                """, (jid, job_name, action, params_json, interval_seconds, next_run, created_str))
                conn.commit()
                return jid
            finally:
                conn.close()

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled job."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE scheduled_jobs SET status = 'cancelled' WHERE id = ?;", (job_id,))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scheduled_jobs WHERE id = ?;", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return ScheduledJob(
                id=row["id"],
                name=row["name"],
                action=row["action"],
                params=json.loads(row["params_json"] or "{}"),
                job_type=row["job_type"],
                interval_seconds=row["interval_seconds"],
                next_run_ts=row["next_run_ts"],
                status=row["status"],
                last_run_ts=row["last_run_ts"],
                created_at=row["created_at"]
            )
        finally:
            conn.close()

    def list_jobs(self, include_completed: bool = False) -> List[ScheduledJob]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if include_completed:
                cursor.execute("SELECT * FROM scheduled_jobs ORDER BY next_run_ts ASC;")
            else:
                cursor.execute("SELECT * FROM scheduled_jobs WHERE status = 'scheduled' ORDER BY next_run_ts ASC;")
            jobs = []
            for row in cursor.fetchall():
                jobs.append(ScheduledJob(
                    id=row["id"],
                    name=row["name"],
                    action=row["action"],
                    params=json.loads(row["params_json"] or "{}"),
                    job_type=row["job_type"],
                    interval_seconds=row["interval_seconds"],
                    next_run_ts=row["next_run_ts"],
                    status=row["status"],
                    last_run_ts=row["last_run_ts"],
                    created_at=row["created_at"]
                ))
            return jobs
        finally:
            conn.close()

    def start(self):
        """Start the background scheduler thread."""
        if self._worker_thread is not None and self._worker_thread.is_alive():
            return

        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._run_loop, name="JarvisScheduler", daemon=True)
        self._worker_thread.start()
        logger.info("TaskScheduler background worker started.")

    def stop(self):
        """Stop the background scheduler thread."""
        self._stop_event.set()
        if self._worker_thread is not None and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
        logger.info("TaskScheduler background worker stopped.")

    def tick(self):
        """Execute one evaluation cycle (can be invoked directly in tests)."""
        now = time.time()
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM scheduled_jobs
                WHERE status = 'scheduled' AND next_run_ts <= ?
                ORDER BY next_run_ts ASC;
            """, (now,))
            due_jobs = cursor.fetchall()

            for row in due_jobs:
                jid = row["id"]
                action = row["action"]
                params = json.loads(row["params_json"] or "{}")
                jtype = row["job_type"]
                interval = row["interval_seconds"]

                # Dispatch job
                try:
                    if self.dispatcher:
                        self.dispatcher(action, params)
                except Exception as e:
                    logger.error(f"Error executing scheduled job '{jid}': {e}")

                # Update job status in DB
                with self._lock:
                    wconn = self._get_connection()
                    try:
                        wcur = wconn.cursor()
                        if jtype == "interval":
                            next_run = time.time() + interval
                            wcur.execute("""
                                UPDATE scheduled_jobs
                                SET next_run_ts = ?, last_run_ts = ?
                                WHERE id = ?;
                            """, (next_run, now, jid))
                        else:
                            wcur.execute("""
                                UPDATE scheduled_jobs
                                SET status = 'completed', last_run_ts = ?
                                WHERE id = ?;
                            """, (now, jid))
                        wconn.commit()
                    finally:
                        wconn.close()

        finally:
            conn.close()

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                self.tick()
            except Exception as e:
                logger.error(f"Error in scheduler tick: {e}")
            self._stop_event.wait(self.tick_rate)
