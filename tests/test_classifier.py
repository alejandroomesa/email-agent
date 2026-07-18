from types import SimpleNamespace
from unittest.mock import patch

from app.classifier import classify
from app.models import Category, EmailMessage

CATEGORIES = [
    Category(name="trabajo", description="Emails de trabajo", gmail_label="Agente/Trabajo"),
    Category(name="personal", description="Emails personales", gmail_label="Agente/Personal"),
]

EMAIL = EmailMessage(
    message_id="msg-1",
    thread_id="thread-1",
    sender="jefe@empresa.com",
    subject="Reunión mañana",
    body="Nos vemos mañana a las 10 para hablar del proyecto.",
)


def _fake_response(json_content: str):
    return SimpleNamespace(message=SimpleNamespace(content=json_content))


def test_classify_parses_structured_response():
    fake_json = (
        '{"category": "trabajo", "confidence": 0.92, '
        '"reasoning": "Menciona reunión y proyecto"}'
    )
    with patch("app.classifier.ollama.chat", return_value=_fake_response(fake_json)) as mock_chat:
        result = classify(EMAIL, CATEGORIES)

    assert result.category == "trabajo"
    assert result.confidence == 0.92
    assert "proyecto" in result.reasoning

    _, kwargs = mock_chat.call_args
    assert kwargs["format"] is not None
    assert any(EMAIL.subject in m["content"] for m in kwargs["messages"])
