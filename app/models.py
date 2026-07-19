from datetime import datetime

from pydantic import BaseModel, Field


class Category(BaseModel):
    """A user-defined classification bucket, loaded from categories.yaml."""

    name: str
    description: str
    gmail_label: str


class EmailMessage(BaseModel):
    """A Gmail message pulled down for classification."""

    message_id: str
    thread_id: str
    sender: str
    subject: str
    body: str


class ClassificationResult(BaseModel):
    """Structured output requested from the local LLM."""

    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class ProcessedRecord(BaseModel):
    """Audit trail row: one classified + labeled message."""

    message_id: str
    thread_id: str
    sender: str
    subject: str
    category: str
    label: str
    confidence: float
    reasoning: str
    classified_at: datetime
