from collections import Counter
from datetime import datetime, timezone
from typing import Callable

from pydantic import BaseModel

from app import config
from app.classifier import classify
from app.gmail_client import GmailClient
from app.models import ProcessedRecord
from app.storage import Storage

ProgressCallback = Callable[[str], None]


class SyncResult(BaseModel):
    """Summary of a sync run: how many messages were processed, by category."""

    processed: int
    skipped_already_processed: int
    by_category: dict[str, int]


def _noop(_: str) -> None:
    return None


def run_sync(progress_callback: ProgressCallback = _noop) -> SyncResult:
    categories = config.load_categories()
    gmail = GmailClient()
    storage = Storage()

    processed_by_category: Counter[str] = Counter()
    skipped = 0

    progress_callback("Buscando mensajes nuevos...")
    messages = gmail.list_new_messages()
    progress_callback(f"{len(messages)} mensaje(s) encontrado(s).")

    for email in messages:
        if storage.is_processed(email.message_id):
            skipped += 1
            continue

        progress_callback(f"Clasificando: {email.subject[:60]}")
        result = classify(email, categories)
        category = next((c for c in categories if c.name == result.category), None)
        label_name = category.gmail_label if category else result.category

        gmail.apply_label(email.message_id, label_name)

        storage.record(
            ProcessedRecord(
                message_id=email.message_id,
                thread_id=email.thread_id,
                sender=email.sender,
                subject=email.subject,
                category=result.category,
                label=label_name,
                confidence=result.confidence,
                reasoning=result.reasoning,
                classified_at=datetime.now(timezone.utc),
            )
        )
        processed_by_category[result.category] += 1

    return SyncResult(
        processed=sum(processed_by_category.values()),
        skipped_already_processed=skipped,
        by_category=dict(processed_by_category),
    )
