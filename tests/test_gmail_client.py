import email
from email.mime.text import MIMEText
from unittest.mock import MagicMock, patch

import pytest

from app import config
from app.gmail_client import GmailClient, _extract_plain_text, _quote


@pytest.fixture(autouse=True)
def _credentials(monkeypatch):
    monkeypatch.setattr(config, "GMAIL_ADDRESS", "user@gmail.com")
    monkeypatch.setattr(config, "GMAIL_APP_PASSWORD", "app-password")


def _mock_conn() -> MagicMock:
    conn = MagicMock()
    conn.login.return_value = ("OK", [b"Logged in"])
    conn.select.return_value = ("OK", [b"1"])
    return conn


def _raw_email(subject: str, body: str) -> bytes:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = "remitente@example.com"
    return msg.as_bytes()


def test_quote_escapes_backslash_and_quotes():
    assert _quote("Agente/Trabajo") == '"Agente/Trabajo"'
    assert _quote('a"b\\c') == '"a\\"b\\\\c"'


def test_extract_plain_text_from_simple_message():
    msg = MIMEText("Hola mundo", "plain", "utf-8")
    assert _extract_plain_text(msg) == "Hola mundo"


def test_extract_plain_text_from_multipart_message():
    raw = (
        'Content-Type: multipart/alternative; boundary="BOUNDARY"\n'
        "\n"
        "--BOUNDARY\n"
        "Content-Type: text/html\n"
        "\n"
        "<p>Hola</p>\n"
        "--BOUNDARY\n"
        "Content-Type: text/plain\n"
        "\n"
        "Hola texto plano\n"
        "--BOUNDARY--\n"
    )
    msg = email.message_from_string(raw)
    assert _extract_plain_text(msg).strip() == "Hola texto plano"


def test_apply_label_sends_store_command():
    conn = _mock_conn()

    with patch("app.gmail_client.imaplib.IMAP4_SSL", return_value=conn):
        GmailClient().apply_label("123", "Agente/Trabajo")

    conn.uid.assert_called_with("STORE", "123", "+X-GM-LABELS", '("Agente/Trabajo")')
    conn.logout.assert_called_once()


def test_apply_label_raises_without_credentials(monkeypatch):
    monkeypatch.setattr(config, "GMAIL_ADDRESS", None)
    monkeypatch.setattr(config, "GMAIL_APP_PASSWORD", None)

    with pytest.raises(RuntimeError):
        GmailClient().apply_label("123", "Agente/Trabajo")


def test_list_new_messages_parses_search_and_fetch():
    conn = _mock_conn()
    conn.uid.side_effect = [
        ("OK", [b"101 102"]),
        ("OK", [(b"101 (X-GM-THRID 555 RFC822 {10}", _raw_email("Asunto uno", "Cuerpo uno"))]),
        ("OK", [(b"102 (X-GM-THRID 556 RFC822 {10}", _raw_email("Asunto dos", "Cuerpo dos"))]),
    ]

    with patch("app.gmail_client.imaplib.IMAP4_SSL", return_value=conn):
        messages = GmailClient().list_new_messages("in:inbox is:unread")

    assert [m.message_id for m in messages] == ["101", "102"]
    assert [m.thread_id for m in messages] == ["555", "556"]
    assert messages[0].subject == "Asunto uno"
    assert messages[0].body.strip() == "Cuerpo uno"

    search_call = conn.uid.call_args_list[0]
    assert search_call.args == ("search", None, "X-GM-RAW", '"in:inbox is:unread"')
