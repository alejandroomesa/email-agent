from datetime import datetime, timezone

from app.models import ProcessedRecord
from app.storage import Storage


def _record(message_id: str = "msg-1") -> ProcessedRecord:
    return ProcessedRecord(
        message_id=message_id,
        thread_id="thread-1",
        category="trabajo",
        label_id="Label_1",
        confidence=0.9,
        reasoning="test",
        classified_at=datetime.now(timezone.utc),
    )


def test_record_and_is_processed(tmp_path):
    storage = Storage(db_path=tmp_path / "agent.db")

    assert storage.is_processed("msg-1") is False

    storage.record(_record())

    assert storage.is_processed("msg-1") is True


def test_list_recent_returns_inserted_records(tmp_path):
    storage = Storage(db_path=tmp_path / "agent.db")

    storage.record(_record("msg-1"))
    storage.record(_record("msg-2"))

    recent = storage.list_recent(limit=10)

    assert {r.message_id for r in recent} == {"msg-1", "msg-2"}
