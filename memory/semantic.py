"""
J.A.R.V.I.S. Semantic Memory Subsystem
Combines SQLite FTS5 full-text search with dense vector embeddings and cosine similarity
for high-speed, 100% offline, persistent hybrid memory retrieval.
"""
import os
import json
import sqlite3
import hashlib
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger("jarvis.memory.semantic")

DEFAULT_EMBEDDING_DIM = 256

def compute_local_embedding(text: str, dim: int = DEFAULT_EMBEDDING_DIM) -> np.ndarray:
    """
    High-performance, deterministic subword and character n-gram embedding.
    Runs 100% locally and offline without external API latency or model weight overhead.
    """
    vec = np.zeros(dim, dtype=np.float32)
    tokens = text.lower().split()
    for token in tokens:
        # Token hash
        h = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:8], 16) % dim
        vec[h] += 1.0
        # Character 3-grams
        for i in range(max(1, len(token) - 2)):
            tri = token[i:i+3]
            h_tri = int(hashlib.md5(tri.encode("utf-8")).hexdigest()[:8], 16) % dim
            vec[h_tri] += 0.5
            
    norm = float(np.linalg.norm(vec))
    if norm > 1e-6:
        vec /= norm
    return vec


class SemanticMemory:
    """
    Persistent SQLite + FTS5 + Vector hybrid memory store.
    """
    def __init__(self, db_path: Optional[Path] = None, embedding_dim: int = DEFAULT_EMBEDDING_DIM):
        if db_path is None:
            config_dir = Path(os.path.expanduser("~/.jarvis_system"))
            config_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = config_dir / "semantic_memory.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.embedding_dim = embedding_dim
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
                # Documents table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        category TEXT DEFAULT 'general',
                        metadata_json TEXT DEFAULT '{}',
                        embedding BLOB,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_category ON documents(category);")
                
                # FTS5 Full-Text Virtual Table
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                        id UNINDEXED,
                        content,
                        category,
                        tokenize = 'porter unicode61'
                    );
                """)
                conn.commit()
            finally:
                conn.close()

    def add(
        self,
        content: str,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """
        Index a memory entry into both relational/vector storage and FTS5.
        """
        content = content.strip()
        if not content:
            raise ValueError("Memory content cannot be empty")

        if not doc_id:
            doc_id = hashlib.sha256(f"{category}:{content}:{datetime.now().isoformat()}".encode("utf-8")).hexdigest()[:16]

        meta_json = json.dumps(metadata or {})
        now = datetime.now().isoformat()
        emb = compute_local_embedding(content, self.embedding_dim).tobytes()

        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO documents (id, content, category, metadata_json, embedding, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        content=excluded.content,
                        category=excluded.category,
                        metadata_json=excluded.metadata_json,
                        embedding=excluded.embedding,
                        updated_at=excluded.updated_at;
                """, (doc_id, content, category, meta_json, emb, now, now))

                # Update FTS5
                cursor.execute("DELETE FROM documents_fts WHERE id = ?;", (doc_id,))
                cursor.execute("INSERT INTO documents_fts (id, content, category) VALUES (?, ?, ?);",
                               (doc_id, content, category))

                conn.commit()
                return doc_id
            finally:
                conn.close()

    def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, content, category, metadata_json, created_at, updated_at FROM documents WHERE id = ?;", (doc_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "content": row["content"],
                "category": row["category"],
                "metadata": json.loads(row["metadata_json"] or "{}"),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
        finally:
            conn.close()

    def delete(self, doc_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM documents WHERE id = ?;", (doc_id,))
                cursor.execute("DELETE FROM documents_fts WHERE id = ?;", (doc_id,))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()

    def count(self, category: Optional[str] = None) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if category:
                cursor.execute("SELECT COUNT(*) FROM documents WHERE category = ?;", (category,))
            else:
                cursor.execute("SELECT COUNT(*) FROM documents;")
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def clear(self):
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM documents;")
                cursor.execute("DELETE FROM documents_fts;")
                conn.commit()
            finally:
                conn.close()

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5,
        mode: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        """
        Search memory using:
        - 'text': SQLite FTS5 BM25 match
        - 'vector': Cosine similarity of dense embeddings
        - 'hybrid': Reciprocal Rank Fusion (RRF) combining both
        """
        query = query.strip()
        if not query:
            return []

        if mode == "text":
            return self._search_fts(query, category, top_k)
        elif mode == "vector":
            return self._search_vector(query, category, top_k)
        else:
            return self._search_hybrid(query, category, top_k)

    def _search_fts(self, query: str, category: Optional[str], top_k: int) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Clean search terms for FTS query
            safe_terms = " ".join([f'"{term.replace(chr(34), "")}"*' for term in query.split() if term])
            if not safe_terms:
                return []

            if category:
                cursor.execute("""
                    SELECT d.id, d.content, d.category, d.metadata_json, d.created_at, bm25(documents_fts) as rank
                    FROM documents_fts f
                    JOIN documents d ON d.id = f.id
                    WHERE documents_fts MATCH ? AND d.category = ?
                    ORDER BY rank ASC
                    LIMIT ?;
                """, (safe_terms, category, top_k))
            else:
                cursor.execute("""
                    SELECT d.id, d.content, d.category, d.metadata_json, d.created_at, bm25(documents_fts) as rank
                    FROM documents_fts f
                    JOIN documents d ON d.id = f.id
                    WHERE documents_fts MATCH ?
                    ORDER BY rank ASC
                    LIMIT ?;
                """, (safe_terms, top_k))

            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row["id"],
                    "content": row["content"],
                    "category": row["category"],
                    "metadata": json.loads(row["metadata_json"] or "{}"),
                    "score": float(row["rank"]),
                    "created_at": row["created_at"]
                })
            return results
        except sqlite3.OperationalError:
            # Fallback if syntax error in query
            return []
        finally:
            conn.close()

    def _search_vector(self, query: str, category: Optional[str], top_k: int) -> List[Dict[str, Any]]:
        query_vec = compute_local_embedding(query, self.embedding_dim)
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if category:
                cursor.execute("SELECT id, content, category, metadata_json, embedding, created_at FROM documents WHERE category = ?;", (category,))
            else:
                cursor.execute("SELECT id, content, category, metadata_json, embedding, created_at FROM documents;")

            candidates = []
            for row in cursor.fetchall():
                raw_emb = row["embedding"]
                if not raw_emb:
                    continue
                doc_vec = np.frombuffer(raw_emb, dtype=np.float32)
                sim = float(np.dot(query_vec, doc_vec))
                candidates.append({
                    "id": row["id"],
                    "content": row["content"],
                    "category": row["category"],
                    "metadata": json.loads(row["metadata_json"] or "{}"),
                    "score": sim,
                    "created_at": row["created_at"]
                })

            candidates.sort(key=lambda x: x["score"], reverse=True)
            return candidates[:top_k]
        finally:
            conn.close()

    def _search_hybrid(self, query: str, category: Optional[str], top_k: int) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF) combining FTS5 lexical ranking and dense vector similarity.
        Score = 1 / (60 + rank_fts) + 1 / (60 + rank_vec)
        """
        fts_hits = self._search_fts(query, category, top_k * 2)
        vec_hits = self._search_vector(query, category, top_k * 2)

        rrf_scores: Dict[str, float] = {}
        items: Dict[str, Dict[str, Any]] = {}

        for rank, hit in enumerate(fts_hits):
            doc_id = hit["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (60 + rank + 1))
            items[doc_id] = hit

        for rank, hit in enumerate(vec_hits):
            doc_id = hit["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (60 + rank + 1))
            if doc_id not in items:
                items[doc_id] = hit

        ranked_ids = sorted(rrf_scores.keys(), key=lambda did: rrf_scores[did], reverse=True)
        results = []
        for did in ranked_ids[:top_k]:
            item = items[did]
            item["rrf_score"] = rrf_scores[did]
            results.append(item)

        return results

    def format_context(self, query: str, top_k: int = 4) -> str:
        """
        Formats retrieved semantic memories into a clean prompt block.
        """
        results = self.search(query, top_k=top_k, mode="hybrid")
        if not results:
            return ""

        lines = ["[RELEVANT MEMORY FACTS]"]
        for r in results:
            cat = r["category"].upper()
            content = r["content"].strip()
            lines.append(f"• [{cat}] {content}")
        lines.append("[END RELEVANT MEMORY]")
        return "\n".join(lines)
