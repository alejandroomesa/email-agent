from collections import Counter
from datetime import datetime, timezone

from fastapi import FastAPI

from app import config
from app.classifier import classify
from app.gmail_client import GmailClient
from app.models import Category, ProcessedRecord
from app.storage import Storage

app = FastAPI(title="Gmail Classifier Agent")


@app.get("/categories")
def get_categories() -> list[Category]:
    return config.load_categories()


@app.post("/sync")
def sync() -> dict:
    categories = config.load_categories()
    gmail = GmailClient()
    storage = Storage()

    processed_by_category: Counter[str] = Counter()
    skipped = 0

    for email in gmail.list_new_messages():
        if storage.is_processed(email.message_id):
            skipped += 1
            continue

        result = classify(email, categories)
        category = next((c for c in categories if c.name == result.category), None)
        label_name = category.gmail_label if category else result.category

        gmail.apply_label(email.message_id, label_name)

        storage.record(
            ProcessedRecord(
                message_id=email.message_id,
                thread_id=email.thread_id,
                category=result.category,
                label=label_name,
                confidence=result.confidence,
                reasoning=result.reasoning,
                classified_at=datetime.now(timezone.utc),
            )
        )
        processed_by_category[result.category] += 1

    return {
        "processed": sum(processed_by_category.values()),
        "skipped_already_processed": skipped,
        "by_category": dict(processed_by_category),
    }


@app.get("/processed")
def get_processed(limit: int = 50) -> list[ProcessedRecord]:
    return Storage().list_recent(limit)
