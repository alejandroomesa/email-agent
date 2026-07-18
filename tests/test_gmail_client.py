import base64
from unittest.mock import MagicMock, patch

from app.gmail_client import GmailClient, _extract_plain_text


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("utf-8")


def test_extract_plain_text_from_simple_payload():
    payload = {"mimeType": "text/plain", "body": {"data": _b64("Hola mundo")}}
    assert _extract_plain_text(payload) == "Hola mundo"


def test_extract_plain_text_from_multipart_payload():
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {"mimeType": "text/html", "body": {"data": _b64("<p>Hola</p>")}},
            {"mimeType": "text/plain", "body": {"data": _b64("Hola texto plano")}},
        ],
    }
    assert _extract_plain_text(payload) == "Hola texto plano"


def _make_client(mock_service: MagicMock) -> GmailClient:
    with (
        patch("app.gmail_client._get_credentials", return_value=MagicMock()),
        patch("app.gmail_client.build", return_value=mock_service),
    ):
        return GmailClient()


def test_ensure_label_creates_missing_label():
    mock_service = MagicMock()
    labels = mock_service.users.return_value.labels.return_value
    labels.list.return_value.execute.return_value = {"labels": []}
    labels.create.return_value.execute.return_value = {
        "id": "Label_123",
        "name": "Agente/Trabajo",
    }

    client = _make_client(mock_service)
    label_id = client.ensure_label("Agente/Trabajo")

    assert label_id == "Label_123"
    assert client.ensure_label("Agente/Trabajo") == "Label_123"
    labels.create.assert_called_once()


def test_ensure_label_reuses_existing_label():
    mock_service = MagicMock()
    labels = mock_service.users.return_value.labels.return_value
    labels.list.return_value.execute.return_value = {
        "labels": [{"id": "Label_9", "name": "Agente/Trabajo"}]
    }

    client = _make_client(mock_service)
    label_id = client.ensure_label("Agente/Trabajo")

    assert label_id == "Label_9"
    labels.create.assert_not_called()


def test_apply_label_calls_modify():
    mock_service = MagicMock()
    client = _make_client(mock_service)

    client.apply_label("msg-1", "Label_9")

    mock_service.users().messages().modify.assert_called_with(
        userId="me", id="msg-1", body={"addLabelIds": ["Label_9"]}
    )
