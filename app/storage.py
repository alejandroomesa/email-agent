import sqlite3
from pathlib import Path

from app import config
from app.models import ProcessedRecord

SCHEMA = """
CREATE TABLE IF NOT EXISTS processed_messages (
    message_id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    category TEXT NOT NULL,
    label TEXT NOT NULL,
    confidence REAL NOT NULL,
    reasoning TEXT NOT NULL,
    classified_at TEXT NOT NULL
);
"""


class Storage:
    def __init__(self, db_path: Path = config.DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(SCHEMA)
        self._conn.commit()

    def is_processed(self, message_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM processed_messages WHERE message_id = ?", (message_id,)
        ).fetchone()
        return row is not None

    def record(self, record: ProcessedRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO processed_messages
                (message_id, thread_id, category, label, confidence, reasoning, classified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.message_id,
                record.thread_id,
                record.category,
                record.label,
                record.confidence,
                record.reasoning,
                record.classified_at.isoformat(),
            ),
        )
        self._conn.commit()

    def list_recent(self, limit: int = 50) -> list[ProcessedRecord]:
        rows = self._conn.execute(
            "SELECT * FROM processed_messages ORDER BY classified_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [ProcessedRecord(**dict(row)) for row in rows]

    def close(self) -> None:
        self._conn.close()
