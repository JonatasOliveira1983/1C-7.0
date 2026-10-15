# -*- coding: utf-8 -*-
"""
Camada de armazenamento SQLite local para persistência ACID de memória de agentes do 1Crypten.
Armazena memórias operacionais de mercado, pares de trading e diretrizes táticas da Laya.
"""
import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from app.models.memory import MemoryCreate, MemoryItem, MemoryType


class SQLiteMemoryStore:
    """Motor de persistência SQLite com suporte a namespaces e isolamento de entidades."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent / "data"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(base_dir / "memory.db")
        else:
            self.db_path = db_path
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._init_db()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._lock:
            with self._connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS agent_memories (
                        id TEXT PRIMARY KEY,
                        namespace TEXT NOT NULL,
                        entity_id TEXT NOT NULL,
                        memory_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        expires_at TEXT,
                        access_count INTEGER NOT NULL DEFAULT 0,
                        last_accessed_at TEXT
                    )
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_mem_ns_entity ON agent_memories(namespace, entity_id)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_mem_type ON agent_memories(memory_type)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_mem_updated ON agent_memories(updated_at DESC)"
                )
                conn.commit()

    def put(self, dto: MemoryCreate) -> MemoryItem:
        now = datetime.now(timezone.utc)
        mem_id = f"mem-{uuid4()}"
        item = MemoryItem(
            id=mem_id,
            namespace=dto.namespace,
            entity_id=dto.entity_id,
            memory_type=dto.memory_type,
            content=dto.content,
            metadata=dto.metadata,
            confidence=dto.confidence,
            expires_at=dto.expires_at,
            created_at=now,
            updated_at=now,
            access_count=0,
            last_accessed_at=None,
        )

        with self._lock:
            with self._connection() as conn:
                conn.execute(
                    """
                    INSERT INTO agent_memories (
                        id, namespace, entity_id, memory_type, content,
                        metadata, confidence, created_at, updated_at,
                        expires_at, access_count, last_accessed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.id,
                        item.namespace,
                        item.entity_id,
                        item.memory_type.value,
                        item.content,
                        json.dumps(item.metadata, ensure_ascii=False),
                        item.confidence,
                        item.created_at.isoformat(),
                        item.updated_at.isoformat(),
                        item.expires_at.isoformat() if item.expires_at else None,
                        item.access_count,
                        None,
                    ),
                )
                conn.commit()
        return item

    def get(self, memory_id: str) -> Optional[MemoryItem]:
        with self._lock:
            with self._connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT * FROM agent_memories WHERE id = ?",
                    (memory_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None

                now = datetime.now(timezone.utc)
                new_count = row["access_count"] + 1
                cur.execute(
                    """
                    UPDATE agent_memories
                    SET access_count = ?, last_accessed_at = ?
                    WHERE id = ?
                    """,
                    (new_count, now.isoformat(), memory_id),
                )
                conn.commit()

                return self._row_to_item(row, new_count, now)

    def search(
        self,
        namespace: str = "crypto_pair",
        entity_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        query: Optional[str] = None,
        limit: int = 10,
        min_confidence: float = 0.0,
    ) -> List[MemoryItem]:
        clauses = ["namespace = ?", "confidence >= ?"]
        params = [namespace, min_confidence]

        if entity_id:
            clauses.append("entity_id = ?")
            params.append(entity_id)

        if memory_type:
            clauses.append("memory_type = ?")
            params.append(memory_type.value if hasattr(memory_type, "value") else str(memory_type))

        if query:
            clauses.append("content LIKE ?")
            params.append(f"%{query}%")

        sql = f"""
            SELECT * FROM agent_memories
            WHERE {' AND '.join(clauses)}
            ORDER BY updated_at DESC
            LIMIT ?
        """
        params.append(limit)

        with self._lock:
            with self._connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, tuple(params))
                rows = cur.fetchall()
                return [self._row_to_item(r) for r in rows]

    def update(self, item: MemoryItem) -> MemoryItem:
        with self._lock:
            with self._connection() as conn:
                conn.execute(
                    """
                    UPDATE agent_memories
                    SET content = ?, metadata = ?, confidence = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        item.content,
                        json.dumps(item.metadata, ensure_ascii=False),
                        item.confidence,
                        item.updated_at.isoformat(),
                        item.id,
                    ),
                )
                conn.commit()
        return item

    def delete(self, memory_id: str) -> bool:
        with self._lock:
            with self._connection() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM agent_memories WHERE id = ?", (memory_id,))
                conn.commit()
                return cur.rowcount > 0

    def count(self, namespace: Optional[str] = None) -> int:
        with self._lock:
            with self._connection() as conn:
                cur = conn.cursor()
                if namespace:
                    cur.execute("SELECT COUNT(*) FROM agent_memories WHERE namespace = ?", (namespace,))
                else:
                    cur.execute("SELECT COUNT(*) FROM agent_memories")
                return cur.fetchone()[0]

    def _row_to_item(
        self,
        row: sqlite3.Row,
        access_count: Optional[int] = None,
        last_accessed_at: Optional[datetime] = None,
    ) -> MemoryItem:
        raw_meta = row["metadata"]
        try:
            metadata = json.loads(raw_meta) if raw_meta else {}
        except Exception:
            metadata = {}

        return MemoryItem(
            id=row["id"],
            namespace=row["namespace"],
            entity_id=row["entity_id"],
            memory_type=MemoryType(row["memory_type"]),
            content=row["content"],
            metadata=metadata,
            confidence=float(row["confidence"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            expires_at=(
                datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None
            ),
            access_count=access_count if access_count is not None else row["access_count"],
            last_accessed_at=(
                last_accessed_at
                if last_accessed_at is not None
                else (
                    datetime.fromisoformat(row["last_accessed_at"])
                    if row["last_accessed_at"]
                    else None
                )
            ),
        )


memory_store = SQLiteMemoryStore()
